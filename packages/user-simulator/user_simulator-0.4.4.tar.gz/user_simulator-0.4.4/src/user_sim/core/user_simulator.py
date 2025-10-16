from typing import Any
from user_sim.core.data_extraction import DataExtraction
from user_sim.utils.utilities import *
from user_sim.core.data_gathering import *
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model
from user_sim.utils.token_cost_calculator import calculate_cost, max_input_tokens_allowed, max_output_tokens_allowed
from user_sim.utils import config
from user_sim.utils.nlp import nlp_processor
from user_sim.core.role_structure import RoleData
import logging

parser = StrOutputParser()
logger = logging.getLogger('Info Logger')


class UserChain:
    """
    Generates user responses in the simulation using an LLM.

    The UserChain builds prompts based on the user's role, conversation
    history, and contextual reminders. It interfaces with the chosen
    LLM provider to simulate realistic user behavior.

    Attributes:
        user_role (str): Role/persona of the simulated user.
        user_llm: LLM client instance for user response generation.
        model (str): Model name (e.g., gpt-4o-mini).
        model_provider (str | None): Provider of the model, if any.
        temperature (float): Sampling temperature for creativity/randomness.
        user_context (PromptTemplate): Prompt template combining role, reminder, and history.
        chain: Composed chain of templates, LLM, and parser.
    """

    def __init__(self, user_role: str, temp: bool) -> None:
        self.user_role = user_role
        self.user_llm = None
        self.model = None
        self.model_provider = None
        self.temperature = temp
        self.init_user_module()
        self.user_context = PromptTemplate(
            input_variables=["reminder", "history"],
            template=self.set_role_template()
        )
        self.chain = None


    def init_user_module(self) -> None:
        """
        Initialize the user LLM with configured parameters.
        """
        self.model = config.model
        self.model_provider = config.model_provider

        if self.model_provider is None:
            params = {
                "model": self.model,
                "temperature": self.temperature
            }
        else:
            params = {
                "model": self.model,
                "model_provider": self.model_provider,
                "temperature": self.temperature
            }

        self.user_llm = init_chat_model(**params)


    def set_role_template(self) -> str:
        """
        Build the role-based prompt template including reminder and history.

        Returns:
            str: Formatted role prompt template.
        """
        reminder = """{reminder}"""
        history = """History of the conversation so far: {history}"""
        role_prompt = self.user_role + reminder + history
        return role_prompt


    @staticmethod
    def parse_history(conversation_history: dict) -> str:
        """
        Convert conversation history dictionary into a readable text format.

        Args:
            conversation_history (dict): Log of interactions.

        Returns:
            str: Flattened conversation text.
        """
        lines = []
        for inp in conversation_history['interaction']:
            for k, v in inp.items():
                lines.append(f"{k}: {v}")
        return "\n".join(lines)


    def text_method(self, conversation_history: dict, reminder: str) -> str:
        """
        Generate a user response given history and context reminder.

        Args:
            conversation_history (dict): Conversation so far.
            reminder (str): Contextual hints for the simulated user.

        Returns:
            str: LLM-generated user reply, or "exit" if token limit exceeded.
        """
        history = self.parse_history(conversation_history)  # formats list to str
        # input_params = {'history': history, 'reminder': reminder}
        # invoke_llm(self.user_llm, self.user_context, input_params, self.model, module="user_simulator", parser=True)

        if max_input_tokens_allowed(history+reminder, model_used=self.model):
            logger.error(f"Token limit was surpassed")
            return "exit"

        if config.token_count_enabled:
            self.user_llm.max_tokens = max_output_tokens_allowed(self.model)

        self.chain = self.user_context | self.user_llm | parser

        response = self.chain.invoke({'history': history, 'reminder': reminder})
        if config.token_count_enabled:
            calculate_cost(history + reminder, response, self.model, module="user_simulator")
        return response


    def invoke(self, conversation_history: dict, reminder: str) -> str:
        """
        Main entrypoint for generating a simulated user response.

        Args:
            conversation_history (dict): Conversation so far.
            reminder (str): Contextual hints.

        Returns:
            str: Generated user response.
        """
        response = self.text_method(conversation_history, reminder)

        return response


class UserSimulator:
    """
    Simulates a user interacting with a chatbot for testing purposes.

    This class manages conversation history, user goals, context,
    interaction styles, and stopping conditions (loops, costs, steps).
    It generates realistic user responses and tracks whether goals
    have been achieved.

    Attributes:
        user_profile: RoleData instance with user configuration.
        fallback: Chatbot fallback sentence.
        temp (float): Sampling temperature for user response generation.
        conversation_history (dict): Log of all interactions.
        ask_about (str): User goals converted into natural language prompt.
        data_gathering (ChatbotAssistant): Extractor for chatbot answers.
        goal_style (list | tuple): Defines when the conversation should stop.
        test_name (str): Name of the current test case.
        repeat_count (int): Counter for repeated fallbacks.
        loop_count (int): Counter for detected loop iterations.
        interaction_count (int): Total number of user-chatbot exchanges.
        user_chain (UserChain): Generator of user responses.
        my_context (InitialContext): Context manager for conversation state.
        output_slots (dict): Tracks variables and their extracted values.
        error_report (list): Accumulated error messages.
    """
    def __init__(self, user_profile: RoleData) -> None:
        self.user_profile = user_profile
        self.fallback = user_profile.fallback
        self.temp = user_profile.temperature
        self.conversation_history = {'interaction': []}
        self.ask_about = user_profile.ask_about.prompt()
        self.data_gathering = ChatbotAssistant(user_profile.ask_about.phrases)
        self.goal_style = user_profile.goal_style
        self.test_name = user_profile.test_name
        self.repeat_count = 0
        self.loop_count = 0
        self.interaction_count = 0
        self.user_chain = UserChain(self.user_profile.role, self.temp)
        self.my_context = self.InitialContext()
        self.output_slots = self.__build_slot_dict()
        self.error_report = []


    def __build_slot_dict(self) -> dict:
        """
        Build an empty slot dictionary from user profile outputs.

        Returns:
            dict: Mapping variable names to None.
        """
        slot_dict = {}
        output_list = self.user_profile.output
        for output in output_list:
            var_name = list(output.keys())[0]
            slot_dict[var_name] = None
        return slot_dict

    class InitialContext:
        """
        Manages the evolving conversational context for the simulated user.
        """
        def __init__(self) -> None:
            self.original_context = []
            self.context_list = []

        def initiate_context(self, context: list) -> None:
            """
            Initialize context with user-defined and default entries.
            """
            default_context = config.default_context

            if isinstance(context, list):
                self.original_context = context.copy() + default_context.copy()
                self.context_list = context.copy() + default_context.copy()
            else:
                self.original_context = [context] + default_context
                self.context_list = [context] + default_context

        def add_context(self, new_context: Any) -> None:
            """
            Append new context entries to the list.
            """
            if isinstance(new_context, list):
                for cont in new_context:
                    self.context_list.append(cont)
            else:
                self.context_list.append(new_context)
                # TODO: add exception to force the user to initiate the context

        def get_context(self) -> str:
            """
            Return the current context as a concatenated string.
            """
            return '. '.join(self.context_list)

        def reset_context(self) -> None:
            """
            Reset context to its original state.
            """
            self.context_list = self.original_context.copy()


    def repetition_track(self, response: str, reps: int = 3) -> None:
        """
        Track repeated fallbacks and update context to rephrase or change topics.

        Args:
            response (str): Chatbot response to evaluate.
            reps (int): Max allowed consecutive repetitions before forcing topic change.
        """
        self.my_context.reset_context()
        logger.info(f'Context list: {self.my_context.context_list}')

        if nlp_processor(response, self.fallback, 0.6):
            self.repeat_count += 1
            self.loop_count += 1
            logger.info(f"is fallback. Repeat_count: {self.repeat_count}. Loop count: {self.loop_count}")

            if self.repeat_count >= reps:
                self.repeat_count = 0
                change_topic = """
                               Since the assistant is not understanding what you're saying, change the 
                               topic to other things to ask about without starting a new conversation
                               """

                self.my_context.add_context(change_topic)

            else:
                ask_repetition = """
                                If the assistant asks you to repeat the question, repeat the last question the user 
                                said but rephrase it.
                                """

                self.my_context.add_context(ask_repetition)
        else:
            self.repeat_count = 0
            self.loop_count = 0


    @staticmethod
    def conversation_ending(response: str) -> bool:
        """
        Check if the response matches conversation-ending patterns.

        Returns:
            bool: True if ending is detected, False otherwise.
        """
        return nlp_processor(response, "src/testing/user_sim/end_conversation_patterns.yml", 0.5)


    def get_history(self) -> str:
        """
        Return the conversation history as a plain text string.
        """
        lines = []
        for inp in self.conversation_history['interaction']:
            for k, v in inp.items():
                lines.append(f"{k}: {v}")
        return "\n".join(lines)


    def update_history(self, role: str, message: str) -> None:
        """
        Add a new entry to the conversation history.

        Args:
            role (str): Speaker ("User" or "Assistant").
            message (str): Content of the message.
        """
        self.conversation_history['interaction'].append({role: message})


    def end_conversation(self, input_msg: str) -> bool:
        """
        Determine if the conversation should stop based on cost,
        step limits, loops, or goals completion.

        Args:
            input_msg (str): Latest assistant message.

        Returns:
            bool: True if the conversation should end, False otherwise.
        """
        if config.total_cost >= config.limit_cost or config.total_individual_cost >= config.limit_individual_cost:
            if config.total_cost >= config.limit_cost:
                config.errors.append({2000: 'Exceeded global cost'})
            elif config.total_individual_cost >= config.limit_individual_cost:
                config.errors.append({2001: 'Exceeded conversation specific cost'})

            logger.info('is end')
            return True

        if self.goal_style[0] == 'steps' or self.goal_style[0] == 'random steps':
            if self.interaction_count >= self.goal_style[1]:
                logger.info('is end')
                return True

        elif self.conversation_ending(input_msg) or self.loop_count >= 9:
            config.errors.append({1000: 'Exceeded loop Limit'})
            logger.warning('Loop count surpassed 9 interactions. Ending conversation.')
            return True

        elif 'all_answered' in self.goal_style[0] or 'default' in self.goal_style[0]:
            if (self.data_gathering.gathering_register["verification"].all()
                and self.all_data_collected()
                    or self.goal_style[2] <= self.interaction_count):
                logger.info(f'limit amount of interactions achieved: {self.goal_style[2]}. Ending conversation.')
                return True
            else:
                return False

        else:
            return False


    def all_data_collected(self) -> bool:
        """
        Check if all required output variables have been filled.

        Returns:
            bool: True if all variables are extracted, False otherwise.
        """
        output_list = self.user_profile.output
        for output in output_list:
            var_name = list(output.keys())[0]
            var_dict = output.get(var_name)
            if var_name in self.output_slots and self.output_slots[var_name] is not None:
                continue
            my_data_extract = DataExtraction(self.conversation_history,
                                             var_name,
                                             var_dict["type"],
                                             var_dict["description"])
            value = my_data_extract.get_data_extraction()
            if value[var_name] is None:
                return False
            else:
                self.output_slots[var_name] = value[var_name]
        return True


    def get_response(self, input_msg: str) -> str:
        """
        Generate a new user response given the assistant's message.

        Args:
            input_msg (str): Latest assistant response.

        Returns:
            str: User's reply, or "exit" if conversation ends.
        """
        self.update_history("Assistant", input_msg)
        self.data_gathering.add_message(self.conversation_history)

        if self.end_conversation(input_msg):
            return "exit"

        self.repetition_track(input_msg)

        self.my_context.add_context(self.user_profile.get_language())

        # history = self.get_history()

        user_response = self.user_chain.invoke(self.conversation_history, self.my_context.get_context())

        self.update_history("User", user_response)

        self.interaction_count += 1

        return user_response


    @staticmethod
    def formatting(role: str, msg: str) -> list[dict]:
        """
        Format a message into role-content structure for LLMs.
        """
        return [{"role": role, "content": msg}]


    def get_interaction_styles_prompt(self) -> str:
        """
        Collect prompts from active interaction styles.

        Returns:
            str: Concatenated prompts (ignores language-change style).
        """
        interaction_style_prompt = []
        for instance in self.user_profile.interaction_styles:
            if instance.change_language_flag:
                pass
            else:
                interaction_style_prompt.append(instance.get_prompt())
        return ''.join(interaction_style_prompt)


    def open_conversation(self, input_msg: str | None = None) -> str:
        """
        Start or continue the conversation.

        Args:
            input_msg (str | None): Optional assistant opening message.

        Returns:
            str: User's first or next reply, or "exit" if conversation ends.
        """
        interaction_style_prompt = self.get_interaction_styles_prompt()
        self.my_context.initiate_context([self.user_profile.context,
                                          interaction_style_prompt,
                                          self.ask_about])

        language_context = self.user_profile.get_language()
        self.my_context.add_context(language_context)

        if input_msg:
            self.update_history("Assistant", input_msg)
            self.data_gathering.add_message(self.conversation_history)
            if self.end_conversation(input_msg):
                return "exit"
            self.repetition_track(input_msg)

        user_response = self.user_chain.invoke(self.conversation_history, self.my_context.get_context())

        self.update_history("User", user_response)

        self.data_gathering.add_message(self.conversation_history)
        self.interaction_count += 1
        return user_response
