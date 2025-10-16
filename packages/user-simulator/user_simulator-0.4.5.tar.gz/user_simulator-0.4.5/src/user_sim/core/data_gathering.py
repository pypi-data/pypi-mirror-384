import ast
import pandas as pd
from user_sim.utils.token_cost_calculator import calculate_cost, max_output_tokens_allowed, max_input_tokens_allowed
import re
from user_sim.utils.exceptions import *
from user_sim.utils.utilities import init_model
from user_sim.utils import config
from langchain_core.prompts import ChatPromptTemplate


model = " "
llm = None

import logging
logger = logging.getLogger('Info Logger')


def init_data_gathering_module() -> None:
    """
    Initialize the data gathering module by setting up the global LLM model.

    Calls `init_model()` to load the model and language model (llm)
    used for resolving dynamic values (e.g., `any()` placeholders)
    during data extraction.

    Globals:
     model: The loaded model identifier or configuration.
     llm: The initialized language model instance.
    """
    global model
    global llm
    model, llm = init_model()

def extract_dict(in_val: str) -> str | None:
    """
    Extract the first dictionary-like substring from a string.

    Looks for the first occurrence of text enclosed in curly braces `{}`.
    Useful for pulling JSON-like or dict-like snippets from raw text.

    Args:
        in_val (str): Input string to search.

    Returns:
        str | None: The matched substring including braces,
        or None if no match is found.
    """
    reg_ex = r'\{[^{}]*\}'
    coincidence = re.search(reg_ex, in_val, re.DOTALL)

    if coincidence:
        return coincidence.group(0)
    else:
        return None


def to_dict(in_val: str) -> dict:
    """
    Safely extract and evaluate a dictionary from a string.

    Uses `extract_dict()` to locate the first dictionary-like substring
    and converts it into a Python dictionary with `ast.literal_eval`.
    If parsing fails, returns an empty dictionary.

    Args:
        in_val (str): Input string containing a dictionary-like structure.

    Returns:
        dict: Parsed dictionary if successful, otherwise an empty dict.

    Raises:
        Logs an error and falls back to `{}` if:
            - The extracted substring is invalid.
            - The format cannot be parsed into a dictionary.
    """
    try:
        dictionary = ast.literal_eval(extract_dict(in_val))
    except (BadDictionaryGeneration, ValueError) as e:
        logger.error(f"Bad dictionary generation: {e}. Setting empty dictionary value.")
        dictionary = {}
    return dictionary


class ChatbotAssistant:
    """
    A helper class for extracting structured information from chatbot
    conversations.

    The assistant checks whether specific user goals ("ask_about")
    were answered, confirmed, or provided by the chatbot, and stores
    the results in structured JSON and tabular formats.

    Attributes:
        verification_description (str): Description used for boolean checks.
        data_description (str): Description used for locating conversation snippets.
        properties (dict): JSON schema built from ask_about items.
        system_message (str): Instruction message for the LLM.
        messages (str): Formatted conversation history.
        gathering_register (pd.DataFrame): Extracted results as a dataframe.
    """
    def __init__(self, ask_about: list[str]) -> None:
        """
        Initialize the assistant with a list of goals.

        Args:
            ask_about (list[str]): Goals or items to check in the conversation.
        """
        self.verification_description = "the following has been answered, confirmed or provided by the chatbot:"
        self.data_description = """"the piece of the conversation where the following has been answered 
                                or confirmed by the assistant. Don't consider the user's interactions:"""
        self.properties = self.process_ask_about(ask_about)
        self.system_message = """You are a helpful assistant that detects when a query in a conversation
                                has been answered, confirmed or provided by the chatbot."""
        self.messages = ""
        self.gathering_register = {}


    def process_ask_about(self, ask_about: list[str]) -> dict:
        """
        Build JSON schema properties from the ask_about list.

        Each entry generates a schema with `verification` (bool)
        and `data` (string/null).

        Args:
            ask_about (list[str]): Goals to process.

        Returns:
            dict: JSON schema properties for structured output.
        """
        properties = {
        }
        for ab in ask_about:
            properties[ab.replace(' ', '_')] = {
                "type": "object",
                "properties": {
                    "verification": {
                        "type": "boolean",
                        "description": f"{self.verification_description} {ab}"
                    },
                    "data": {
                        "type": ["string", "null"],
                        "description": f"{self.data_description} {ab} "
                    }
                },
                "required": ["verification", "data"],
                "additionalProperties": False
            }
        return properties


    def add_message(self, history: dict) -> None:
        """
        Append chat history and update the gathering register.

        Adds directly the chat history from user_simulator "self.conversation_history".

        Args:
            history (dict): A conversation history containing
                'interaction' entries with speaker-message pairs.
        """
        text = ""
        for entry in history['interaction']:
            for speaker, message in entry.items():
                text += f"{speaker}: {message}\n"

        self.messages = text
        self.gathering_register = self.create_dataframe()


    def get_json(self) -> dict | str | None:
        """
        Query the LLM to extract structured goal-related data.

        Returns:
            dict | str | None: Extracted structured data if successful,
            None if token limits are exceeded or errors occur,
            str if data gathering module not initialized.
        """
        response_format = {
                "title": "data_gathering",
                "type": "object",
                "description": "The information to check.",
                "properties": self.properties,
                "required": list(self.properties.keys()),
                "additionalProperties": False
        }

        parsed_input_message = self.messages + self.verification_description + self.data_description

        if llm is None:
            logger.error("data gathering module not initialized.")
            return "Empty data"

        if max_input_tokens_allowed(parsed_input_message, model):
            logger.error(f"Token limit was surpassed")
            return None

        if config.token_count_enabled:
            llm.max_tokens = max_output_tokens_allowed(model)

        prompt = ChatPromptTemplate.from_messages([("system", self.system_message), ("human", "{input}")])
        structured_llm = llm.with_structured_output(response_format)
        prompted_structured_llm = prompt | structured_llm

        try:
            response = prompted_structured_llm.invoke({"input": self.messages})
            parsed_output_message = str(response)

        except Exception as e:
            logger.error(f"Truncated data in message: {e}")
            response = parsed_output_message = None
        if config.token_count_enabled:
            calculate_cost(parsed_input_message, parsed_output_message, model=config.model, module="data_extraction")
        return response


    def create_dataframe(self) -> pd.DataFrame:
        """
        Convert the structured extraction into a pandas DataFrame.

        Returns:
            pd.DataFrame: Dataframe of extracted information,
            or the previous register if parsing fails.
        """
        data_dict = self.get_json()
        if data_dict is None:
            df = self.gathering_register
        else:
            try:
                df = pd.DataFrame.from_dict(data_dict, orient='index')
            except Exception as e:
                logger.error(f"{e}. data_dict: {data_dict}. Retrieving data frame from gathering_register")
                df = self.gathering_register
        return df
