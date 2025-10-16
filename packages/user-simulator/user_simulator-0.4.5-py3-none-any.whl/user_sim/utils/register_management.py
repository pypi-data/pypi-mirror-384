import os
import json
import hashlib
import logging
from user_sim.utils import config

temp_file_dir = config.cache_path

logger = logging.getLogger('Info Logger')


def save_register(register: dict, name: str) -> None:
    """
    Save a register (dict) to a JSON file in the temporary directory.

    Args:
        register (dict): The dictionary to save.
        name (str): File name of the register.
    """
    path = os.path.join(temp_file_dir, name)
    os.makedirs(temp_file_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        json.dump(register, file, ensure_ascii=False, indent=4)


def load_register(register_name: str) -> dict:
    """
    Load a register from the temporary directory.

    Args:
        register_name (str): File name of the register.

    Returns:
        dict: Contents of the register. Returns {} if not found.
    """
    register_path = os.path.join(temp_file_dir, register_name)
    if not os.path.exists(temp_file_dir):
        os.makedirs(temp_file_dir)
        return {}
    else:
        if not os.path.exists(register_path):
            with open(register_path, 'w',  encoding="utf-8") as file:
                json.dump({}, file, ensure_ascii=False, indent=4)
            return {}
        else:
            with open(register_path, 'r', encoding="utf-8") as file:
                hash_reg = json.load(file)
            return hash_reg


def hash_generate(content_type: str | None = None, hasher_cls=hashlib.md5, **kwargs) -> str:
    """
    Generate a hash for a given content or PDF file.

    Args:
        content_type (str, optional): "pdf" for PDFs, else hashes text or bytes.
        hasher_cls (Callable): A callable returning a new hasher instance
                               (default: hashlib.md5).
        **kwargs:
            - content (str|bytes): Text/bytes to hash.
            - content (str path): Path to a PDF if content_type == "pdf".

    Returns:
        str: Hex digest of the hash.
    """
    hasher = hasher_cls()

    if content_type == "pdf":
        with open(kwargs.get("content",""), 'rb') as pdf_file:
            hasher.update(pdf_file.read())
    else:
        content = kwargs.get('content', '')
        if isinstance(content, str):
            hasher.update(content.encode("utf-8"))
        else:
            hasher.update(content)

    return hasher.hexdigest()


def clear_register(register_name: str) -> None:
    """
    Clear (reset to empty {}) a given register file.

    Args:
        register_name (str): File name of the register.
    """
    try:
        path = os.path.join(temp_file_dir, register_name)
        with open(path, 'w') as file:
            json.dump({}, file)
    except Exception as e:
        logger.error("Couldn't clear cache because the cache file was not created during the execution.")


def clean_temp_files() -> None:
    """
    Clear all known cache registers.
    """
    clear_register("image_register.json")
    clear_register("pdf_register.json")
    clear_register("webpage_register.json")