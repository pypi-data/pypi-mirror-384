import re
import logging
from langchain.schema.messages import HumanMessage, SystemMessage
from user_sim.utils.token_cost_calculator import calculate_cost, max_input_tokens_allowed, max_output_tokens_allowed
from user_sim.utils import config
from user_sim.utils.utilities import init_model
from user_sim.utils.register_management import save_register, load_register, hash_generate


logger = logging.getLogger('Info Logger')
model = None
llm = None


image_register_name = "image_register.json"


def init_vision_module() -> None:
    """
    Initialize the vision module by creating a model and LLM instance.

    This function sets the global `model` and `llm` variables using
    the `init_model()` function, preparing them for vision-related tasks.
    """
    global model
    global llm
    model, llm = init_model()


def generate_image_description(image: str | bytes, url: bool = True, detailed: bool = False) -> str:
    """
    Generate a description of an image using the vision LLM module.

    Args:
        image (str | bytes): Image input, either as a URL (str) or a base64-encoded object (bytes).
        url (bool, optional): Whether the `image` argument is a URL (default: True).
        detailed (bool, optional): If True, produce a highly detailed description.
                                   If False, produce a concise summary (default: False).

    Returns:
        str: Text description of the image. Returns "Empty data" if the vision module
             is not initialized, or None if the token limit is exceeded.

    Notes:
        - Relies on global `llm` and `model` initialized by `init_vision_module()`.
        - Tracks token usage with `calculate_cost()` if cost counting is enabled.
        - Errors are logged and return fallback messages instead of raising exceptions.
    """
    if not url:
        image_parsed = f"data:image/png;base64,{image.decode('utf-8')}"
    else:
        image_parsed = image

    if detailed:
        prompt = ("""
                  Describe in detail this image and its content. 
                  If there's text, describe everything you read. don't give vague descriptions.
                  If there is content listed, read it as it is.
                  Be as detailed as possible.
                  """)
    else:
        prompt = "briefly describe this image, don't over explain, just give a simple and fast explanation of the main characteristics."

    if llm is None:
        logger.error("vision module not initialized.")
        return "Empty data"

    if max_input_tokens_allowed(prompt, model, image=image):
        logger.error(f"Token limit was surpassed")
        return None

    message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_parsed,
                            # "detail": "auto"
                        }
                    }
                ]
            )

    try:
        if config.token_count_enabled:
            llm.max_tokens = max_output_tokens_allowed(model)
            output = llm.invoke([message])
        else:
            output = llm.invoke([message])
        output_text = f"(Image description: {output.content})"
    except Exception as e:
        logger.error(e)
        logger.error("Couldn't get image description")
        output_text = "Empty data"
    logger.info(output_text)
    if config.token_count_enabled:
        calculate_cost(prompt, output_text, model=model, module="image recognition module", image=image)

    return output_text


def image_description(image: str |  bytes, detailed: bool = False, url: bool = True) -> str:
    """
    Generate and cache a description for an image.

    Args:
        image (str | bytes): Image input, either as a URL (str) or a base64-encoded object (bytes).
        detailed (bool, optional): If True, generate a detailed description. Defaults to False.
        url (bool, optional): Whether the `image` argument is a URL. Defaults to True.

    Returns:
        str: The description of the image, retrieved from cache if available
             or generated via `generate_image_description`.

    Notes:
        - Uses caching unless `config.ignore_cache` is enabled.
        - Updates the cache if `config.update_cache` is set.
        - Relies on `generate_image_description` for actual LLM-based description.
    """
    if config.ignore_cache:
        register = {}
        logger.info("Cache will be ignored.")
    else:
        register = load_register(image_register_name)

    image_hash = hash_generate(content=image)

    if image_hash in register:
        if config.update_cache:
            description = generate_image_description(image, url, detailed)
            register[image_hash] = description
            logger.info("Cache updated!")
        # description = register[image_hash]
        logger.info("Retrieved information from cache.")
        return register[image_hash]
    else:
        description = generate_image_description(image, url)
        register[image_hash] = description

    if config.ignore_cache:
        logger.info("Images cache was ignored")
    else:
        save_register(register, image_register_name)
        logger.info("Images cache was saved!")

    return description


def image_processor(text: str | None) -> str:
    """
    Process a text containing <image> tags by appending descriptions of each image.

    Args:
        text (str | None): Input text that may include <image>...</image> tags.

    Returns:
        str: Text with each <image> tag followed by its generated description.
             Returns the original text if no <image> tags are found or if `text` is None.

    Notes:
        - Uses `image_description()` to generate descriptions for the images.
        - Each image is described once and appended after its corresponding tag.
    """
    def get_images(phrase: str):
        pattern = r"<image>(.*?)</image>"
        matches = re.findall(pattern, phrase)
        return matches

    def replacer(match):
        nonlocal replacement_index, descriptions
        if replacement_index < len(descriptions):
            original_image = match.group(1)
            replacement = descriptions[replacement_index]
            replacement_index += 1
            return f"<image>{original_image}</image> {replacement}"
        return match.group(0)  # If no more replacements, return the original match

    if text is None:
        return text
    else:
        images = get_images(text)
        if images:
            descriptions = []
            for image in images:
                descriptions.append(image_description(image))

            replacement_index = 0

            result = re.sub(r"<image>(.*?)</image>", replacer, text)
            return result
        else:
            return text
