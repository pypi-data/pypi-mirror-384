import random
import logging

logger = logging.getLogger('Info Logger')


def find_instance(instances, i_class):
    """
    Find the first instance of a given class in a list.

    Iterates through a list of objects and returns the first one
    that matches the specified class type.

    Args:
        instances (list): List of objects to search.
        i_class (type): Class or type to check against.

    Returns:
        object | None: The first matching instance if found,
        otherwise None.
    """
    for instance in instances:
        if isinstance(instance, i_class):
            return instance
    return None


def create_instance(class_list, interaction_styles):
    """
    Dynamically create instances of interaction style classes.

    Iterates through a list of class specifications and instantiates
    each one using provided arguments. The available classes are looked
    up in the `interaction_styles` dictionary.

    Args:
        class_list (list[dict]): A list of class specifications, where each
            dict must contain:
            - "clase" (str): The class name key from `interaction_styles`.
            - "args" (list, optional): Positional arguments for instantiation.
            - "kwargs" (dict, optional): Keyword arguments for instantiation.
        interaction_styles (dict[str, type]): Mapping of class names to
            actual class constructors.

    Returns:
        list[object]: A list of instantiated objects.

    Raises:
        ValueError: If a class name in `class_list` does not exist in
        `interaction_styles`.
    """
    instances = []
    for class_info in class_list:
        class_name = class_info['clase']
        args = class_info.get('args', [])
        kwargs = class_info.get('kwargs', {})
        if class_name in interaction_styles:
            instance = interaction_styles[class_name](*args, **kwargs)
            instances.append(instance)
        else:
            raise ValueError(f"Couldn't find {class_name} in interaction list.")
    return instances


class InteractionStyle:
    """
    Base class for conversation interaction styles.

    Represents a generic interaction style that can be extended
    (e.g., long phrases, change language, spelling mistakes).
    Provides common attributes and abstract methods to be
    implemented by subclasses.

    Attributes:
        inter_type (str): Name/type of the interaction style.
        change_language_flag (bool): Whether the style requires
            language switching during the conversation.
        languages_options (list[str]): Available languages if
            change-language behavior is enabled.
    """

    def __init__(self, inter_type: str) ->None:
        """
        Initialize the interaction style.

        Args:
            inter_type (str): The type or name of this style.
        """
        self.inter_type = inter_type
        self.change_language_flag = False
        self.languages_options = []

    def get_prompt(self):
        """
        Return the prompt associated with this style.

        To be implemented by subclasses. Default does nothing.

        Returns:
            Any: A style-specific prompt or instruction.
        """
        return

    def get_metadata(self):
        """
        Return metadata describing this interaction style.

        To be implemented by subclasses. Default does nothing.

        Returns:
            dict | Any: Metadata structure with details about
            the interaction style.
        """
        return


class LongPhrases(InteractionStyle):
    def __init__(self) -> None:
        super().__init__(inter_type='long phrases')

    def get_prompt(self) -> str:
        return "use very long phrases to write anything. "

    def get_metadata(self) -> str:
        return self.inter_type


class ChangeYourMind(InteractionStyle):
    def __init__(self) -> None:
        super().__init__(inter_type='change your mind')

    def get_prompt(self) -> str:
        return "eventually, change your mind about any information you provided. "

    def get_metadata(self) -> str:
        return self.inter_type


class ChangeLanguage(InteractionStyle):
    # TODO: add chance variable with *args
    def __init__(self, default_language: str) -> None:
        super().__init__(inter_type='change language')
        self.default_language = default_language
        self.languages_list = []
        self.chance = 0.3

    def get_prompt(self) -> str:
        lang = self.language(self.chance)
        prompt = f"""Please, always talk in {lang}, even If the assistant tells you that he doesn't understand, 
                or you had a conversation in another language before. """
        return prompt

    def language(self, chance: float = 0.3) -> str:
        """
        Decide the conversation language based on probability.

        Args:
            chance (float, optional): Probability (0–1) of switching
                to a random language. Defaults to 0.3.

        Returns:
            str: The chosen language (random or default).
        """
        chance = chance*100
        rand_number = random.randint(1, 100)
        if rand_number <= chance:
            lang = random.choice(self.languages_options)
            logger.info(f'Language was set to {lang}')
            self.languages_list.append(lang)
            return lang
        else:
            self.languages_list.append(self.default_language)
            logger.info(f'Language was set to default ({self.default_language})')
            return self.default_language

    def reset_language_list(self) -> None:
        """
        Clear the history of previously chosen languages.
        """
        self.languages_list.clear()

    def get_metadata(self) -> dict:
        """
        Retrieve metadata about chosen languages.

        Returns:
            dict: A dictionary containing the list of languages
            used in this interaction style, under the key
            `"change languages"`.
        """
        language_list = self.languages_list.copy()
        self.reset_language_list()
        return {'change languages': language_list}


class MakeSpellingMistakes(InteractionStyle):
    def __init__(self) -> None:
        super().__init__(inter_type='make spelling mistakes')

    def get_prompt(self) -> str:
        prompt = """
                 please, make several spelling mistakes during the conversation. Minimum 5 typos per 
                 sentence if possible. 
                 """
        return prompt

    def get_metadata(self) -> str:
        return self.inter_type


class SingleQuestions(InteractionStyle):
    def __init__(self) -> None:
        super().__init__(inter_type='single questions')

    def get_prompt(self) -> str:
        return "ask only one question per interaction. "

    def get_metadata(self) -> str:
        return self.inter_type


class AllQuestions(InteractionStyle):
    # todo: all questions should only get questions from ask_about
    def __init__(self) -> None:
        super().__init__(inter_type='all questions')

    def get_prompt(self) -> str:
        return "ask everything you have to ask in one sentence. "

    def get_metadata(self) -> str:
        return self.inter_type


class Default(InteractionStyle):
    def __init__(self) -> None:
        super().__init__(inter_type='default')

    def get_prompt(self) -> str:
        return "Ask about one or two things per interaction, don't ask everything you want to know in one sentence."

    def get_metadata(self) -> str:
        return self.inter_type
