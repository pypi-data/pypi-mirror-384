import os
import pandas as pd
import yaml
import json
import configparser
import re
import random
import importlib.util
import logging
import platform

from typing import Any, Optional
from colorama import Fore, Style
from datetime import datetime, timedelta, date
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from user_sim.utils.exceptions import *
from user_sim.utils import config
from langchain.chat_models import init_chat_model
from charset_normalizer import detect

logger = logging.getLogger('Info Logger')

def print_user(msg: str):
    """
    Print a user message cleaned of metadata annotations.

    Removes:
    - (Web page content: ... >>)
    - (PDF content: ... >>)
    - (Image description ...)

    Args:
        msg (str): Raw message containing possible metadata.
    """
    clean_text = re.sub(r'\(Web page content: [^)]*>>\)', '', msg)
    clean_text = re.sub(r'\(PDF content: [^)]*>>\)', '', clean_text)
    clean_text = re.sub(r'\(Image description[^)]*\)', '', clean_text)
    print(f"{Fore.GREEN}User:{Style.RESET_ALL} {clean_text}")


def print_chatbot(msg: str):
    """
    Print a chatbot message cleaned of metadata annotations.

    Removes:
    - (Web page content: ... >>)
    - (PDF content: ... >>)
    - (Image description ...)

    Args:
        msg (str): Raw chatbot message containing possible metadata.
    """
    clean_text = re.sub(r'\(Web page content:.*?\>\>\)', '', msg, flags=re.DOTALL)
    clean_text = re.sub(r'\(PDF content:.*?\>\>\)', '', clean_text, flags=re.DOTALL)
    clean_text = re.sub(r'\(Image description[^)]*\)', '', clean_text)
    print(f"{Fore.LIGHTRED_EX}Chatbot:{Style.RESET_ALL} {clean_text}")


def end_alarm(sound_path: str = "config/misc/sound/c1bccaed.wav") -> None:
    """
    Play an alarm sound at the end of a process.

    - On Windows: uses winsound.
    - On macOS: uses afplay.
    - On Linux: uses aplay or paplay (depending on availability).
    - If sound playback fails, silently does nothing.

    Args:
        sound_path (str): Path to the sound file (default: c1bccaed.wav).
    """
    os_name = platform.system()

    try:
        if os_name == "Windows":
            import winsound
            winsound.PlaySound(sound_path, winsound.SND_FILENAME)

        elif os_name == "Darwin":  # macOS
            os.system(f"afplay {sound_path} >/dev/null 2>&1 &")

        elif os_name == "Linux":
            # Try with aplay first, then paplay
            if os.system(f"command -v aplay >/dev/null") == 0:
                os.system(f"aplay {sound_path} >/dev/null 2>&1 &")
            elif os.system(f"command -v paplay >/dev/null") == 0:
                os.system(f"paplay {sound_path} >/dev/null 2>&1 &")
            else:
                print("No audio player found for Linux.")

    except Exception as e:
        print(f"Failed to play alarm sound: {e}")


def init_model() -> tuple[str, Any]:
    """
    Initialize and return a chat model along with its name.

    This function reads the global configuration (`config.model` and
    `config.model_provider`) and initializes a chat model accordingly.

    Returns:
        tuple:
            - str: Model name.
            - Any: Initialized LLM/chat model instance.
    """
    model = config.model
    model_provider = config.model_provider
    if model_provider is None:
        params = {
            "model": model,
        }
    else:
        params = {
            "model": model,
            "model_provider": model_provider,
        }
    llm = init_chat_model(**params)

    return model, llm


def load_yaml_files_from_folder(
        folder_path: str, existing_keys: Optional[set[str]]=None
) -> dict[str, dict]:
    """
    Load YAML files from a folder into a dictionary indexed by the `name` field.

    Args:
        folder_path (str): Path to the folder containing `.yml` or `.yaml` files.
        existing_keys (set[str], optional): If provided, YAML entries whose
            `name` is in this set will be skipped.

    Returns:
        dict[str, dict]: A dictionary where keys are the `name` values found in
        the YAML files, and values are the parsed YAML data.

    Notes:
        - Files without a `name` field are ignored.
        - Invalid YAML files are skipped, and the error is logged.
    """
    types = {}
    for filename in os.listdir(folder_path):
        if filename.endswith((".yml", ".yaml")):
            file_path = os.path.join(folder_path, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    name = data.get("name")
                    if name:
                        if not existing_keys or name not in existing_keys:
                            types[name] = data
            except yaml.YAMLError as e:
                logger.error(f"Error reading {file_path}: {e}")
    return types


def parse_content_to_text(messages):
    """
    Concatenate the 'content' field from a list of message dictionaries into a single string.

    Args:
        messages: A list of dictionaries, each possibly containing a "content" key with string data.

    Returns:
        A single string with all content values joined by spaces.
    """
    return " ".join([message["content"] for message in messages if "content" in message])


def parse_profiles(user_path):
    """
    Load one or more user profile YAML files from a given path.

    Args:
        user_path: Path to a YAML file or a directory containing YAML files.

    Returns:
        A list of dictionaries, each parsed from a YAML profile file.

    Raises:
        FileNotFoundError: If the path does not exist.
        ValueError: If the path is not a valid YAML file or directory.
    """
    def is_yaml(file_path: str) -> bool:
        """Check if a file is a valid YAML file."""
        if not file_path.endswith(('.yaml', '.yml')):
            return False
        try:
            with open(file_path, 'r', encoding="utf-8") as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError:
            return False

    list_of_files = []
    if os.path.isfile(user_path):
        if is_yaml(user_path):
            yaml_file = read_yaml(user_path)
            return [yaml_file]
        else:
            raise Exception(f'The user profile file is not a yaml: {user_path}')

    elif os.path.isdir(user_path):
        for root, _, files in os.walk(user_path):
            for file in files:
                if is_yaml(os.path.join(root, file)):
                    path = root + '/' + file
                    yaml_file = read_yaml(path)
                    list_of_files.append(yaml_file)

            return list_of_files
    else:
        raise Exception(f'Invalid path for user profile operation: {user_path}')


def get_encoding(encoded_file: str):
    """
    Detect the character encoding of a given file.

    This function reads the first 4KB of the file (to avoid high memory usage with large files)
    and uses the `chardet` library's `detect` function to guess the encoding.
    If the detection fails or no encoding is found, it falls back to UTF-8.

    Args:
        encoded_file (str): Path to the file to analyze.

    Returns:
        dict: A dictionary containing at least:
              - "encoding" (str): The detected or fallback encoding.
              - "confidence" (float, optional): Confidence level of the detection.
    """
    with open(encoded_file, 'rb') as file:
        detected = detect(file.read())
        return detected


def save_json(msg: Any, test_name: str, path: str) -> None:
    """
    Save a Python object as a JSON file with a timestamped filename.

    The file is named using the provided test name and the current timestamp
    (formatted as `YYYY-MM-DD_HH-MM-SS`) to ensure uniqueness.

    Args:
        msg (Any): The data to be serialized into JSON format (must be JSON serializable).
        test_name (str): A label or identifier that will be included in the filename.
        path (str): Directory where the JSON file will be saved.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = os.path.join(path, f'{test_name}_{timestamp}.json')
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(msg, file, indent=4)


def str_to_bool(s: str) -> bool:
    """
    Convert a string representation of truth to a boolean value.

    Accepts common textual representations of boolean values such as:
    - True: "true", "1", "yes", "y"
    - False: "false", "0", "no", "n"

    The check is case-insensitive.

    Args:
        s (str): The input string to convert.

    Returns:
        bool: The corresponding boolean value (True or False).

    Raises:
        ValueError: If the string does not match any known boolean representation.
    """
    if s.lower() in ['true', '1', 'yes', 'y']:
        return True
    elif s.lower() in ['false', '0', 'no', 'n']:
        return False
    else:
        raise ValueError(f"Cannot convert {s} to boolean")


def execute_list_function(path: str, function_name: str, arguments: Any = None) -> Any:
    """
    Dynamically import a Python module from a given file path and execute a specified function.

    This function allows executing external functions by loading a module at runtime.
    It supports passing both positional and keyword arguments.

    Args:
        path (str): Path to the Python file containing the target function.
        function_name (str): Name of the function to execute from the module.
        arguments (list | dict | any, optional): Arguments to pass to the function.
            - If None: The function will be executed without arguments.
            - If list: Elements will be split into positional args and dicts into keyword args.
            - If dict: Will be treated as keyword arguments.
            - If any other type: Will be wrapped into a list as a single positional argument.

    Returns:
        Any: The result of the executed function.

    Raises:
        InvalidFormat: If the provided arguments do not match the function signature.
        AttributeError: If the specified function is not found in the module.
        FileNotFoundError: If the module file does not exist.
        ImportError: If the module cannot be loaded.
    """
    spec = importlib.util.spec_from_file_location("my_module", path)
    my_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(my_module)

    function_to_execute = getattr(my_module, function_name)

    if arguments:

        if not isinstance(arguments, list):
            arguments = [arguments]

        args = [item for item in arguments if not isinstance(item, dict)]
        dict_list = [item for item in arguments if isinstance(item, dict)]
        kwargs = {k: v for dic in dict_list for k, v in dic.items()}

        try:
            result = function_to_execute(*args, **kwargs)
        except TypeError as e:
            raise InvalidFormat(f"No arguments needed for this function: {e}")

    else:
        try:
            result = function_to_execute()
        except TypeError as e:
            raise InvalidFormat(f"Arguments are needed for this function: {e}")

    return result


def list_to_phrase(s_list: list, prompted: bool = False) -> str:
    """
    Convert a list of strings into a natural language phrase.

    This function takes a list of strings and concatenates them into a single
    phrase separated by commas, adding "or" before the last element for readability.
    Optionally, it can prepend a prompt to guide usage in chatbot contexts.

    Args:
        s_list (list of str): A list of strings to be joined into a phrase.
        prompted (bool, optional): If True, the returned phrase will be prefixed with
            "please, ask about". Defaults to False.

    Returns:
        str: A human-readable phrase constructed from the list.

    Raises:
        IndexError: If `s_list` is empty, since the function assumes at least one element.
    """
    # s_list: list of strings
    # l_string: string values extracted from s_list in string format
    l_string = s_list[0]

    if len(s_list) <= 1:
        return f"{s_list[0]}"
    else:
        for i in range(len(s_list) - 1):
            if s_list[i + 1] == s_list[-1]:
                l_string = f" {l_string} or {s_list[i + 1]}"
            else:
                l_string = f" {l_string}, {s_list[i + 1]}"

    if prompted:
        l_string = "please, ask about" + l_string

    return l_string


def read_yaml(file: str) -> Any:
    """
    Read and parse a YAML file into a Python object.

    This function checks if the given file has a valid YAML extension
    ('.yaml' or '.yml') and then attempts to safely load its contents
    using `yaml.safe_load`. If the file is not a YAML or contains
    invalid YAML syntax, it raises an exception.

    Args:
        file (str): Path to the YAML file to be read.

    Returns:
        Any: The parsed YAML content as a Python object
             (commonly a dictionary or list).

    Raises:
        InvalidFile: If the file does not have a `.yaml` or `.yml` extension.
        yaml.YAMLError: If the file contains invalid YAML syntax.
        FileNotFoundError: If the file path does not exist.
    """
    if not file.lower().endswith(('.yaml', '.yml')):
        raise InvalidFile("File type is not a YAML.")
    try:
        with open(file, 'r', encoding="UTF-8") as f:
            yaml_file = yaml.safe_load(f)
        return yaml_file
    except yaml.YAMLError as e:
        raise e


def generate_serial() -> str:
    """
    Generate a serial string based on the current date and time.

    The serial is formatted as `YYYY-MM-DD-HH-MM-SS`, which ensures
    uniqueness at the second level and can be used for naming files,
    logging runs, or tracking test sessions.

    Returns:
        str: A string representing the current date and time.
    """
    serial = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return serial


def normalize_regex_pattern(pattern: str) -> str:
    """
    Normalize a regex pattern string by removing raw string markers.

    This function checks if the input string is formatted as a raw string literal
    (e.g., r"...") enclosed in double quotes. If so, it removes the leading `r"`
    and trailing `"`, returning only the inner pattern.

    Args:
        pattern (str): The regex pattern string to normalize.
                       Example: 'r"\\d+"' or '\\d+'.

    Returns:
        str: The cleaned regex pattern string without raw string markers.
    """
    if pattern.startswith('r"') and pattern.endswith('"'):
        pattern = pattern[2:-1]

    return pattern


def build_sequence(pairs):
    """
    Build sequences from a list of directed pairs.

    Given a list of (a, b) pairs, this function constructs ordered sequences
    where each element maps to the next. A value of `None` marks the end of
    a sequence. The function returns a list of sequences starting from elements
    that are never used as endpoints.

    Args:
        pairs (list[tuple]): A list of tuples (a, b) where `a` maps to `b`.
                             If `b` is None, it represents the end of a sequence.

    Returns:
        list[list]: A list of sequences, where each sequence is represented
                    as a list of ordered elements.

    Raises:
        ValueError: If no valid starting point can be determined (e.g., in case
                    of cycles or malformed input).

    Example:
        >>> build_sequence([("A", "B"), ("B", "C"), ("C", None)])
        [['A', 'B', 'C']]

        >>> build_sequence([("dog", "cat"), ("cat", None), ("sun", "moon"), ("moon", None)])
        [['dog', 'cat'], ['sun', 'moon']]
    """
    mapping = {}
    starts = set()
    ends = set()
    for a, b in pairs:
        mapping[a] = b
        starts.add(a)
        if b is not None:
            ends.add(b)
    # Find starting words (appear in 'starts' but not in 'ends')
    start_words = starts - ends
    start_words.discard(None)
    sequences = []
    for start_word in start_words:
        sequence = [start_word]
        current_word = start_word
        while current_word in mapping and mapping[current_word] is not None:
            current_word = mapping[current_word]
            sequence.append(current_word)
        sequences.append(sequence)

    if not sequences:
        raise ValueError("Cannot determine a unique starting point.")
    return sequences
