import itertools
from pydantic import BaseModel, ValidationError, field_validator
from typing import List, Union, Dict, Optional
from importlib.resources import files
from user_sim.core.interaction_styles import *
from user_sim.core.ask_about import *
from user_sim.utils.exceptions import *
from user_sim.utils.languages import languages
from user_sim.utils import config
from dataclasses import dataclass
from user_sim.handlers.image_recognition_module import init_vision_module
from user_sim.core.data_gathering import init_data_gathering_module
from user_sim.core.data_extraction import init_data_extraction_module
import logging
logger = logging.getLogger('Info Logger')


def replace_placeholders(phrase: str, variables: dict | list) -> str:
    """
    Replace placeholders of the form {{variable}} in a phrase with values.

    Args:
        phrase (str): The input string containing placeholders like {{var}}.
        variables (dict | list):
            - If dict, keys correspond to placeholder names and values are lists of replacements.
            - If list, all placeholders will be replaced with this list of values.

    Returns:
        str: The phrase with placeholders replaced by corresponding values.
    """
    def replacer(match) -> str:
        key = match.group(1)
        if isinstance(variables, dict):
            return ', '.join(map(str, variables.get(key, [])))
        else:
            return ', '.join(map(str, variables))

    pattern = re.compile(r'\{\{(\w+)\}\}')
    return pattern.sub(replacer, phrase)


def list_to_str(list_of_strings):
    if list_of_strings is None:
        return ''
    try:
        single_string = ' '.join(list_of_strings)
        return single_string
    except Exception as e:
        # logging.getLogger().verbose(f'Error: {e}')
        return ''


class ConvFormat(BaseModel):
    type: Optional[str] = "text"
    config: Optional[str] = None


class LLM(BaseModel):
    model: Optional[str] = "gpt-4o"
    model_prov: Optional[str] = None
    temperature: Optional[float] = 0.8
    format: Optional[ConvFormat] = ConvFormat()  # text, speech, hybrid


class User(BaseModel):
    language: Optional[Union[str, None]] = 'English'
    role: str
    context: Optional[Union[List[Union[str, Dict]], Dict, None]] = ''
    goals: list


class ChatbotClass(BaseModel):
    is_starter: Optional[bool] = True
    fallback: str
    output: list


class Conversation(BaseModel):
    number: Union[int, str]
    max_cost: Optional[float]=10**9
    goal_style: Dict
    interaction_style: list


class RoleDataModel(BaseModel):
    test_name: str
    llm: Optional[LLM] = LLM()
    user: User
    chatbot: ChatbotClass
    conversation: Conversation


@dataclass
class ValidationIssue:
    field: str
    error: str
    error_type: str
    location: str


class RoleData:
    """
    Parse, validate, and manage data for a user role profile.

    This class loads a role definition from a YAML structure and
    initializes components required for conversation simulation,
    including the LLM, user attributes, chatbot settings, conversation
    parameters, and interaction styles. It also provides methods for
    validation, error collection, and resetting attributes between
    conversations.

    Attributes:
        yaml (dict): Parsed YAML profile data.
        validation (bool): Flag indicating if the instance is in validation mode.
        personality_file (str | None): Optional path to a personality YAML file.
        project_folder (str | None): Path to the project folder.
        errors (list[ValidationIssue]): Collected validation issues.

        test_name (str | None): Name of the test from the profile.
        llm (LLM | None): LLM configuration object.
        model (str | None): Name of the LLM model.
        model_provider (str | None): Provider of the LLM.
        temperature (float | None): Sampling temperature for the LLM.
        format_type (str | None): Conversation format type (e.g., text, speech).
        format_config (dict | None): Additional format configuration.

        user (User | None): User configuration object.
        language (str | None): Language for the conversation.
        role (str | None): Role of the user.
        raw_context (Any): Original context data from YAML.
        context (str | None): Processed context string.
        ask_about (AskAboutClass | None): Object defining what the user should be asked about.

        chatbot (ChatbotClass | None): Chatbot configuration object.
        is_starter (bool | None): Whether the chatbot starts the conversation.
        fallback (str | None): Fallback response for the chatbot.
        output (Any | None): Expected output configuration.

        conversation (Conversation | None): Conversation configuration object.
        conversation_number (int | None): Number of conversations to simulate.
        max_cost (float | None): Maximum cost allowed for the conversation.
        goal_style (Any | None): Conversation goals (steps, limits, etc.).
        interaction_styles (list | None): List of interaction style objects.
        combinations_dict (dict): Data about generated conversation combinations.
    """

    def __init__(
            self,
            yaml_file: dict,
            project_folder: str | None = None,
            personality_file: str | None = None,
            validation: bool = False
    ) -> None:
        """
        Initialize a RoleData instance from a YAML profile.

        Args:
            yaml_file (dict): Parsed YAML profile data describing test
                name, LLM configuration, user settings, chatbot settings,
                and conversation parameters.
            project_folder (str | None, optional): Path to the project folder.
                Used for locating resources like profiles, personalities,
                and types. Defaults to None.
            personality_file (str | None, optional): Path to a YAML file
                defining a custom personality context. If provided, it is
                merged into the profile's context. Defaults to None.
            validation (bool, optional): If True, enables validation mode
                (errors are collected instead of raising exceptions).
                Defaults to False.

        Side Effects:
            - Initializes LLM, user, chatbot, and conversation attributes.
            - Collects errors into `self.errors` if invalid configuration
              values are found.
            - Calls `init_llm_modules()` unless validation errors occurred.

        Raises:
            ValidationError: If critical issues are found and not in
                validation mode.
        """
        self.yaml = yaml_file
        self.validation = validation
        self.personality_file = personality_file
        self.project_folder = project_folder
        self.errors: List[ValidationIssue] = []


    # Test Name
        try:
            self.test_name = self.yaml.get('test_name')
        except (Exception, ValidationError) as e:
            self.collect_errors(e, prefix='llm')

    # LLM
        self.model = self.model_provider = self.temperature = self.format_type = self.format_config = None
        try:
            self.llm = LLM(**self.yaml.get('llm', {}))
            self.model = config.model = self.llm.model
            self.model_provider = config.model_provider = self.llm.model_prov
            self.temperature = self.llm.temperature
            self.format_type = self.llm.format.type
            self.format_config = self.llm.format.config
        except Exception as e:
            self.collect_errors(e, prefix='llm')

        if not self.errors:
            self.init_llm_modules()

    # User
        self.language = self.role = self.raw_context = self.context = self.ask_about = None
        try:
            self.user = User(**self.yaml.get('user', {}))
            self.language = self.set_language(self.user.language)
            self.role = self.user.role
            self.raw_context = self.user.context
            self.context = self.context_processor(self.raw_context)
            self.ask_about = self.get_ask_about()
        except Exception as e:
            self.collect_errors(e, prefix='user')

    # Chatbot
        self.is_starter = self.fallback = self.output = None
        try:
            self.chatbot = ChatbotClass(**self.yaml.get('chatbot', {}))
            self.is_starter = self.chatbot.is_starter
            self.fallback = self.chatbot.fallback
            self.output = self.chatbot.output
        except Exception as e:
            self.collect_errors(e, prefix='chatbot')

    # Conversation
        self.conversation_number = self.max_cost = self.goal_style = self.interaction_styles = None
        try:
            self.conversation = Conversation(**self.yaml.get('conversation', {}))
            self.combinations_dict = {}
            self.conversation_number = self.get_conversation_number(self.conversation.number)
            self.max_cost = self.conversation.max_cost
            config.limit_cost = self.max_cost
            self.goal_style = self.pick_goal_style(self.conversation.goal_style)
            self.interaction_styles = self.pick_interaction_style(self.conversation.interaction_style)
        except Exception as e:
            self.collect_errors(e, prefix='conversation')


    @staticmethod
    def init_llm_modules():
        """
        Initialize all required LLM-related modules.

        This method sets up supporting modules needed for conversation
        simulation and data processing, such as vision, data gathering,
        data extraction, and list handling.

        Side Effects:
            - Calls initialization routines for:
                - `init_vision_module()`
                - `init_data_gathering_module()`
                - `init_data_extraction_module()`
                - `init_any_list_module()`
            - Prepares modules for use in later conversation flows.

        Notes:
            - `init_asr_module()` is available but currently disabled.
        """
        init_vision_module()
        init_data_gathering_module()
        init_data_extraction_module()
        init_any_list_module()
        # init_asr_module()


    def collect_errors(self, e: ValidationError, prefix: str = "") -> None:
        """
        Collect and record a validation error.

        Converts a `ValidationError` or generic exception into one or more
        `ValidationIssue` entries and appends them to `self.errors`.

        Args:
            e (ValidationError | Exception): The error to collect.
                - If `ValidationError`, iterates through its `.errors()` and
                  records each individual issue with detailed location info.
                - Otherwise, wraps the exception as a generic error entry.
            prefix (str, optional): Context prefix (e.g., "llm", "user",
                "chatbot") to help locate the source of the error.
                Defaults to "".

        Side Effects:
            - Appends one or more `ValidationIssue` objects to `self.errors`.
        """
        if isinstance(e, ValidationError):
            for err in e.errors():
                loc_path = '.'.join(str(part) for part in err['loc'])
                full_path = f"{prefix}.{loc_path}" if prefix else loc_path
                self.errors.append(
                    ValidationIssue(
                        field=err['loc'][-1],
                        error=err['msg'],
                        error_type=err['type'],
                        location=full_path
                    )
                )
        else:
            self.errors.append(
                ValidationIssue(
                    field='unknown',
                    error=str(e),
                    error_type=type(e).__name__,
                    location=prefix
                )
            )


    def get_errors(self) -> [list[dict], int]:
        """
        Retrieve and summarize collected validation errors.

        Iterates over `self.errors` and returns a list of formatted error
        dictionaries along with the total error count.

        Returns:
            tuple[list[dict], int]:
                - A list of dictionaries, each containing:
                    - `"field"` (str): Location of the error within the profile.
                    - `"error"` (str): Error message.
                    - `"type"` (str): Error type.
                - The total number of errors (int).

        Side Effects:
            - Logs a warning with the number of detected errors.
        """
        error_list = []
        for error in self.errors:
            formated_error = {
                "field": error.location,
                "error": error.error,
                "type": error.error_type
            }
            error_list.append(formated_error)
        logger.warning(f"\n{len(self.errors)} errors detected.\n")

        return error_list, len(self.errors)


    def get_ask_about(self):
        """
        Initialize the AskAbout handler for the user profile.

        Creates an instance of `AskAboutClass` based on the user's goals.
        In validation mode, exceptions are caught and recorded as
        `ValidationIssue`s instead of being raised.

        Returns:
            AskAboutClass | None: An initialized `AskAboutClass` object if
            successful, otherwise `None` when in validation mode and an
            error occurs.

        Side Effects:
            - If `self.validation` is True and initialization fails,
              appends a `ValidationIssue` to `self.errors`.
        """
        if self.validation:
            try:
                return AskAboutClass(self.user.goals)
            except Exception as e:
                issue = ValidationIssue(
                    field="goals",
                    error=str(e),
                    error_type=type(e).__name__,
                    location="user.goals"
                )
                self.errors.append(issue)
        else:
            return AskAboutClass(self.user.goals)



    def set_language(self, lang: str | None) -> str:
        """
        Validate and set the conversation language.

        If the provided language is valid (exists in the `languages` list),
        it is returned and logged. Otherwise, the language defaults to
        `"English"` and an error is recorded.

        Args:
            lang (str | None): Desired language string, or None.

        Returns:
            str: The validated language. Defaults to `"English"` if the
            input is None or invalid.

        Side Effects:
            - Logs the language decision (valid or fallback).
            - Appends a `ValidationIssue` to `self.errors` if the input
              language is invalid.
        """
        if isinstance(lang, type(None)):
            logger.info("Language parameter empty. Setting language to Default (English)")
            return "English"
        try:
            if lang in languages:
                logger.info(f"Language set to {lang}")
                return lang
            else:
                raise InvalidLanguageException(f'Invalid language input: {lang}. Setting language to default (English)')
        except InvalidLanguageException as e:
            issue = ValidationIssue(
                field= "language",
                error=str(e),
                error_type=type(e).__name__,
                location="user.language"
            )
            self.errors.append(issue)
            return "English"


    def reset_attributes(self) -> None:
        """
        Reset role attributes for the next conversation.

        Reinitializes LLM modules and restores key attributes such as
        fallback responses, context, goals, language, and interaction styles.
        This ensures that each new conversation starts with a fresh and
        consistent state.

        Returns:
            None

        Side Effects:
            - Calls `init_llm_modules()` to reinitialize dependent modules.
            - Resets `ask_about` (clearing picked elements and phrases).
            - Updates attributes:
                - `fallback`
                - `context`
                - `goal_style`
                - `language`
                - `interaction_styles`
        """
        logger.info(f"Preparing attributes for next conversation...")
        self.init_llm_modules()
        self.fallback = self.chatbot.fallback
        # self.is_starter = self.validated_data.is_starter
        self.context = self.context_processor(self.raw_context)
        self.ask_about.reset()  # self.picked_elements = [], self.phrases = []

        self.goal_style = self.pick_goal_style(self.conversation.goal_style)
        self.language = self.set_language(self.user.language)
        self.interaction_styles = self.pick_interaction_style(self.conversation.interaction_style)


    def personality_extraction(self, context: dict) -> list[str]:
        """
        Extract personality context phrases from a profile.

        Given a context dictionary containing a `"personality"` key,
        this method searches for a matching personality YAML file in
        both custom and default personality paths. If found, it loads
        the personality data and returns its `"context"` content.

        Args:
            context (dict): A dictionary expected to contain a `"personality"`
                key with the name of the desired personality file.

        Returns:
            list[str]: A list of context phrases associated with the
            specified personality. Returns `['']` if the personality
            file cannot be found, parsed, or does not contain the
            required `"context"` key.

        Side Effects:
            - Updates `self.personality` with the personality name
              if successfully loaded.
            - Logs status, errors, or missing file information.
            - Appends no errors to `self.errors` directly, but may
              raise `InvalidFormat` for malformed personality files.

        Raises:
            InvalidFormat: If the personality file does not contain a
            `"context"` key.

        Notes:
            - Search order:
                1. Custom personalities (`config.custom_personalities_path`)
                2. Default personalities (`config/personalities`)
            - Personality files must be in `.yml` or `.yaml` format.
        """
        if context["personality"]:
            personality = context["personality"]

            path_list = []
            if os.path.exists(config.custom_personalities_path):
                custom_personalities_path = config.custom_personalities_path
                path_list.append(custom_personalities_path)

            default_personalities_path = files("config") / "personalities"
            path_list.append(default_personalities_path)

            try:
                for path in path_list:
                    for file in os.listdir(path):
                        file_name, ext = os.path.splitext(file)
                        clean_personality, _ = os.path.splitext(personality)
                        if file_name == clean_personality and ext in ('.yml', '.yaml'):
                            personality_path = os.path.join(path, file)
                            personality_data = read_yaml(personality_path)

                            try:
                                self.personality = personality_data["name"]
                                logger.info(f"Personality set to '{file_name}'")
                                return personality_data['context']
                            except KeyError:
                                raise InvalidFormat(f"Key 'context' not found in personality file.")

                logger.error(f"Couldn't find specified personality file: '{personality}'")
                return ['']

            except Exception as e:
                logger.error(e)
                return ['']

        else:
            logger.error(f"Data for context is not a dictionary with context key: {context}.")
            return ['']


    def get_conversation_number(self, conversation: int | str) -> int:
        """
        Determine the number of conversations to generate.

        This method supports both explicit integers and string patterns
        describing combination-based generation strategies. When in
        validation mode, it also builds `self.combinations_dict` from
        the variable generators in `self.ask_about`.

        Args:
            conversation (int | str): Conversation count or a string
                pattern describing combinations. Supported string formats:
                - "combinations"
                - "combinations(forward)"
                - "combinations(pairwise)"
                - "combinations(<sample>, forward)"
                - "combinations(<sample>, pairwise)"

        Returns:
            int: The resolved number of conversations to generate.
            Returns 0 if no valid number can be determined.

        Side Effects:
            - Updates `self.combinations_dict` in validation mode with
              details about generated matrices (forward/pairwise).
            - Logs info and error messages about generation decisions.
            - Appends a `ValidationIssue` to `self.errors` if the value
              is invalid or unrecognized.

        Notes:
            - `<sample>` can be a float multiplier applied to the base
              number of combinations.
            - If no valid combinations can be generated, returns 0.
        """
        if isinstance(conversation, int):
            logger.info(f"{conversation} conversations will be generated")
            return conversation

        comb_pattern = r'^combinations(?:\(([^,()\s]+)(?:,\s*([^()]+))?\))?$'
        match = re.match(comb_pattern, conversation.strip())

        if self.validation:
            generators_list = self.ask_about.var_generators
            combinations_dict = []

            for generator in generators_list:
                if "matrix" in generator:
                    name = generator['name']
                    combination_matrix = []
                    combinations = 0
                    if generator['type'] == 'forward':
                        combination_matrix = [list(p) for p in itertools.product(*generator['matrix'])]
                        combinations = len(combination_matrix)
                    elif generator['type'] == 'pairwise':
                        combination_matrix = generator['matrix']
                        combinations = len(combination_matrix)

                    combinations_dict.append({'name':name,
                                 'matrix':combination_matrix,
                                 'combinations':combinations,
                                 'type': generator['type']})

            self.combinations_dict = combinations_dict

        if match:
            # func_name = "combinations"
            sample = match.group(1)
            iter_function = match.group(2)

            if iter_function == "forward":
                if self.ask_about.forward_combinations <= 0:
                    logger.error("Conversation number set to 'forward_all_combinations' but no combinations can be made.")
                    return 0
                conv_number = self.ask_about.forward_combinations

                if sample:
                    conv_number = round(conv_number * float(sample))
                logger.info(f"{conv_number} conversations will be generated.")
                return conv_number

            elif iter_function == "pairwise":
                if self.ask_about.pairwise_combinations <= 0:
                    logger.error("Conversation number set to 'pairwise_all_combinations' but no combinations can be made.")
                    return 0

                conv_number = self.ask_about.pairwise_combinations
                if sample:
                    conv_number = round(conv_number * float(sample))
                logger.info(f"{conv_number} conversations will be generated.")
                return conv_number

            else:
                conv_number = max(self.ask_about.forward_combinations, self.ask_about.pairwise_combinations)
                if conv_number < 1:
                    logger.error("Conversation number set to 'combinations' but no combinations can be made.")
                    return 0
                if sample:
                    conv_number = round(conv_number * float(sample))
                logger.info(f"{conv_number} conversations will be generated.")
                return conv_number

        else:
            logger.error(f"Conversation number can't be obtained due tu unrecognized value: {conversation}")
            issue = ValidationIssue(
                field= "language",
                error=f"Conversation number can't be obtained due tu unrecognized value: {conversation}",
                error_type=type(InvalidFormat).__name__,
                location="conversation.number"
            )
            self.errors.append(issue)
            return 0


    def context_processor(self, context: dict | list[str | dict]) -> str:
        """
        Process and normalize the conversation context.

        Depending on the input type, this method extracts personality
        phrases, merges them with custom context phrases, and converts
        everything into a single string representation.

        Args:
            context (dict | list[str | dict]): The raw context data from
                the user profile. It may be:
                - A dict containing a personality reference.
                - A list of strings (phrases).
                - A list mixing strings and personality dicts.

        Returns:
            str: A string representation of the processed context.
            Returns an empty string ("") if invalid or conflicting data
            is found.

        Side Effects:
            - Calls `personality_extraction()` when context includes
              personality references.
            - Reads from `self.personality_file` if provided and no
              personality is found in context.
            - Appends `ValidationIssue` objects to `self.errors` if:
                - Too many personality dicts are present.
                - Invalid data types appear in the context list.

        Notes:
            - When both personality and custom context phrases are
              present, they are concatenated.
            - If no personality is defined in the context but a
              `personality_file` was provided, that file is used.
        """
        if isinstance(context, dict):
            personality_phrases = self.personality_extraction(context)
            return list_to_str(personality_phrases)

        res = len(list(filter(lambda x: isinstance(x, dict), context)))
        if res > 1:
            # raise InvalidFormat(f)
            issue = ValidationIssue(
                field="context",
                error=str("Too many keys in context list."),
                error_type=type(InvalidFormat).__name__,
                location="user.context"
            )
            self.errors.append(issue)
            return ""
        elif res <= 0 and not isinstance(context, dict):
            phrases = list_to_str(context)
            if self.personality_file is not None:
                personality = read_yaml(self.personality_file)
                personality_phrases = personality['context']
                phrases = phrases + list_to_str(personality_phrases)
            return phrases
        else:
            custom_phrases = []
            personality_phrases = []
            for item in context:
                if isinstance(item, str):
                    custom_phrases.append(item)
                elif isinstance(item, dict):
                    personality_phrases = personality_phrases + self.personality_extraction(item)
                else:
                    issue = ValidationIssue(
                        field="context",
                        error=str(f"Invalid data type in context list: {type(item)}:{item}"),
                        error_type=type(InvalidDataType).__name__,
                        location="user.context"
                    )
                    self.errors.append(issue)
                    return ""

            # If no personality is given, we use the one specified as input in the command line
            if len(personality_phrases) == 0 and self.personality_file is not None:
                personality = read_yaml(self.personality_file)
                personality_phrases = personality['context']

            total_phrases = personality_phrases + custom_phrases
            return list_to_str(total_phrases)


    def pick_goal_style(self, goal: dict | None) -> tuple | list | str:
        """
        Parse and validate the conversation goal style.

        Determines the conversation goal based on cost, steps, or other
        goal-style configurations defined in the profile. Returns a
        structured goal representation or records errors in validation mode.

        Args:
            goal (dict | None): Goal configuration from the profile. Supported keys:
                - "max_cost": Maximum allowed cost for a conversation.
                - "steps": Fixed number of conversation steps (must be <= 20).
                - "all_answered" or "default": Dict with optional "export" (bool)
                  and "limit" (int, default=30).
                - "random steps": Upper bound for random step selection (< 20).

        Returns:
            tuple | list | str:
                - `(None, False)` if `goal` is None.
                - `(key, steps)` for step-based goals.
                - `[key, export, limit]` for "all_answered"/"default".
                - `(key, random_steps)` for "random steps".
                - `""` (empty string) if validation mode detects an error.

        Side Effects:
            - Updates `config.limit_individual_cost` and `config.token_count_enabled`
              when "max_cost" is provided.
            - Appends `ValidationIssue` entries to `self.errors` if validation fails.
            - Raises exceptions if not in validation mode and invalid values are found:
                - `NoCostException` if cost <= 0.
                - `OutOfLimitException` if steps > 20 or < 0.
                - `InvalidGoalException` for unsupported goal formats.

        Raises:
            NoCostException: If "max_cost" <= 0 (outside validation mode).
            OutOfLimitException: If steps exceed 20 or are invalid (outside validation mode).
            InvalidGoalException: If the goal structure is unrecognized (outside validation mode).
        """
        max_random_steps = 20

        if goal is None:
            return goal, False

        if 'max_cost' in goal:
            if goal['max_cost'] > 0:
                config.limit_individual_cost = goal['max_cost']
                config.token_count_enabled = True
            else:
                if self.validation:
                    issue = ValidationIssue(
                        field="goal_style",
                        error=str(f"Goal cost can't be lower than or equal to 0: {goal['cost']}"),
                        error_type=type(NoCostException).__name__,
                        location="conversation.goal_style"
                    )
                    self.errors.append(issue)
                    return ""
                else:
                    raise NoCostException(f"Goal cost can't be lower than or equal to 0: {goal['cost']}")
        else:
            config.limit_individual_cost = config.limit_cost

        if 'steps' in goal:
            if goal['steps'] <= 20 or goal['steps'] > 0:
                return list(goal.keys())[0], goal['steps']
            else:
                if self.validation:
                    issue = ValidationIssue(
                        field="goal_style",
                        error=str(f"Goal steps higher than 20 steps or lower than 0 steps: {goal['steps']}"),
                        error_type=type(OutOfLimitException).__name__,
                        location="conversation.goal_style"
                    )
                    self.errors.append(issue)
                    return ""
                else:
                    raise OutOfLimitException(f"Goal steps higher than 20 steps or lower than 0 steps: {goal['steps']}")

        elif 'all_answered' in goal or 'default' in goal:
            if isinstance(goal, dict):

                if 'export' in goal['all_answered']:
                    all_answered_goal = [list(goal.keys())[0], goal['all_answered']['export']]
                else:
                    all_answered_goal = [list(goal.keys())[0], False]

                if 'limit' in goal['all_answered']:
                    all_answered_goal.append(goal['all_answered']['limit'])
                else:
                    all_answered_goal.append(30)

                return all_answered_goal
            else:
                return [goal, False, 30]

        elif 'random steps' in goal:
            if goal['random steps'] < max_random_steps:
                return list(goal.keys())[0], random.randint(1, goal['random steps'])
            else:
                if self.validation:
                    issue = ValidationIssue(
                        field="goal_style",
                        error=str(f"Goal steps higher than 20 steps: {goal['random steps']}"),
                        error_type=type(OutOfLimitException).__name__,
                        location="conversation.goal_style"
                    )
                    self.errors.append(issue)
                    return ""
                else:
                    raise OutOfLimitException(f"Goal steps higher than 20 steps: {goal['random steps']}")

        else:
            if self.validation:
                issue = ValidationIssue(
                    field="goal_style",
                    error=str(f"Invalid goal value: {goal}"),
                    error_type=type(InvalidGoalException).__name__,
                    location="conversation.goal_style"
                )
                self.errors.append(issue)
                return ""
            else:
                raise InvalidGoalException(f"Invalid goal value: {goal}")


    def get_interaction_metadata(self) -> list[dict]:
        """
        Retrieve metadata from all interaction styles.

        Iterates over the active interaction style objects and collects
        their metadata for reporting or analysis.

        Returns:
            list[dict]: A list of metadata dictionaries, one per
            interaction style. The structure of each dictionary is
            defined by the corresponding `get_metadata()` implementation
            of the interaction style.

        Example:
            >>> role_data.get_interaction_metadata()
            [
                {"type": "long phrases", "enabled": True},
                {"type": "change language", "languages": ["English", "Spanish"]}
            ]
        """
        metadata_list = []
        for inter in self.interaction_styles:
            metadata_list.append(inter.get_metadata())

        return metadata_list


    def pick_interaction_style(self, interactions):
        """
        Select and configure interaction styles for the conversation.

        Based on the provided list of interaction style names or
        configurations, this method instantiates and returns the
        corresponding interaction style objects. Supports both fixed
        and random selection.

        Args:
            interactions (list[str | dict] | None): List of interaction
                style names (e.g., "long phrases", "single question") or
                configuration dicts. Examples:
                - None → uses "default"
                - ["long phrases", "make spelling mistakes"]
                - [{"change language": ["English", "Spanish"]}]
                - [{"random": ["long phrases", "all questions"]}]

        Returns:
            list: A list of instantiated interaction style objects
            configured according to the provided input.

        Side Effects:
            - Logs the number and type of randomly chosen styles.
            - If an invalid style is provided, logs an error and appends a
              `ValidationIssue` to `self.errors`.

        Raises:
            InvalidInteractionException: If an unknown interaction style
            is provided and not in validation mode.

        Notes:
            - `"change language"` dicts must provide a list of language
              options.
            - `"random"` dicts trigger random selection of one or more
              styles from the given list.
            - If no interactions are specified, the `"default"` style is used.
        """
        inter_styles = {
            'long phrases': LongPhrases(),
            'change your mind': ChangeYourMind(),
            'change language': ChangeLanguage(self.language),
            'make spelling mistakes': MakeSpellingMistakes(),
            'single question': SingleQuestions(),
            'all questions': AllQuestions(),
            'default': Default()
        }


        def choice_styles(interaction_styles: list[str]) -> list[str]:
            """
            Randomly select one or more interaction styles from a list.

            Args:
                interaction_styles (list[str]): Available style names.

            Returns:
                list[str]: Randomly chosen subset of style names.
            """
            count = random.randint(1, len(interaction_styles))
            random_list = random.sample(interaction_styles, count)
            # logging.getLogger().verbose(f'interaction style amount: {count} style(s): {random_list}')
            logger.info(f'interaction style count: {count}; style(s): {random_list}')
            return random_list


        def get_styles(interact: list[str | dict]) -> list:
            """
            Instantiate interaction style objects from names or configs.

            Args:
                interact (list[str | dict]): Style names or configuration dicts.

            Returns:
                list: Instantiated and configured interaction style objects.
            """
            interactions_list = []
            try:
                for inter in interact:

                    if isinstance(inter, dict):
                        keys = list(inter.keys())
                        if keys[0] == "change language":
                            cl_interaction = inter_styles[keys[0]]
                            cl_interaction.languages_options = inter.get(keys[0]).copy()
                            cl_interaction.change_language_flag = True
                            interactions_list.append(cl_interaction)

                    else:
                        if inter in inter_styles:
                            interaction = inter_styles[inter]
                            interactions_list.append(interaction)
                        else:

                                raise InvalidInteractionException(f"Invalid interaction: {inter}")
            except InvalidInteractionException as e:
                issue = ValidationIssue(
                    field="interaction_style",
                    error=str(e),
                    error_type=type(e).__name__,
                    location="conversation.interaction_style"
                )
                self.errors.append(issue)
                logger.error(f"Error: {e}")

            return interactions_list

        # interactions_list = []
        if interactions is None:
            interaction_def = inter_styles['default']
            return [interaction_def]

        elif isinstance(interactions[0], dict) and 'random' in list(interactions[0].keys()):
            # todo: add validation funct to admit random only if it's alone in the list
            inter_rand = interactions[0]['random']
            choice = choice_styles(inter_rand)
            return get_styles(choice)

        else:
            return get_styles(interactions)


    def get_language(self) -> str:
        """
        Get the current language instruction for the user.

        If an interaction style with `change_language_flag` is active,
        returns its prompt. Otherwise, returns a default instruction
        to use the profile's configured language.

        Returns:
            str: Language prompt or default instruction.
        """
        for instance in self.interaction_styles:
            if instance.change_language_flag:
                prompt = instance.get_prompt()
                return prompt

        return f"Please, talk in {self.language}"
