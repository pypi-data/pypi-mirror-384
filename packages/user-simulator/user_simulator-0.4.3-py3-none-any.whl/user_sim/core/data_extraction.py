import re
import logging
from typing import Any
from dateutil import parser
from langchain_core.prompts import ChatPromptTemplate
from user_sim.utils.token_cost_calculator import calculate_cost
from user_sim.utils import config
from user_sim.utils.utilities import init_model
from datetime import date


model = ""
llm = None
logger = logging.getLogger('Info Logger')


def init_data_extraction_module() -> None:
    """
    Initialize the data extraction module by setting up the global LLM model.

    Calls `init_model()` to load the model and language model (llm) that are
    used for extracting structured information from chatbot conversations.

    Globals:
        model: The loaded model identifier or configuration.
        llm: The initialized language model instance.
    """
    global model
    global llm
    model, llm = init_model()


class DataExtraction:
    """
    Extract structured data from chatbot conversations using LLMs.

    Given a conversation, a target variable, and its expected type,
    this class builds prompts for the LLM, runs static/dynamic extraction,
    and casts the results into the desired format.

    Attributes:
        model (str): Identifier of the LLM used for extraction.
        message (str): Conversation history in text format.
        dtype (str): Expected data type (int, float, string, etc.).
        variable (str): Name of the variable to extract.
        description (str): Text description of the variable.
        system (str): System-level instructions for the LLM.
    """
    def __init__(self, conversation, variable_name, dtype, description):
        self.model = "gpt-4o-mini"
        self.message = f"{conversation['interaction']}"
        self.dtype = dtype
        self.variable = variable_name
        self.description = description
        self.system = f"""
        You're an assistant that analyzes a conversation between a user and a chatbot.
        Your objective is to test the chatbot's capabilities by extracting the information only if the chatbot provides it 
        or verifies it. Output only the requested data, If you couldn't find it, output None.
        """


    @staticmethod
    def data_process(text: str | None, dtype: str) -> Any:
        """
        Cast extracted text into the specified data type.

        Args:
            text (str | None): Extracted value.
            dtype (str): Target type ("int", "float", "bool", etc.).

        Returns:
            Any: Converted value, or the original text if casting fails.
        """
        logger.info(f'input text on data process for casting: {text}')

        if text is None or text == 'null':
            return text
        try:
            if dtype == 'int':
                return int(text)
            elif dtype == 'float':
                return float(text)
            elif dtype == 'money':
                return text
            elif dtype == 'str':
                return str(text)
            elif dtype == 'bool':
                return bool(text)
            elif dtype == 'time':
                # time = parser.parse(text).time().strftime("%H:%M:%S")
                time = str(text)
                return time
            elif dtype == 'date':
                # date = parser.parse(text).date()
                date = str(text)
                return date
            else:
                return text

        except ValueError as e:
            logger.warning(f"Error in casting: {e}. Returning 'str({str(text)})'.")
            return str(text)

    @staticmethod
    def get_data_prompt(dtype: str) -> tuple[str, str]:
        """
        Build data type and format instructions for the LLM.

        Args:
            dtype (str): Requested type, may include modifiers like
                "time(...)" or "date(...)".

        Returns:
            tuple[str, str]: (JSON schema type, format instructions).
        """
        time_format = "hh:mm:ss"
        date_format = "month/day/year"
        todays_date = date.today()
        if "time(" in dtype:
            match = re.findall(r'\((.*?)\)', dtype)
            if match:
                time_format = match
            dtype = "time"
        if "date(" in dtype:
            match = re.findall(r'\((.*?)\)', dtype)

            if match:
                date_format = match
            dtype = "date"

        data_type = {
            'int': 'integer',
            'float': 'number',
            'string': 'string',
            'time': 'string',
            'bool': 'boolean',
            'date': 'string',
            'list': 'array'
        }

        data_format = {
            'int': '',
            'float': '',
            'string': "Extract and  display concisely only the requested information "
                  "without including additional context",
            'time': f'Output just the time data (not date) following strictly this format: {time_format}',
            'bool': '',
            'list': 'Output only the content to list.',
            'date': f'''
                Output just the date data (not time) following strictly this format: {date_format}.
                If you're getting a relative date, for example, "tomorrow", "yesterday", "in two days", 
                keep in mind that today is {todays_date}.
                '''
        }

        prompt_type = data_type.get(dtype)
        d_format = data_format.get(dtype)
        return prompt_type, d_format


    def static_extraction(self, dtype: str, dformat: str, list_dtype: str | None) -> Any:
        """
        Perform static extraction with a fixed response schema.

        Args:
            dtype (str): Target type for output.
            dformat (str): Additional format instructions.
            list_dtype (str | None): Item type if dtype is "array".

        Returns:
            Any: LLM-extracted value(s).
        """
        parsed_input_message = self.system + self.message


        description = f"{self.description}. {dformat}"

        prompt = ChatPromptTemplate.from_messages([("system", self.system + description), ("human", "{input}")])


        if dtype == "array":
            answer = {
                "type": [dtype, 'null'],
                "items": {
                    "type": list_dtype
                }
            }
        else:
            answer = {
                "type": [dtype, 'null'],
            }


        response_format =  {
                    "title": "Data_extraction",
                    "description": description,
                    "type": "object",
                    "properties": {
                        "answer": answer
                    },
                    "required": ['answer'],
                    "additionalProperties": False,
                }


        structured_llm = llm.with_structured_output(response_format)
        prompted_structured_llm = prompt | structured_llm
        response = prompted_structured_llm.invoke({"input": self.message})

        output_message = response["answer"]
        if config.token_count_enabled:
            calculate_cost(parsed_input_message, output_message, model=self.model, module="data_extraction")

        return output_message

    def dynamic_extraction(self, extraction: dict, llm_output: Any) -> Any:
        """
        Perform dynamic extraction based on a custom type definition.

        Args:
            extraction (dict): Schema with expected fields and types.
            llm_output (Any): Output of static extraction for context.

        Returns:
            dict: Field-value pairs extracted by the LLM.
        """
        extraction_keys = list(extraction.keys())
        field_definitions = {key: ([self.get_data_prompt(extraction[key]["type"])[0], "null"], extraction[key]["description"]) for key in extraction_keys}

        if llm_output is None:
            logger.warning("Couldn't get an answer from static extraction.")
            llm_output = "none"

        message = llm_output

        parsed_input_message = self.system + message
        properties = {}
        required = []

        for field_name, (field_type, field_description) in field_definitions.items():
            properties[field_name] = {
                "type": field_type,
                "description": field_description
            }
            required.append(field_name)

        response_format = {
            "title": "data_extraction",
            "description": "The data you want to extract",
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        }

        prompt = ChatPromptTemplate.from_messages([("system", self.system), ("human", "{input}")])


        structured_llm = llm.with_structured_output(response_format)
        prompted_structured_llm = prompt | structured_llm
        response = prompted_structured_llm.invoke({"input": message})


        llm_output = response
        parsed_output_message = str(response)
        if config.token_count_enabled:
            calculate_cost(parsed_input_message, parsed_output_message, model=self.model, module="data_extraction")

        return llm_output


    def get_data_extraction(self) -> dict:
        """
        Orchestrate the full data extraction pipeline.

        - Resolves custom types from config.
        - Handles predefined and list-based types.
        - Runs static/dynamic extraction and casts the result.

        Returns:
            dict: Mapping of variable name to extracted value(s).
        """
        custom_types_names = list(config.types_dict.keys())
        if llm is None:
            logger.error("data extraction module not initialized.")
            return {"output": None}

        list_dtype = None
        # If data type is custom
        if self.dtype in custom_types_names:
            type_yaml = config.types_dict.get(self.dtype, "string")
            dformat = f"Data should be strictly outputted following regular expression pattern: {type_yaml['format']}"
            if isinstance(type_yaml["extraction"], dict):
                dtype = self.get_data_prompt("string")
                static_output = self.static_extraction(dtype[0], dformat, list_dtype)
                llm_output = self.dynamic_extraction(type_yaml["extraction"], static_output)
                return {self.variable: llm_output}
            else:
                dtype = self.get_data_prompt(type_yaml["extraction"])
                llm_output = self.static_extraction(dtype[0], dformat, list_dtype)
                logger.info(f'LLM output for data extraction: {llm_output}')
                return {self.variable: llm_output}

        # If data type is predefined
        else:

            if "list" in self.dtype:
                pattern = r'(\w+)\[(.*?)\]'
                match = re.match(pattern, self.dtype)
                if match:
                    list_name = match.group(1)
                    content = match.group(2)
                    dtype = self.get_data_prompt(list_name)[0]
                    list_dtype = self.get_data_prompt(content)[0]
                    dformat = self.get_data_prompt(list_name)[1]
                else:
                    logger.error("Invalid structure on list for output data. Using 'string' by default.")
                    dtype = self.get_data_prompt('string')[0]
                    dformat = self.get_data_prompt('string')[1]

            else:
                dtype, dformat = self.get_data_prompt(self.dtype)

            if dtype is None:
                logger.warning(f"Data type {self.dtype} is not supported. Using 'string' by default.")
                dtype = 'string'

            if dformat is None:
                logger.warning(f"Data format for {self.dtype} is not supported. Using default format.")
                dformat = "Extract and display concisely only the requested information without including additional context"



            llm_output = self.static_extraction(dtype, dformat, list_dtype)

            logger.info(f'LLM output for data extraction: {llm_output}')
            # text = llm_output['answer']
            data = self.data_process(llm_output, self.dtype)
            return {self.variable: data}
