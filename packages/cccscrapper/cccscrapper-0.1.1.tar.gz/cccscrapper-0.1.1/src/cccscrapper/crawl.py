#!/usr/bin/env python3
import os
import re
import json
import shutil
import argparse
import logging
import requests
import random
import time
import sys
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote, parse_qs
from markdownify import markdownify as markdownify
from PyPDF2 import PdfReader
from datetime import datetime
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

ZYTE_API_KEY = os.getenv("ZYTE_API_KEY")  # set this in your environment
ZYTE_API_URL = "https://api.zyte.com/v1/extract"

BROWSERLESS_TOKEN = os.getenv("BROWSERLESS_TOKEN")
BROWSERLESS_WS = None

if BROWSERLESS_TOKEN:
    BROWSERLESS_WS = f"wss://production-sfo.browserless.io?token={BROWSERLESS_TOKEN}"

# ---------- Proxy & Browserless Configuration ----------
CONFIG = {"use_residential": False}
ISP_HOSTS = [f"isp.oxylabs.io:800{i}" for i in range(1, 10)] + ["isp.oxylabs.io:8010"]
OX_ISP_USER = os.getenv("OXYLAB_ISP_USERNAME")
OX_ISP_PASS = os.getenv("OXYLAB_ISP_PASSWORD")
OX_RES_USER = os.getenv("OXYLAB_RES_USERNAME")
OX_RES_PASS = os.getenv("OXYLAB_RES_PASSWORD")

def choose_isp_proxy(offset=0):
    if not (OX_ISP_USER and OX_ISP_PASS):
        return None
    host = ISP_HOSTS[(int(time.time()) + offset) % len(ISP_HOSTS)]
    return f"http://{OX_ISP_USER}:{OX_ISP_PASS}@{host}"

def choose_res_proxy():
    if not (OX_RES_USER and OX_RES_PASS):
        return None
    host = os.getenv("OXYLAB_RES_HOST", "residential.oxylabs.io:7777")
    return f"http://{OX_RES_USER}:{OX_RES_PASS}@{host}"

def new_session(residential=None, offset=0):
    if residential is None:
        residential = CONFIG.get("use_residential", False)
    proxy = choose_res_proxy() if residential else choose_isp_proxy(offset=offset)
    s = requests.Session()
    s.headers["User-Agent"] = os.getenv(
        "SCRAPER_UA",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
    )
    if proxy:
        s.proxies = {"http": proxy, "https": proxy}
    return s

def http_get(url, params=None, timeout=30, max_retries=3, stream=False):
    """
    Proxy-aware wrapper around requests.get() that uses Oxylabs ISP/residential proxy credentials.
    Returns requests.Response or None on failure.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            s = new_session(offset=attempt)
            r = s.get(url, params=params, timeout=timeout, stream=stream)
            if r.status_code >= 400:
                logger.warning("HTTP %s for %s", r.status_code, url)
            else:
                logger.debug("Fetched URL successfully: %s", url)
            return r
        except (requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError) as e:
            last_error = e
            logger.warning("Proxy/connection failed for %s: %s", url, e)
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.error("Request error for %s: %s", url, e, exc_info=True)
            return None
    logger.error("All retries failed for %s: %s", url, last_error, exc_info=True)
    return None

def ensure_browser(p, browser=None, context=None, page=None):
    """
    Ensure a Playwright browser/context/page connected to Browserless via CDP.
    Returns tuple (browser, context, page).
    """
    try:
        if page and not page.is_closed():
            return browser, context, page
    except Exception:
        pass
    logger.warning("Browser/page closed or missing. Reconnecting to Browserless...")
    try:
        if browser:
            try:
                browser.close()
            except Exception:
                pass
    except Exception:
        pass
    # Connect over CDP to remote Browserless (this will manage headless remotely)
    browser = p.chromium.connect_over_cdp(BROWSERLESS_WS)
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.pages[0] if context.pages else context.new_page()
    return browser, context, page

# ---------- Utilities ----------

def fetch_html_with_playwright(url: str, max_retries: int = 3) -> str:
    """
    Use Browserless-connected Playwright to fetch page content (HTML).
    This function uses ensure_browser() to connect and reuse the remote browser.
    """
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    # We'll try a few attempts with exponential backoff
    for attempt in range(max_retries):
        try:
            if not BROWSERLESS_TOKEN:
                logger.critical("Environment variable BROWSERLESS_TOKEN is missing.")
                sys.exit(1)

            with sync_playwright() as p:
                browser, context, page = ensure_browser(p)

                # set a random UA on the context (won't break existing context if shared)
                try:
                    context.set_extra_http_headers({"User-Agent": random.choice(user_agents)})
                except Exception:
                    # some remote contexts may not allow headers mutation; ignore
                    pass

                # Navigate
                page.goto(url,
                          wait_until="networkidle",
                          timeout=60000,
                          referer='https://www.google.com/')
                # Small scroll to trigger lazy-loads
                try:
                    page.evaluate('''() => {
                        window.scrollBy(0, window.innerHeight);
                        return new Promise(resolve => setTimeout(resolve, 1500));
                    }''')
                except Exception:
                    pass

                try:
                    page.wait_for_selector('body', timeout=10000)
                except PlaywrightTimeoutError:
                    logger.warning("Timed out waiting for the page to load via playwright")

                # Simple block checks
                try:
                    content = page.content()
                    title = page.title()
                    if "Access Denied" in title or "Checking your browser" in content:
                        raise Exception("Access denied by Cloudflare / bot protection")
                except Exception as e:
                    raise

                return page.content()
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Failed to fetch {url} after {max_retries} attempts: {str(e)}")
            time.sleep((2 ** attempt) + random.uniform(0, 1))

    raise Exception("Failed to fetch the page")

def fetch_html_with_zyte(url: str, max_retries: int = 3) -> str:
    """
    Fetch fully rendered HTML from Zyte API with retries and proxy fallback.
    """
    if not ZYTE_API_KEY:
        logger.critical("ZYTE_API_KEY not set in environment")
        sys.exit(1)

    payload = {
        "url": url,
        "browserHtml": True,
        "javascript": True
    }

    for attempt in range(max_retries):
        try:
            proxies = None
            proxy = choose_res_proxy() or choose_isp_proxy()
            if proxy:
                proxies = {"http": proxy, "https": proxy}

            resp = requests.post(
                ZYTE_API_URL,
                auth=(ZYTE_API_KEY, ""),
                json=payload,
                timeout=90,
                proxies=proxies
            )

            if resp.status_code == 200:
                data = resp.json()
                html = data.get("browserHtml") or data.get("httpResponseBody")
                if html:
                    logger.info(f"✅ Zyte fetched page successfully on attempt {attempt + 1}")
                    return html
                else:
                    raise Exception("Zyte returned empty HTML or body")

            raise Exception(f"Zyte API returned {resp.status_code}: {resp.text}")

        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep((2 ** attempt) + random.uniform(0, 1))  # exponential backoff
            else:
                logger.error(f"❌ Failed after {max_retries} attempts for {url}")
                raise

def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

def sanitize_filename(name: str) -> str:
    if not name:
        return None
    name = name.strip()
    name = name.split('?')[0]  # remove query
    return re.sub(r'[\\/*?:"<>|]', "_", name)

def parse_file_scheme(path_or_url: str):
    parsed = urlparse(path_or_url)
    if parsed.scheme == "file":
        return unquote(parsed.path)
    return None

def resolve_link(crawl_url: str, link: str):
    if not link:
        return None
    parsed_link = urlparse(link)
    if parsed_link.scheme in ("http", "https"):
        return link
    if parsed_link.scheme == "file":
        return unquote(parsed_link.path)
    if os.path.exists(link):
        return os.path.abspath(link)
    if os.path.exists(crawl_url):
        base_dir = os.path.dirname(os.path.abspath(crawl_url))
        candidate = os.path.normpath(os.path.join(base_dir, link))
        return candidate
    if link.startswith("//"):
        parsed_base = urlparse(crawl_url)
        return f"{parsed_base.scheme}:{link}"
    return urljoin(crawl_url, link)

def download_or_copy(src: str, dst_path: str) -> bool:
    """
    Copy local file if available, otherwise download via http_get (proxy-aware).
    """
    ensure_folder(os.path.dirname(dst_path))
    file_path_from_scheme = parse_file_scheme(src)
    if file_path_from_scheme and os.path.exists(file_path_from_scheme):
        try:
            shutil.copy2(file_path_from_scheme, dst_path)
            logger.info(f"Copied local file: {file_path_from_scheme} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy {file_path_from_scheme}: {e}")
            return False
    if os.path.exists(src):
        try:
            shutil.copy2(src, dst_path)
            logger.info(f"Copied local file: {src} -> {dst_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to copy {src}: {e}")
            return False
    try:
        resp = http_get(src, stream=True, timeout=60)
        if not resp or resp.status_code != 200:
            raise Exception(f"Bad response: {resp}")
        with open(dst_path, "wb") as f:
            for chunk in resp.iter_content(1024 * 8):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded: {src} -> {dst_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {src}: {e}")
        return False

# ---------- Metadata helpers ----------

def extract_pdf_metadata(full_path: str):
    result = {
        "version": None,
        "date": None,
        "language": None,
        "description": None
    }

    try:
        reader = PdfReader(full_path)
        info = reader.metadata or {}

        # --- version ---
        version = info.get('/Version') or info.get('Version')
        if version:
            version = str(version).strip()
            result["version"] = version

        # --- description ---
        description = (
            info.get('/Subject') or
            info.get('Subject') or
            info.get('/Title') or
            info.get('Title')
        )
        if description:
            result["description"] = str(description).strip()

        # --- date ---
        date_val = info.get('/CreationDate') or info.get('CreationDate')
        if date_val:
            date_val = str(date_val).strip()
            # Example: D:20230216094904Z
            match = re.match(r"D:(\d{4})(\d{2})(\d{2})", date_val)
            if match:
                y, m, d = match.groups()
                result["date"] = f"{y}-{m}-{d}"
            else:
                try:
                    # Try to parse if already in ISO format
                    parsed = datetime.fromisoformat(date_val)
                    result["date"] = parsed.strftime("%Y-%m-%d")
                except Exception:
                    result["date"] = date_val  # fallback as-is

        # --- language ---
        lang = (
            info.get('/Lang') or
            info.get('Lang') or
            info.get('/Language') or
            info.get('Language')
        )
        if lang:
            lang = str(lang).strip().lower()
            # Normalize language codes
            if lang in ['en', 'en-us', 'english', 'eng']:
                lang = 'english'
            elif lang in ['fr', 'fr-fr', 'french']:
                lang = 'french'
            elif lang in ['de', 'de-de', 'german']:
                lang = 'german'
            elif lang in ['es', 'es-es', 'spanish']:
                lang = 'spanish'
            result["language"] = lang

    except Exception as e:
        logger.warning(f"Failed to read PDF metadata for {full_path}: {e}")

    return result

def load_metadata_for_section(section_path: str):
    meta_path = os.path.join(section_path, "metadata.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_metadata_for_section(section_path: str, metadata_list):
    ensure_folder(section_path)
    meta_path = os.path.join(section_path, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata_list, f, indent=2, ensure_ascii=False)

def append_metadata_entry(section_path: str, entry: dict, outdir: str):
    """
    Append a minimal metadata entry for a saved file.

    'file_path' is stored relative to the root output directory (outdir),
    e.g. "output_dir2/category/images/226_500_366_LP-11PMBT_resized_1.png"
    """
    metadata = load_metadata_for_section(section_path)

    name = entry.get("name")
    url = entry.get("url")
    file_path_rel = entry.get("file_path")

    file_path_abs = None
    rel_from_root = None
    if file_path_rel:
        file_path_abs = os.path.abspath(os.path.join(section_path, file_path_rel))
        try:
            # ✅ keep output_dir2 in relative path
            root_parent = os.path.abspath(os.path.join(outdir, "..", ".."))
            rel_from_root = os.path.relpath(file_path_abs, root_parent)
        except Exception:
            rel_from_root = file_path_abs  # fallback

    minimal = {
        "name": name,
        "url": url,
        "file_path": rel_from_root,
        "version": None,
        "date": None,
        "language": None,
        "description": None
    }

    if file_path_abs and file_path_abs.lower().endswith(".pdf") and os.path.exists(file_path_abs):
        pdf_meta = extract_pdf_metadata(file_path_abs)
        minimal.update({
            "version": pdf_meta.get("version"),
            "date": pdf_meta.get("date"),
            "language": pdf_meta.get("language"),
            "description": pdf_meta.get("description")
        })

    metadata.append(minimal)
    save_metadata_for_section(section_path, metadata)

# ---------- Block scraping ----------

def get_nodes(parent, selector: str, loop: bool):
    if not selector or selector == "self":
        return [parent]
    nodes = parent.select(selector)
    if not nodes:
        return []
    if not loop:
        return [nodes[0]]
    return nodes

def detect_url_type(soup: BeautifulSoup, url_types_config: dict, current_url: str):
    ref_required = get_url_param(current_url, "ref")

    logging.info("STARTED marker detection.")

    for url_type, conf in url_types_config.items():
        marker = conf.get("marker")
        has_fragment = conf.get("has_fragment")

        # Skip if marker is not defined
        if not marker:
            continue

        # Skip if marker is not found in soup
        if not soup.select_one(marker):
            continue

        if ref_required:
            if has_fragment:
                return url_type
            else:
                continue

        if not has_fragment:
            return url_type

    logging.info(f"ENDED marker detection.")

    logging.info(f"STARTED marker function detection.")
    for url_type, conf in url_types_config.items():
        cb_name = conf.get("marker_callback")

        if cb_name:
            func = glob.get(cb_name)
            if callable(func):
                result = func(soup, conf, current_url)
                if result:
                    return url_type

    logging.info(f"ENDED marker function detection.")

    # Fallback
    logging.warning("No URL type marker OR marker function matched; falling back to first url_type in config.")
    return next(iter(url_types_config.keys()))

def process_block(block: dict, parent_elem, section_path: str, crawl_url: str, collected: list, outdir: str, image_counter=[0]):
    """
    Recursive block processor with optional block_callback hooks.
    Supports:
      - Container/node recursion
      - Leaf data extraction
      - File downloads (e.g., images, docs)
      - First image renamed to product.jpeg
      - block_callback (applied at both container and leaf levels)
    """

    btype = block.get("type")
    loop = block.get("loop", False)
    selector = block.get("selector")

    # --- Handle container/node blocks recursively ---
    if btype in ("container", "node"):
        nodes = get_nodes(parent_elem, selector, loop)
        all_child_results = []

        for n in nodes:
            for child in block.get("blocks", []):
                process_block(child, n, section_path, crawl_url, all_child_results, outdir, image_counter)

        # --- Apply block_callback (container-level) ---
        cb_name = block.get("block_callback")
        if cb_name:
            func = glob.get(cb_name)
            if callable(func):
                all_child_results = func(
                    all_child_results, parent_elem, block, section_path, crawl_url, outdir, image_counter
                )

        collected.extend(all_child_results)

    # --- Handle leaf blocks ---
    elif btype == "leaf":
        nodes = get_nodes(parent_elem, selector, loop)
        for n in nodes:
            item = {}
            for attr in block.get("attributes", []):
                name = attr.get("name")
                attr_type = attr.get("attr")

                if attr_type == "text":
                    item[name] = n.get_text(strip=True)
                elif attr_type == "html":
                    item[name] = str(n)
                elif attr_type == "callback":
                    cb_name = attr.get("attr_callback")
                    if cb_name:
                        func = glob.get(cb_name)
                        if callable(func):
                            try:
                                item[name] = func(n, crawl_url, attr, block, section_path, outdir, image_counter)
                            except Exception as e:
                                logger.error(f"Error in attr_callback '{cb_name}': {e}")
                else:
                    item[name] = n.get(attr_type)

            # --- Handle file download ---
            if block.get("is_file") or block.get("download"):
                file_url = item.get("url") or item.get("content")
                if file_url:
                    resolved = resolve_link(crawl_url, file_url)
                    original_fname = os.path.basename(urlparse(resolved).path) or "file"
                    fname = sanitize_filename(original_fname)

                    #  First image named product.jpeg
                    try:
                        if os.path.basename(section_path).lower() == "images" and image_counter[0] == 0:
                            fname = "product.jpeg"
                    except Exception:
                        pass

                    dest = os.path.join(section_path, fname)
                    success = download_or_copy(resolved, dest)

                    if success:
                        item["file_path"] = fname
                        item["name"] = fname
                    else:
                        item["file_path"] = None

                    append_metadata_entry(section_path, item, outdir)

                    # increment counter for images
                    if success and os.path.basename(section_path).lower() == "images":
                        image_counter[0] += 1

            # ---  Apply block_callback (leaf-level) ---
            cb_name = block.get("block_callback")
            if cb_name:
                func = glob.get(cb_name)
                
                if callable(func):
                    item = func(item, n, block, section_path, crawl_url, outdir,parent_elem, image_counter)

            collected.append(item)

def is_category_or_subcategory(outdir: str) -> bool:
    base = os.path.basename(os.path.normpath(outdir)).lower()
    return base.startswith("category") or base.startswith("sub_category")

# ---------- Section processing ----------

def process_section(section_name: str, section_conf: dict, soup: BeautifulSoup, outdir: str, crawl_url: str, base_url: str):
    logging.info(f"Starting section '{section_name}'")

    if is_category_or_subcategory(outdir) and section_name.lower() in ("markdowns", "tables"):
        section_path = outdir
    else:
        section_path = os.path.join(outdir, section_name)
        ensure_folder(section_path)

    collected = []
    for block in section_conf.get("blocks", []):
        process_block(block, soup, section_path, crawl_url, collected, outdir)

    if (not os.path.exists(os.path.join(section_path, "metadata.json"))) and (section_name not in ("markdowns", "tables")):
        save_metadata_for_section(section_path, [])

    if section_conf.get("type") == "specific":
        lowname = section_name.lower()
        if lowname == "markdowns":
            handle_markdowns_section(section_path, collected)
        elif lowname == "tables":
            handle_tables_section(section_conf, section_path, crawl_url, base_url)

    cb_name = section_conf.get("section_callback")
    if cb_name:
        func = glob.get(cb_name)
        if callable(func):
            try:
                func(soup, section_conf, collected, section_path, crawl_url, base_url)
            except Exception as e:
                logging.error(f"Callback {cb_name} failed for section {section_name}: {e}")

    logging.info(f"Finished section '{section_name}'")

# ---------- Section-specific handlers ----------

def handle_markdowns_section(section_path, collected):
    html_parts = []
    for it in collected:
        if it.get("content"):
            html_parts.append(it.get("content"))
    html_content = "\n".join(html_parts).strip()
    if not html_content:
        return
    md_content = markdownify(html_content, heading_style="ATX")
    overview_path = os.path.join(section_path, "overview.md")
    with open(overview_path, "w", encoding="utf-8") as f:
        f.write(md_content)
def handle_tables_section(section_conf, section_path, crawl_url, base_url):
    products = {}

    # Run pagination if callback exists
    pagination_fn_name = section_conf.get("pagination_callback")
    if pagination_fn_name:
        fn = glob.get(pagination_fn_name)
        if callable(fn):
            logging.info(f"Running pagination script: {pagination_fn_name}")
            products = fn(crawl_url, base_url, section_conf, section_path)

    # Normalize to list if function returns dict
    if isinstance(products, dict):
        products = list(products.values())

    # If no products or empty, skip file creation
    if not products:
        logging.info("No products found — skipping parametric/products JSON creation.")
        return

    # Determine JSON filename based on category/sub_category
    if is_category_or_subcategory(section_path):
        products_path = os.path.join(section_path, "parametric_table.json")
    else:
        products_path = os.path.join(section_path, "products.json")

    # Optional: key_column re-mapping
    key_column = section_conf.get("key_column")
    if key_column and products and key_column in products[0]:
        products_dict = {row[key_column]: row for row in products if row.get(key_column)}
        products = products_dict

    # Write final JSON
    with open(products_path, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    logging.info(f"Saved table data to: {products_path}")

def get_url_param(url: str, param_name: str):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return params.get(param_name, [None])[0]

# ---------- Main runner ----------

def run_scraper(config: dict, url: str, outdir: str):
    ensure_folder(outdir)
    soup = None

    runner_type = (
        config.get("runner", "requests")
        if isinstance(config, dict)
        else "requests"
    ).lower()

    try:
        logging.info("Loading page...")

        if os.path.exists(url):
            # local HTML file
            with open(url, "r", encoding="utf-8") as fh:
                html = fh.read()
        else:
            # dynamic choice based on runner
            if runner_type == "zyte":
                logging.info(f"Using runner: zyte")
                html = fetch_html_with_zyte(url)
            elif runner_type == "playwright":
                logging.info(f"Using runner: playwright")
                html = fetch_html_with_playwright(url)
            else:
                logging.info(f"Using runner: requests")
                resp = http_get(url)
                if not resp:
                    logging.error(f"Failed to fetch {url} via proxy.")
                    return
                html = resp.text

        soup = BeautifulSoup(html, "html.parser")

    except Exception as e:
        logging.error(f"Failed to load URL/file {url}: {e}")
        return

    # ---------- derive base URL from provided URL ----------
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}/"
    # -------------------------------------------------------

    url_type = detect_url_type(soup, config.get("url_types", {}), url)
    logging.info(f"Detected URL type: {url_type}")

    url_conf = config.get("url_types", {}).get(url_type, {})
    sections = url_conf.get("sections", {})

    for section_name, section_conf in sections.items():
        process_section(section_name, section_conf, soup, outdir, url, base_url)
    base = os.path.basename(os.path.normpath(outdir)).lower()
    if base.startswith("part"):
        mandatory_part_subfolders = [
            "markdowns",
            "images",
            "documentation",
            "block_diagrams",
            "design_resources",
            "software_tools",
            "tables",
            "trainings",
            "other"
        ]
        for folder in mandatory_part_subfolders:
            folder_path = os.path.join(outdir, folder)
            os.makedirs(folder_path, exist_ok=True)

def init(g, config=None):
    global glob
    glob = g
    parser = argparse.ArgumentParser(description="Config-driven scraper")
    parser.add_argument("--url", required=True, help="URL or local HTML file path to scrape")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()
    if not config or not isinstance(config, dict):
        logging.error("Config is empty or invalid. Please provide a valid config file.")
        return
    run_scraper(config, args.url, args.out)

# ---------- CLI ----------
# if __name__ == "__main__":
#     init()