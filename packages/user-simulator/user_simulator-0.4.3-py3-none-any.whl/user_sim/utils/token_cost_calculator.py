import re
import os
import base64
import tiktoken
import requests
import pandas as pd
import logging
from typing import Any
from io import BytesIO
from PIL import Image
from langchain_core.output_parsers import StrOutputParser
from user_sim.utils import config
from user_sim.utils.utilities import get_encoding

logger = logging.getLogger('Info Logger')

columns = ["Conversation", "Test Name", "Module", "Model", "Total Cost",
           "Timestamp", "Input Cost", "Input Message",
           "Output Cost", "Output Message"]

PRICING = {
    "gpt-4o": {"input": 2.5 / 10**6, "output": 10 / 10**6},
    "gpt-4o-mini": {"input": 0.15 / 10**6, "output": 0.6 / 10**6},
    "whisper": 0.006/60,
    "tts-1": 0.0015/1000,  # (characters, not tokens)
    "gemini-2.0-flash": 0
}

TOKENS = {
    "gpt-4o": {"input": 10**6/2.5, "output": 10**6/10},
    "gpt-4o-mini": {"input": 10**6/0.15, "output": 10**6/0.6},
    "whisper": 60/0.006,
    "tts-1": 1000/0.0015,  # (characters, not tokens)
    "gemini-2.0-flash": 0

}

MAX_MODEL_TOKENS = {
    "gpt-4o": 16384,
    "gpt-4o-mini": 16384,
    "gemini-2.0-flash": 10000000
}


DEFAULT_COSTS = {
    # OpenAI models costs per 1M tokens
    "gpt-4o": {"prompt": 5.00, "completion": 20.00},
    "gpt-4o-mini": {"prompt": 0.60, "completion": 2.40},
    "gpt-4.1": {"prompt": 2.00, "completion": 8.00},
    "gpt-4.1-mini": {"prompt": 0.40, "completion": 1.60},
    "gpt-4.1-nano": {"prompt": 0.10, "completion": 0.40},
    # Google/Gemini models costs per 1M tokens
    "gemini-2.0-flash": {"prompt": 0.10, "completion": 0.40},
    "gemini-2.5-flash-preview-05-2023": {"prompt": 0.15, "completion": 0.60},
    # Default fallback rates if model not recognized
    "default": {"prompt": 0.10, "completion": 0.40},
}


def create_cost_dataset(serial: str | int, test_cases_folder: str) -> None:
    """
    Create and initialize a CSV dataset to track model usage costs.

    Args:
        serial (str | int): Unique identifier for this test run (used in file name).
        test_cases_folder (str): Path to the folder where reports should be stored.

    Side effects:
        - Creates `reports/__cost_reports__` folder inside test_cases_folder if it doesn't exist.
        - Writes an empty CSV file with predefined columns.
        - Updates `config.cost_ds_path` with the CSV path.
    """
    folder = f"{test_cases_folder}/reports/__cost_reports__"
    file = f"cost_report_{serial}.csv"
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created cost report folder at: {folder}")

    path = f"{folder}/{file}"

    cost_df = pd.DataFrame(columns=columns)
    cost_df.to_csv(path, index=False)
    config.cost_ds_path = path
    logger.info(f"Cost dataframe created at {path}.")


def count_tokens(text: Any, model: str = "gpt-4o-mini"):
    """
    Count the number of tokens in a given text using the specified model.

    Args:
        text (str | list | Any): Input text (or object convertible to string).
        model (str): Model name for encoding. Default is "gpt-4o-mini".

    Returns:
        int: Number of tokens in the input text.

    Notes:
        - If the model is not recognized by tiktoken, falls back to "cl100k_base".
        - Non-string inputs are cast to string before tokenization.
    """
    try:
        # First try to use the model name directly with tiktoken
        encoding = tiktoken.encoding_for_model(model)
    except (KeyError, ValueError):
        # If tiktoken doesn't recognize the model, use cl100k_base encoding
        # which is used for GPT-4 family models including gpt-4o and gpt-4o-mini
        logger.warning(
            f"Model '{model}' not recognized by tiktoken, using cl100k_base encoding"
        )
        encoding = tiktoken.get_encoding("cl100k_base")

    if not isinstance(text, str) or not isinstance(text, list):
        text = str(text)

    return len(encoding.encode(text))


def calculate_text_cost(tokens: int, model: str = "gpt-4o-mini", io_type: str = "input") -> float:
    """
    Calculate the cost of processing text tokens for a given model.

    Args:
        tokens (int): Number of tokens to evaluate.
        model (str): Model name. Must exist in the PRICING dictionary. Default is "gpt-4o-mini".
        io_type (str): Type of token cost to calculate.
                       Options are "input" or "output". Default is "input".

    Returns:
        float: The cost in USD for the given token count.

    Raises:
        ValueError: If the model or io_type is not available in PRICING.
    """
    cost = tokens * PRICING[model][io_type]
    return cost


def calculate_image_cost(image: str | bytes) -> float | None:
    """
    Estimate the cost of processing an image based on its dimensions.

    The function supports images provided as:
    - A URL string (http/https).
    - A base64-encoded string.
    - Raw bytes containing a base64-encoded string.

    The cost is estimated using a tile-based system (512x512 px tiles),
    with fixed base tokens and per-tile token multipliers.

    Args:
        image (str | bytes): The image input (URL, base64 string, or base64 bytes).

    Returns:
        float | None: The estimated cost in USD, or None if dimensions couldn't be retrieved.
    """
    def get_dimensions(image_input):
        try:
            if isinstance(image_input, bytes):
                image_input = image_input.decode('utf-8')
            if re.match(r'^https?://', image_input) or re.match(r'^http?://', image_input):  # Detects if it's a URL
                response = requests.get(image_input)
                response.raise_for_status()  #
                image = Image.open(BytesIO(response.content))
            else:
                decoded_image = base64.b64decode(image_input)
                image = Image.open(BytesIO(decoded_image))

            # Get the dimensions
            w, h = image.size
            return w, h
        except Exception as e:
            logger.error(e)
            return None

    dimensions = get_dimensions(image)
    if dimensions is None:
        logger.warning("Couldn't get image dimensions.")
        return None
    width, height = dimensions

    # Initial configuration
    price_per_million_tokens = 0.15
    tokens_per_tile = 5667
    base_tokens = 2833

    # Calculate the number of tiles needed (512 x 512 pixels)
    horizontal_tiles = (width + 511) // 512
    vertical_tiles = (height + 511) // 512
    total_tiles = horizontal_tiles * vertical_tiles

    # Calculate the total tokens
    total_tokens = base_tokens + (tokens_per_tile * total_tiles)

    # Convert tokens to price
    total_price = (total_tokens / 1_000_000) * price_per_million_tokens

    return total_price


# VISION
def input_vision_module_cost(input_message: str, image: Any, model: str) -> float:
    """
    Calculate the input cost for a vision-enabled model call.

    This function computes the cost of processing both text tokens and an
    image in a multimodal request. The text input is tokenized and priced
    according to the model’s input cost, and the image is priced separately
    via `calculate_image_cost`.

    Args:
        input_message (str): The text prompt provided to the model.
        image (Any): Image input (format expected by `calculate_image_cost`).
        model (str): Identifier of the model (must exist in `PRICING`).

    Returns:
        float: The total input cost in USD, combining text and image costs.

    Notes:
        - Uses `count_tokens` to estimate text token usage.
        - Uses `calculate_image_cost` to determine the cost of the image.
        - If image cost cannot be computed (`None`), it defaults to 0
          and logs a warning.
        - Pricing information is retrieved from the global `PRICING` dictionary.
    """
    input_tokens = count_tokens(input_message, model)
    image_cost = calculate_image_cost(image)
    if image_cost is None:
        logger.warning("Image cost set to $0.")
        image_cost = 0

    model_pricing = PRICING[model]
    input_cost = input_tokens * model_pricing["input"] + image_cost
    return input_cost

def output_vision_module_cost(output_message: str, model: str) -> float:
    """
    Calculate the output cost for a vision-enabled model call.

    This function computes the cost of the model’s generated response
    (text output) based on the number of tokens and the model’s
    pricing information.

    Args:
        output_message (str): The text response generated by the model.
        model (str): Identifier of the model (must exist in `PRICING`).

    Returns:
        float: The total output cost in USD.

    Notes:
        - Uses `count_tokens` to estimate token usage in the output.
        - Multiplies the number of tokens by the model's output price
          from the global `PRICING` dictionary.
        - Only the text output cost is considered. Image costs are handled
          separately in the input phase (`input_vision_module_cost`).
    """
    output_tokens = count_tokens(output_message, model)
    model_pricing = PRICING[model]
    output_cost = output_tokens * model_pricing["output"]
    return output_cost


# TTS-STT
def input_tts_module_cost(input_message: str, model: str) -> float:
    """
    Calculate the input cost for a Text-to-Speech (TTS) model.

    The cost is computed based on the length of the input message
    (in characters) and the per-character pricing for the given model.

    Args:
        input_message (str): The text to be synthesized into speech.
        model (str): The TTS model identifier (must exist in `PRICING`).

    Returns:
        float: The total input cost in USD.

    Notes:
        - Unlike text models (which use tokens), TTS models are billed
          per character.
        - Uses the `"input"` field from the `PRICING` dictionary.
    """
    model_pricing = PRICING[model]
    input_cost = len(input_message) * model_pricing
    return input_cost

def whisper_module_cost(audio_length: float, model: str) -> float:
    """
    Calculate the cost of using a Whisper (STT) model.

    The cost is based on the length of the audio (in seconds)
    and the per-second pricing defined in `PRICING`.

    Args:
        audio_length (float): Length of the audio in seconds.
        model (str): The Whisper model identifier (must exist in `PRICING`).

    Returns:
        float: The total input cost in USD.

    Notes:
        - Whisper models are billed per second of audio.
        - Uses the `"input"` field from the `PRICING` dictionary.
    """
    if audio_length is None:
        logger.warning("Audio length is None, returning cost = 0.")
        return 0.0

    model_pricing = PRICING[model]["input"]
    input_cost = audio_length * model_pricing
    return input_cost


# TEXT
def input_text_module_cost(input_message: str | list, model: str) -> float:
    """
    Calculate the input cost for a text-based model.

    The cost is determined by counting tokens in the input message
    and multiplying by the model's per-token input price.

    Args:
        input_message (str | list): The input text or list of text segments.
        model (str): The model identifier (must exist in `PRICING`).

    Returns:
        float: The total input cost in USD.
    """
    if isinstance(input_message, list):
        input_message = ", ".join(input_message)
    input_tokens = count_tokens(input_message, model)
    model_pricing = PRICING[model]
    input_cost = input_tokens * model_pricing["input"]
    return input_cost

def output_text_module_cost(output_message: str | list, model: str) -> float:
    """
    Calculate the output cost for a text-based model.

    The cost is determined by counting tokens in the output message
    and multiplying by the model's per-token output price.

    Args:
        output_message (str | list): The model output text or list of text segments.
        model (str): The model identifier (must exist in `PRICING`).

    Returns:
        float: The total output cost in USD.
    """
    if isinstance(output_message, list):
        output_message = ", ".join(output_message)
    output_tokens = count_tokens(output_message, model)
    model_pricing = PRICING[model]
    output_cost = output_tokens * model_pricing["output"]
    return output_cost


def calculate_cost(input_message: str = '',
                   output_message: str = '',
                   model: str = "gpt-4o",
                   module: str | None = None,
                   **kwargs):
    """
    Calculate and update the cost of an interaction with an AI module.

    Supports text, vision, speech-to-text (Whisper), and text-to-speech (TTS)
    models. Costs are logged and appended to a CSV report, while cumulative
    totals are updated in the global `config`.

    Args:
        input_message (str, optional): Input text sent to the model.
        output_message (str, optional): Output text returned by the model.
        model (str, optional): Model name (e.g., "gpt-4o", "whisper", "tts-1").
        module (str, optional): Module name for cost attribution.
        **kwargs: Extra parameters, e.g.:
            - image (bytes | str): For vision models, image content or URL.
            - audio_length (float): For Whisper, audio duration in seconds.

    Raises:
        ValueError: If pricing information for the model is unavailable.

    Effects:
        - Appends a new row with cost details to `config.cost_ds_path` (CSV).
        - Updates global totals in `config.total_cost` and
          `config.total_individual_cost`.
    """
    # input_tokens = count_tokens(input_message, model)
    # output_tokens = count_tokens(output_message, model)

    if input_message is None:
        input_message = ""
    if output_message is None:
        output_message = ""

    if model not in PRICING:
        raise ValueError(f"Pricing not available for model: {model}")

    if model == "whisper":
        input_cost = 0
        output_cost = whisper_module_cost(kwargs.get("audio_length", None), model)
        total_cost = output_cost

    elif model == "tts-1":
        input_cost = input_tts_module_cost(input_message, model)
        output_cost = 0
        total_cost = input_cost

    elif kwargs.get("image", None):
        input_cost = input_vision_module_cost(input_message, kwargs.get("image", None), model)
        output_cost = output_vision_module_cost(output_message, model)
        total_cost = input_cost + output_cost

    else:
        input_cost = input_text_module_cost(input_message, model)
        output_cost = output_text_module_cost(output_message, model)
        total_cost = input_cost + output_cost

    new_row = {"Conversation": config.conversation_name, "Test Name": config.test_name, "Module": module,
               "Model": model, "Total Cost": total_cost, "Timestamp": pd.Timestamp.now(),
               "Input Cost": input_cost, "Input Message": input_message,
               "Output Cost": output_cost, "Output Message": output_message}

    encoding = get_encoding(config.cost_ds_path)["encoding"]
    cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
    cost_df.loc[len(cost_df)] = new_row
    cost_df.to_csv(config.cost_ds_path, index=False)

    config.total_cost = config.total_individual_cost = float(cost_df['Total Cost'].sum())

    logger.info(f"Updated 'cost_report' dataframe with new cost from {module}.")


def get_cost_report(test_cases_folder):
    """
    Export the accumulated cost report to a CSV file inside the test case folder.

    Creates a `reports/__cost_report__` directory (if missing) and saves a
    timestamped copy of the global cost report. The report is based on the
    contents of `config.cost_ds_path`.

    Args:
        test_cases_folder (str): Path to the folder containing test cases.
            The report will be saved in `<test_cases_folder>/reports/__cost_report__`.

    Effects:
        - Creates a directory `<test_cases_folder>/reports/__cost_report__`
          if it does not exist.
        - Exports a CSV file named `report_<serial>.csv`, where `<serial>` is
          taken from `config.serial`.
        - Uses the same encoding as detected from `config.cost_ds_path`.

    Files:
        - Input: `config.cost_ds_path` (CSV with accumulated cost data).
        - Output: `<test_cases_folder>/reports/__cost_report__/report_<serial>.csv`.
    """
    export_path = test_cases_folder + f"/reports/__cost_report__"
    serial = config.serial
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    export_file_name = export_path + f"/report_{serial}.csv"

    encoding = get_encoding(config.cost_ds_path)["encoding"]
    temp_cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
    temp_cost_df.to_csv(export_file_name, index=False)


def max_input_tokens_allowed(text: str = '', model_used: str = 'gpt-4o-mini', **kwargs) -> bool:
    """
    Check if processing an input would exceed the configured token/cost limits.

    Simulates the cost of encoding the input text (and optionally additional
    inputs such as images or audio length) for the specified model, then verifies
    if adding it would surpass either the global or per-conversation limits
    defined in `config`.

    Args:
        text (str, optional): Input text to be processed. Defaults to "".
        model_used (str, optional): Model name to estimate cost for
            (e.g., "gpt-4o-mini", "tts-1", "whisper"). Defaults to "gpt-4o-mini".
        **kwargs: Extra parameters depending on the model:
            - image (bytes | str): Base64-encoded image or URL (for vision models).
            - audio_length (float): Audio length in seconds (for Whisper).

    Returns:
        bool:
            - True if adding the new input would exceed either the global
              (`config.limit_cost`) or conversation-specific
              (`config.limit_individual_cost`) cost limit.
            - False otherwise.

    Notes:
        - Requires `config.token_count_enabled` to be True; otherwise it
          always returns False.
        - Costs are computed with the helper functions:
            - `input_vision_module_cost` for vision models,
            - `input_tts_module_cost` for TTS,
            - `whisper_module_cost` for Whisper,
            - `input_text_module_cost` for standard text models.
        - Logs the remaining budget for both global and individual costs.
    """
    def get_delta_verification(sim_cost, sim_ind_cost):
        delta_cost = config.limit_cost - sim_cost
        delta_individual_cost = config.limit_individual_cost - sim_ind_cost
        logger.info(f"${delta_cost} for global and ${delta_individual_cost} for individual input cost left.")
        return True if delta_cost <= 0 or delta_individual_cost <= 0 else False

    if config.token_count_enabled:
        if kwargs.get("image", None):
            input_cost = input_vision_module_cost(text, kwargs.get("image", 0), model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        elif model_used == "tts-1":
            input_cost = input_tts_module_cost(text, model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        elif model_used == "whisper":
            input_cost = whisper_module_cost(kwargs.get("audio_length", 0), model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
        else:
            input_cost = input_text_module_cost(text, model_used)
            simulated_cost = input_cost + config.total_cost
            simulated_individual_cost = input_cost + config.total_individual_cost
            return get_delta_verification(simulated_cost, simulated_individual_cost)
    else:
        return False


def max_output_tokens_allowed(model_used):
    """
    Calculate the maximum number of output tokens that can be safely generated
    without exceeding global or conversation-specific cost limits.

    The function estimates the remaining budget by subtracting the current
    accumulated cost from the defined limits (`config.limit_cost` and
    `config.limit_individual_cost`). It then converts the remaining budget
    into token units based on the pricing information in `TOKENS`.

    Args:
        model_used (str): The model identifier (e.g., "gpt-4o-mini") whose
            output token pricing will be used for the calculation.

    Returns:
        int | None:
            - Maximum number of output tokens allowed for this model.
            - Capped at the model’s maximum token capacity (`MAX_MODEL_TOKENS`).
            - Returns None if `config.token_count_enabled` is False.

    Notes:
        - Relies on:
            - `TOKENS[model_used]["output"]`: cost per output token for the model.
            - `MAX_MODEL_TOKENS[model_used]`: hard maximum tokens supported by the model.
        - Logs the remaining token allowance before returning it.
    """
    if config.token_count_enabled:
        delta_cost = config.limit_cost - config.total_cost
        delta_individual_cost = config.limit_individual_cost - config.total_individual_cost

        delta = min([delta_cost, delta_individual_cost])
        output_tokens = round(delta * TOKENS[model_used]["output"])


        if MAX_MODEL_TOKENS[model_used]<output_tokens:
            output_tokens = MAX_MODEL_TOKENS[model_used]

        logger.info(f"{output_tokens} output tokens left.")
        return output_tokens
    else:
        return


def invoke_llm(llm, prompt, input_params, model, module, parser=False):

    # Outputs input messages as text.
    if isinstance(input_params, dict):
        messages = list(input_params.values())
        parsed_messages = " ".join(messages)
    else:
        parsed_messages = input_params

    # Measures max input tokens allowed by the execution
    if config.token_count_enabled and max_input_tokens_allowed(parsed_messages, model):
        logger.error(f"Token limit was surpassed in {module} module")
        return None

    # Calculates the amount of tokens left and updates the LLM max_tokens parameter
    if config.token_count_enabled:
        llm.max_tokens = max_output_tokens_allowed(model)

    # Enables str output parser
    if parser:
        parser = StrOutputParser()
        llm_chain = prompt | llm | parser
    else:
        llm_chain = prompt | llm

    # Invoke LLM
    try:
        response = llm_chain.invoke(input_params)
        if config.token_count_enabled:
            calculate_cost(parsed_messages, response, model, module="user_simulator")
    except Exception as e:
        logger.error(e)
        response = None
    if response is None and module == "user_simulator":
        response = "exit"

    return response
