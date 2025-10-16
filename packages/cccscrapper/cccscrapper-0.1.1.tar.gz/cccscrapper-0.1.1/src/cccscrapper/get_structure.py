import os
import sys
import json
import time
import random
import logging
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote, urlparse, urlunparse
from playwright.sync_api import sync_playwright
from requests.exceptions import RequestException, Timeout

# ---------------- Logging Setup ----------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.propagate = False

# ---------------- Global ----------------
visited_urls = set()
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

# ---------------- Utility ----------------
def is_url(path):
    return path.startswith("http://") or path.startswith("https://")

def make_proper_url(base_url, relative_url):
    """Convert a relative URL to full absolute and encoded form."""
    if not relative_url:
        return None
    full_url = urljoin(base_url, relative_url)
    parsed = urlparse(full_url)
    path = quote(parsed.path)
    query = quote(parsed.query, safe="=&")
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, query, parsed.fragment))

def normalize_url(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, parsed.fragment))

# ---------------- Zyte Fetcher ----------------
def fetch_with_zyte(url: str, max_retries: int = 3, backoff_base: int = 2) -> BeautifulSoup:
    """Fetch fully rendered HTML via Zyte API with retries and exponential backoff."""
    if not ZYTE_API_KEY:
        logger.critical("ZYTE_API_KEY not set in environment")
        sys.exit(1)

    if not is_url(url):
        abs_path = url if os.path.isabs(url) else os.path.join(os.getcwd(), url)
        if not os.path.exists(abs_path):
            logger.error(f"[zyte] Local file not found: {abs_path}")
            return None
        with open(abs_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")

    payload = {"url": url, "browserHtml": True, "javascript": True}

    for attempt in range(max_retries):
        try:
            logger.info(f"[zyte] Fetching (attempt {attempt + 1}/{max_retries}): {url}")
            resp = requests.post(
                ZYTE_API_URL,
                auth=(ZYTE_API_KEY, ""),
                json=payload,
                timeout=90,
            )

            if resp.status_code == 200:
                data = resp.json()
                html = data.get("browserHtml") or data.get("httpResponseBody")
                if html:
                    logger.info(f"✅ Zyte fetched successfully on attempt {attempt + 1}")
                    time.sleep(0.5)
                    return BeautifulSoup(html, "html.parser")
                raise Exception("Zyte returned empty HTML")
            raise Exception(f"Zyte API returned {resp.status_code}: {resp.text}")

        except Exception as e:
            logger.warning(f"[zyte] Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                sleep_time = (backoff_base ** attempt) + random.uniform(0, 1)
                logger.info(f"[zyte] Retrying in {sleep_time:.1f}s...")
                time.sleep(sleep_time)
            else:
                logger.error(f"❌ Zyte failed after {max_retries} attempts for {url}")
                return None

def fetch_with_playwright(path, retries=3, backoff=5):
    if is_url(path):
        for attempt in range(1, retries + 1):
            try:
                if attempt == 1:
                    logger.info(f"[playwright] Fetching URL: {path}")
                else:
                    logger.info(f"[playwright] Retrying URL: {path} (attempt {attempt})")

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent=(
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/120.0.0.0 Safari/537.36"
                        )
                    )
                    page = context.new_page()
                    page.goto(path, timeout=60000, wait_until="networkidle")
                    time.sleep(0.5)
                    html = page.content()
                    browser.close()
                return BeautifulSoup(html, "html.parser")
            except Exception as e:
                logger.warning(f"[playwright] Error fetching {path}: {e}")
                if attempt < retries:
                    sleep_time = backoff * attempt
                    logger.info(f"[playwright] Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"[playwright] Failed after {retries} attempts: {path}")
                    return None
    else:
        abs_path = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
        if not os.path.exists(abs_path):
            logger.error(f"[playwright] Local file not found: {abs_path}")
            return None
        with open(abs_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")


# ---------------- Requests Fallback ----------------
def fetch_with_requests(path, retries=3, backoff=5):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if is_url(path):
        for attempt in range(1, retries + 1):
            try:
                logger.info(f"[requests] Fetching: {path} (attempt {attempt})")
                resp = requests.get(path, headers=headers, timeout=30)
                resp.raise_for_status()
                time.sleep(0.5)
                return BeautifulSoup(resp.text, "html.parser")
            except (RequestException, Timeout) as e:
                logger.warning(f"[requests] Error fetching {path}: {e}")
                if attempt < retries:
                    sleep_time = backoff * attempt
                    logger.info(f"[requests] Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"[requests] Failed after {retries} attempts: {path}")
                    return None
    else:
        abs_path = path if os.path.isabs(path) else os.path.join(os.getcwd(), path)
        if not os.path.exists(abs_path):
            logger.error(f"[requests] Local file not found: {abs_path}")
            return None
        with open(abs_path, "r", encoding="utf-8") as f:
            return BeautifulSoup(f.read(), "html.parser")

# ---------------- Fetch Router ----------------

def fetch_html(path, retries=3, backoff=5):
    """
    Chooses between requests and Playwright based on config["url_types"]["runner"].
    Defaults to requests if invalid or missing.
    """
    runner = (
        config.get("runner", "requests")
        if isinstance(config, dict)
        else "requests"
    ).lower()

    if runner == "zyte":
        return fetch_with_zyte(path, retries, backoff)
    if runner == "playwright":
        return fetch_with_playwright(path, retries, backoff)
    else:
        return fetch_with_requests(path, retries, backoff)


# ---------------- Recursive Page Processing ----------------
def process_page(path, parent_breadcrumbs=None):
    parent_breadcrumbs = parent_breadcrumbs or []
    path = normalize_url(path)

    if path in visited_urls:
        logger.info(f"Skipping already visited URL: {path}")
        return []
    visited_urls.add(path)

    soup = fetch_html(path)
    if not soup:
        return []

    results = []
    for root_name, root_cfg in config["url_types"].items():
        if not isinstance(root_cfg, dict):
            continue

        marker_callback = root_cfg.get("marker_callback")
        marker = root_cfg.get("marker")
        has_fragment = root_cfg.get("has_fragment")
        isMatch = False

        # marker callback check
        if marker_callback:
            fn = glob.get(marker_callback)
            if callable(fn):
                try:
                    if fn(soup, root_cfg, path, parent_breadcrumbs):
                        if ("ref=" in path and has_fragment) or ("ref=" not in path and not has_fragment):
                            isMatch = True
                except Exception as e:
                    logger.error(f"Error in marker_callback {marker_callback}: {e}")

        # marker selector check
        if not isMatch and marker and soup.select_one(marker):
            if ("ref=" in path and has_fragment) or ("ref=" not in path and not has_fragment):
                isMatch = True

        if isMatch:
            logger.info(f"Matched url_type: {root_name}")

            pagination_fn_name = root_cfg.get("pagination_callback")
            if pagination_fn_name:
                fn = glob.get(pagination_fn_name)
                if callable(fn):
                    return fn(root_cfg, path, parent_breadcrumbs, visited_urls, marker)

            sections = root_cfg.get("sections", {})
            section_callback = sections.get("section_callback")
            if section_callback:
                fn = glob.get(section_callback)
                if callable(fn):
                    results = fn(soup, root_cfg, path, parent_breadcrumbs, visited_urls)
            else:
                for block in sections.get("blocks", []):
                    results.extend(extract_block(soup, block, root_cfg, parent_breadcrumbs, path))
            break

    return results

# ---------------- Block Extraction ----------------
def extract_block(soup, block, root_cfg, parent_breadcrumbs=None, current_path=None):
    parent_breadcrumbs = parent_breadcrumbs or []
    results = []
    selector = block.get("selector")
    elements = soup.select(selector) if selector else [soup]
    if not elements:
        return []

    loop_elements = elements if block.get("loop", False) else [elements[0]]

    for el in loop_elements:
        if block["type"] in ["container", "node", "specific"]:
            # before callback
            if "before_block_callback" in block:
                cb = glob.get(block["before_block_callback"])
                if callable(cb):
                    updated = cb(root_cfg, parent_breadcrumbs, block, el, current_path)
                    if isinstance(updated, dict):
                        block.update(updated)

            # child recursion
            block_results = []
            for child in block.get("blocks", []):
                block_results.extend(extract_block(el, child, root_cfg, parent_breadcrumbs, current_path))

            # after callback
            if "after_block_callback" in block:
                cb = glob.get(block["after_block_callback"])
                if callable(cb):
                    ret = cb(root_cfg, parent_breadcrumbs, block, el, current_path, block_results)
                    if isinstance(ret, list):
                        block_results = ret

            results.extend(block_results)

        elif block["type"] == "leaf":
            item = {}
            for attr in block.get("attributes", []):
                target_el = el.select_one(attr["selector"]) if attr.get("selector") else el
                if attr["attr"] == "text":
                    item[attr["name"]] = target_el.get_text(strip=True) if target_el else ""
                elif attr["attr"] == "attr_callback":
                    cb_name = attr.get("attr_callback")
                    func = glob.get(cb_name)
                    if callable(func):
                        try:
                            item[attr["name"]] = func(root_cfg, parent_breadcrumbs, block, el, current_path, target_el, attr)
                        except Exception as e:
                            logger.exception(f"attr_callback {cb_name} failed: {e}")
                            item[attr["name"]] = None
                else:
                    item[attr["name"]] = target_el.get(attr["attr"], "").strip() if target_el else ""

            # before callback
            if "before_block_callback" in block:
                cb = glob.get(block["before_block_callback"])
                if callable(cb):
                    returned = cb(soup, root_cfg, parent_breadcrumbs, block, el, current_path, item)
                    if isinstance(returned, dict):
                        item = returned

            item_name = item.get("name") or "Unnamed"
            item["name"] = item_name
            item["breadcrumbs"] = parent_breadcrumbs + [item_name]
            item["sub_topics"] = []

            sub_path = item.get("url")
            if sub_path:
                sub_path_full = make_proper_url(current_path, sub_path) if current_path and is_url(current_path) else sub_path
                item["url"] = sub_path_full
                if root_cfg.get("sub_topics", True):
                    sub_results = process_page(sub_path_full, item["breadcrumbs"])
                    if len(sub_results) == 1 and sub_results[0].get("name") == item.get("name"):
                        item["sub_topics"] = sub_results[0].get("sub_topics", [])
                    else:
                        item["sub_topics"] = sub_results

            # after callback
            if "after_block_callback" in block:
                cb = glob.get(block["after_block_callback"])
                if callable(cb):
                    ret = cb(soup, root_cfg, parent_breadcrumbs, block, el, current_path, item)
                    if isinstance(ret, dict):
                        item = ret

            if item:
                results.append(item)

    return results

# ---------------- Hierarchy + Output ----------------
def build_hierarchy(items, start_url):
    hierarchy = []

    def insert(branch, item, crumbs):
        if not crumbs:
            branch.append(item)
            return
        head, *tail = crumbs
        if head == config["url_types"]["breadcrumbs-start-point"]:
            insert(branch, item, tail)
            return
        node = next((x for x in branch if x["name"] == head), None)
        if not node:
            node = {"name": head, "url": item.get("url", ""), "breadcrumbs": [head], "sub_topics": []}
            branch.append(node)
        if tail:
            insert(node["sub_topics"], item, tail)
        else:
            node["sub_topics"].append(item)

    for i in items:
        bc = i.get("breadcrumbs", [i["name"]])
        insert(hierarchy, i, bc[:-1])
    return hierarchy

def reorder_keys(obj):
    if isinstance(obj, list):
        return [reorder_keys(x) for x in obj]
    if isinstance(obj, dict):
        ordered = {k: reorder_keys(obj[k]) for k in ["name", "url", "sub_topics", "breadcrumbs"] if k in obj}
        for k, v in obj.items():
            if k not in ordered:
                ordered[k] = reorder_keys(v)
        return ordered
    return obj

def init(g, conf=None, url=None):
    global config, target_url, glob
    glob = g
    config = conf
    target_url = url

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    if not config or not isinstance(config, dict):
        logger.error("Invalid or empty config.")
        return
    if not target_url:
        logger.error("Target URL not specified.")
        return

    raw_data = process_page(target_url, parent_breadcrumbs=[config["url_types"]["breadcrumbs-start-point"]])
    data = build_hierarchy(raw_data, target_url)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    data = reorder_keys(data)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Output saved to {args.out}")
