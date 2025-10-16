import os
import sys
import json
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# Allowed folder names
ALLOWED_FOLDERS = {
    "documentation",
    "images",
    "block_diagrams",
    "design_resources",
    "software_tools",
    "tables",
    "markdowns",
    "trainings",
    "other"
}

# Folders where metadata.json is optional
METADATA_OPTIONAL = {"tables", "markdowns"}

# Keys in metadata.json
MANDATORY_KEYS = ["name", "file_path", "url"]
ALL_KEYS = ["name", "file_path", "version", "date", "url", "language", "description"]

# Mandatory files for specific folders
FOLDER_MANDATORY_FILES = {
    "markdowns": ["overview.md"],
    "tables": ["products.json"]
}

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def make_relative_path(path):
    """Convert absolute path to relative path from script directory."""
    return os.path.relpath(path, SCRIPT_DIR)

def validate_metadata_file(metadata_path, folder_path, base_output_dir):
    errors = []
    rel_folder_path = make_relative_path(folder_path)
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return errors
            data = json.loads(content)
    except Exception as e:
        errors.append(f"{rel_folder_path}/metadata.json -> Failed to read or parse JSON: {e}")
        return errors

    if not isinstance(data, list):
        errors.append(f"{rel_folder_path}/metadata.json -> metadata.json must be a list of objects")
        return errors

    folder_name = os.path.basename(folder_path)

    for i, item in enumerate(data):
        if not isinstance(item, dict):
            errors.append(f"{rel_folder_path}/metadata.json -> Item {i} is not an object")
            continue

        # Check mandatory keys
        for key in ALL_KEYS:
            if key not in item:
                errors.append(f"{rel_folder_path}/metadata.json -> Item {i} missing key '{key}'")
        for key in MANDATORY_KEYS:
            if key not in item or not item[key]:
                errors.append(f"{rel_folder_path}/metadata.json -> Item {i} mandatory field '{key}' is empty")

        # Check file exists
        if "file_path" in item and item["file_path"]:
            file_path = item["file_path"]
            if not os.path.exists(file_path):
                errors.append(f"{rel_folder_path}/metadata.json -> Item {i} file does not exist: {file_path}")
            else:
                # ✅ Check that the file is under the correct folder (folder_name)
                abs_file_path = os.path.abspath(file_path)
                abs_folder_path = os.path.abspath(folder_path)
                if folder_name not in abs_file_path.replace("\\", "/").split("/"):
                    errors.append(f"{rel_folder_path}/metadata.json -> Item {i} file is not under correct folder '{folder_name}': {file_path}")
                else:
                    # Optional: check that it's directly under the folder or in subfolder (like output_dir2/categoryinner/images/)
                    rel_to_output = os.path.relpath(abs_file_path, base_output_dir)
                    parts = rel_to_output.replace("\\", "/").split("/")
                    # parts[0] = category folder, parts[1..] = subfolders
                    if folder_name not in parts:
                        errors.append(f"{rel_folder_path}/metadata.json -> Item {i} file path is invalid relative to output folder: {file_path}")

    return errors


def validate_products_json(products_json_path, folder_path):
    errors = []
    rel_folder_path = make_relative_path(folder_path)
    try:
        with open(products_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        errors.append(f"{rel_folder_path}/products.json -> Failed to read or parse JSON: {e}")
        return errors

    if not data:
        return errors  # Empty JSON is allowed

    if not isinstance(data, dict):
        errors.append(f"{rel_folder_path}/products.json -> products.json must be a dictionary of products")
        return errors

    for key, product in data.items():
        if not isinstance(product, dict):
            errors.append(f"{rel_folder_path}/products.json -> Product '{key}' should be a dictionary")
            continue
        # Product key must match "Product" field
        if "Product" not in product:
            errors.append(f"{rel_folder_path}/products.json -> Product '{key}' missing 'Product' field")
        elif str(product["Product"]).strip() != str(key).strip():
            errors.append(f"{rel_folder_path}/products.json -> Product '{key}' field 'Product' does not match the key")

    return errors


def validate_strict_folder_contents(folder_path):
    """
    Ensure only allowed files are present.
    overview.md and parametric_table.json are optional,
    but if they exist, they must not be empty.
    No extra files or folders are allowed.
    """
    allowed_category_files = {"overview.md", "parametric_table.json"}
    errors = []
    rel_folder_path = make_relative_path(folder_path)

    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if os.path.isdir(item_path):
            errors.append(f"{rel_folder_path} -> Unexpected subfolder: {item}")
        elif item not in allowed_category_files:
            errors.append(f"{rel_folder_path} -> Unexpected file: {item}")
        else:
            # File exists: check if empty
            if os.path.getsize(item_path) == 0:
                errors.append(f"{rel_folder_path} -> File is empty: {item}")
            elif item == "parametric_table.json":
                # Additional check: if JSON and empty dict
                try:
                    with open(item_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and not data:
                        errors.append(f"{rel_folder_path} -> parametric_table.json is an empty dictionary")
                except Exception as e:
                    errors.append(f"{rel_folder_path} -> Failed to read parametric_table.json: {e}")

    return errors


def validate_directories(base_dirs, root_folder):
    errors = []

    def _validate_folder(folder_path):
        rel_folder_path = make_relative_path(folder_path)
        if not os.path.exists(folder_path):
            logging.warning(f"{rel_folder_path} -> Folder does not exist")
            return

        logging.info(f"Checking folder: {rel_folder_path}")

        folder_name = os.path.basename(os.path.normpath(folder_path))

        # ✅ NEW: If this is the "part" folder, ensure all ALLOWED_FOLDERS exist
        print(folder_name)
        if folder_name == "part":
            for mandatory_subfolder in ALLOWED_FOLDERS:
                expected_path = os.path.join(folder_path, mandatory_subfolder)
                if not os.path.isdir(expected_path):
                    err = f"{rel_folder_path} -> Missing mandatory subfolder: {mandatory_subfolder}"
                    errors.append(err)
                    logging.error(err)

        if root_folder in {"category", "sub_category"}:
            # This is a category/sub-category folder: only allow two files
            strict_errors = validate_strict_folder_contents(folder_path)
            for se in strict_errors:
                errors.append(se)
                logging.error(se)

        elif folder_name in ALLOWED_FOLDERS:
            # Check metadata.json if required
            metadata_file = os.path.join(folder_path, "metadata.json")
            if folder_name not in METADATA_OPTIONAL:
                if not os.listdir(folder_path):
                    # ✅ Allow completely empty folder as valid
                    logging.info(f"{rel_folder_path} -> Empty folder allowed (no metadata.json needed)")
                elif not os.path.exists(metadata_file):
                    errors.append(f"{rel_folder_path} -> Missing metadata.json")
                    logging.error(f"{rel_folder_path}/metadata.json not found")
                else:
                    metadata_errors = validate_metadata_file(metadata_file, folder_path, base_dirs[0])
                    for me in metadata_errors:
                        errors.append(me)
                        logging.error(me)
            else:
                if os.path.exists(metadata_file):
                    metadata_errors = validate_metadata_file(metadata_file, folder_path, base_dirs[0])
                    for me in metadata_errors:
                        errors.append(me)
                        logging.error(me)

            # Check folder-specific mandatory files
            if folder_name in FOLDER_MANDATORY_FILES:
                for mandatory_file in FOLDER_MANDATORY_FILES[folder_name]:
                    mandatory_path = os.path.join(folder_path, mandatory_file)
                    if not os.path.exists(mandatory_path):
                        errors.append(f"{rel_folder_path} -> Missing mandatory file: {mandatory_file}")
                        logging.error(f"{rel_folder_path}/{mandatory_file} not found")
                    else:
                        if folder_name == "tables" and mandatory_file == "products.json":
                            product_errors = validate_products_json(mandatory_path, folder_path)
                            for pe in product_errors:
                                errors.append(pe)
                                logging.error(pe)

        # Recursively validate all subfolders
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                _validate_folder(item_path)

    for base_dir in base_dirs:
        _validate_folder(base_dir)

    if not errors:
        logging.info("All folders and mandatory files are valid!")
    else:
        logging.warning("Validation completed with errors:")
        for err in errors:
            logging.warning(f"- {err}")


def init():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", help="Path to output JSON file (e.g., output/topic_structure.json)")
    args = parser.parse_args()
    root_folder = ''
    output_file = args.out
    if not output_file:
        output_dir = [os.path.join(SCRIPT_DIR, d) for d in os.listdir(SCRIPT_DIR) if os.path.isdir(os.path.join(SCRIPT_DIR, d))]
    else:
        if not output_file.strip():
            parser.error("--out argument cannot be empty")
        if not os.path.exists(output_file) or not os.path.isdir(output_file):
            logging.error(f"Specified folder does not exist: {output_file}")
            return
        root_folder = os.path.basename(os.path.normpath(output_file))
        output_dir = [output_file]

    if not output_dir:
        logging.error("please specify folder you have to validate")
        return
    validate_directories(output_dir, root_folder)

# MAIN FUNCTION
# if __name__ == "__main__":
#     init()