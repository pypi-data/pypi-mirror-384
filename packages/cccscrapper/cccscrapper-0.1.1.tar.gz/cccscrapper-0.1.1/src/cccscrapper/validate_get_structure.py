#!/usr/bin/env python3
import json
import re
import sys
import logging
import argparse
from urllib.parse import urlparse

# ----------------------------
# Logging setup
# ----------------------------
logger = logging.getLogger("validate_json")
logger.setLevel(logging.DEBUG)

if not logger.hasHandlers():
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Prevent messages from propagating to root logger
logger.propagate = False

# ----------------------------
# Validation constants
# ----------------------------
ALLOWED_KEYS = {"name", "sub_topics", "url", "breadcrumbs"}
EXPECTED_KEY_ORDER = ["name", "url", "sub_topics", "breadcrumbs"]

URL_PATTERN = re.compile(
    r'^(https?:\/\/)'               # http:// or https://
    r'([A-Za-z0-9.-]+)'             # domain (hostname or subdomain)
    r'(\.[A-Za-z]{2,})'             # TLD
    r'(\/[A-Za-z0-9._~:/?#@!$&\'()*+,;=%-]*)?$'  # optional path/query
)

# ----------------------------
# URL validation
# ----------------------------
def is_valid_url(url):
    if not isinstance(url, str) or not url.strip():
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme.lower() not in ("http", "https"):
        return False
    if not parsed.netloc or "." not in parsed.netloc:
        return False
    return bool(URL_PATTERN.match(url))

# ----------------------------
# Key order validation
# ----------------------------
def validate_key_order(topic, path):
    errors = []
    keys = list(topic.keys())
    if set(keys) != set(EXPECTED_KEY_ORDER):
        missing = [k for k in EXPECTED_KEY_ORDER if k not in keys]
        extra = [k for k in keys if k not in EXPECTED_KEY_ORDER]
        if missing:
            errors.append(f"[{path}] Missing keys: {missing}")
        if extra:
            errors.append(f"[{path}] Unexpected keys: {extra}")
        return errors
    if keys != EXPECTED_KEY_ORDER:
        errors.append(f"[{path}] Keys out of order: found {keys}, expected {EXPECTED_KEY_ORDER}")
    return errors

# ----------------------------
# Recursive topic validation
# ----------------------------
def validate_topic(topic, path="root"):
    errors = []

    for key in topic.keys():
        if key not in ALLOWED_KEYS:
            errors.append(f"[{path}] Unexpected key: '{key}'")

    errors.extend(validate_key_order(topic, path))

    for key in ("name", "url", "breadcrumbs"):
        if key not in topic:
            errors.append(f"[{path}] Missing mandatory key: '{key}'")

    name = topic.get("name", "")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"[{path}] 'name' cannot be empty")

    url = topic.get("url")
    if url is None:
        errors.append(f"[{path}] Missing 'url'")
    elif not isinstance(url, str) or not url.strip():
        errors.append(f"[{path}] 'url' must be a non-empty string")
    elif not is_valid_url(url):
        errors.append(f"[{path}] Invalid URL format: {url}")

    breadcrumbs = topic.get("breadcrumbs")
    if not isinstance(breadcrumbs, list):
        errors.append(f"[{path}] 'breadcrumbs' must be a list")
    elif not breadcrumbs:
        errors.append(f"[{path}] 'breadcrumbs' cannot be empty")
    elif breadcrumbs[0] not in ("Products", "Catalog"):
        errors.append(f"[{path}] First breadcrumb must be 'Products' or 'Catalog', got '{breadcrumbs[0]}'")

    sub_topics = topic.get("sub_topics")
    if sub_topics is None:
        errors.append(f"[{path}] Missing key: 'sub_topics'")
    elif not isinstance(sub_topics, list):
        errors.append(f"[{path}] 'sub_topics' must be a list")
    else:
        for i, sub in enumerate(sub_topics):
            errors.extend(validate_topic(sub, path=f"{path}.sub_topics[{i}]"))

    return errors

# ----------------------------
# JSON file validation
# ----------------------------
def validate_json_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        logger.error("Top-level JSON must be a list")
        sys.exit(1)

    all_errors = []
    for i, topic in enumerate(data):
        all_errors.extend(validate_topic(topic, path=f"root[{i}]"))

    if all_errors:
        logger.error("Validation failed with errors:")
        for err in all_errors:
            logger.error(" - " + err)
        sys.exit(1)
    else:
        logger.info("JSON validation passed successfully")
        sys.exit(0)

# ----------------------------
# CLI
# ----------------------------
def init():
    parser = argparse.ArgumentParser(description="Validate JSON topic structure")
    parser.add_argument("--out", required=True, help="Path to the JSON file to validate")
    args = parser.parse_args()

    logger.info(f"Starting validation for file: {args.out}")
    validate_json_file(args.out)

# if __name__ == "__main__":
#     init()
