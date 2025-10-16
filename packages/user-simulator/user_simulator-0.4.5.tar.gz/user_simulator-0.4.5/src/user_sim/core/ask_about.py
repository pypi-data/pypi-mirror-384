import re

from typing import Any
from user_sim.utils.utilities import *
from user_sim.utils.exceptions import *

import numpy as np
import logging
import random

from user_sim.utils import config
from allpairspy import AllPairs
from langchain_core.prompts import ChatPromptTemplate
from user_sim.utils.dates import get_date_list
from user_sim.utils.utilities import init_model
from user_sim.utils.token_cost_calculator import calculate_cost, max_input_tokens_allowed, max_output_tokens_allowed

model = ""
llm = None

logger = logging.getLogger('Info Logger')


def init_any_list_module():
    global model
    global llm
    model, llm = init_model()


def reorder_variables(entries):
    def parse_entry(entry):

        match = re.search(r'forward\((.*?)\)', entry['function'])
        if match:
            slave = entry['name']
            master = match.group(1)
            return slave, master

    def reorder_list(dependencies):
        tuple_list = []
        none_list = []
        for main_tuple in dependencies:
            if main_tuple:
                for comp_tuple in dependencies:
                    if comp_tuple:
                        if main_tuple[1] == comp_tuple[0]:
                            tuple_list.append(main_tuple)
                            tuple_list.append(comp_tuple)
            else:
                none_list.append(main_tuple)

        tuple_list = list(dict.fromkeys(tuple_list))
        return tuple_list

    dependencies_list = []

    for entry in entries:
        dependencies_list.append(parse_entry(entry))

    reordered_list = reorder_list(dependencies_list)

    editable_entries = entries.copy()
    new_entries = []
    for tupl in reordered_list:
        for entry in entries:
            if tupl[0] == entry['name']:
                new_entries.append(entry)
                editable_entries.remove(entry)
    reordered_entries = new_entries + editable_entries
    return reordered_entries


def dependency_error_check(variable_list):
    for slave in variable_list:
        for master in variable_list:
            if slave['dependence'] == master['name']:
                pattern = r'(\w+)\((\w*)\)'
                match = re.search(pattern, master['function'])
                function = match.group(1)
                if function != 'forward':
                    raise InvalidDependence(f"the following function doesn't admit dependence: {function}()")


def check_circular_dependency(items):
    dependencies = {}
    for item in items:
        name = item['name']
        dep = item['dependence']
        dependencies[name] = dep

    def visit(node, visited, stack):
        if node in stack:
            cycle = ' -> '.join(stack + [node])
            raise Exception(f"Circular dependency detected: {cycle}")
        if node in visited or node not in dependencies:
            return
        stack.append(node)
        dep = dependencies[node]
        if dep is not None:
            visit(dep, visited, stack)
        stack.pop()
        visited.add(node)

    visited = set()
    for node in dependencies.keys():
        if node not in visited:
            visit(node, visited, [])


class VarGenerators:

    def __init__(self, variable_list):

        self.forward_combinations = 0
        self.pairwise_combinations = 0
        self.variable_list = variable_list
        self.generator_list = self.create_generator_list()

    class ForwardMatrixGenerator:
        def __init__(self):
            self.forward_function_list = []
            self.dependence_tuple_list = []  # [(size, toppings), (toppings,drink), (drink, None)]
            self.dependent_list = []
            self.independent_list = []
            self.item_matrix = []
            # self.dependent_generators = []
            # self.independent_generators = []

        def get_matrix(self, dependent_variable_list):
            self.item_matrix.clear()
            for index, dependence in enumerate(dependent_variable_list):
                self.item_matrix.append([])
                for variable in dependence:
                    for forward in self.forward_function_list:
                        if variable == forward['name']:
                            self.item_matrix[index].append(forward['data'])

        def add_forward(self,
                        forward_variable):  # 'name': var_name, 'data': data_list,'function': content['function'],'dependence': dependence}
            self.forward_function_list.append(forward_variable)

            if forward_variable['dependence']:
                master = forward_variable['dependence']
                slave = forward_variable['name']
                self.dependence_tuple_list.append((slave, master))
                for indep_item in self.independent_list:
                    if indep_item == master:
                        self.independent_list.remove(master)
                        self.dependence_tuple_list.append((master, None))

            else:
                if self.dependence_tuple_list:
                    dtlc = self.dependence_tuple_list.copy()
                    for dependence in dtlc:  # [(size, toppings), (toppings,drink), (drink, None)]
                        if forward_variable['name'] in dependence:
                            master = forward_variable['name']
                            self.dependence_tuple_list.append((master, None))
                            break
                    else:
                        master = forward_variable['name']
                        self.independent_list.append(master)
                else:
                    master = forward_variable['name']
                    self.independent_list.append(master)

            if self.dependence_tuple_list:
                self.dependent_list = build_sequence(self.dependence_tuple_list)
                self.get_matrix(self.dependent_list)
                pass


        @staticmethod
        def combination_generator(matrix):
            if not matrix:
                while True:
                    yield []
            else:
                lengths = [len(lst) for lst in matrix]
                indices = [0] * len(matrix)
                while True:
                    # Yield the current combination based on indices
                    yield [matrix[i][indices[i]] for i in range(len(matrix))]
                    # Increment indices from the last position
                    i = len(matrix) - 1
                    while i >= 0:
                        indices[i] += 1
                        if indices[i] < lengths[i]:
                            break
                        else:
                            indices[i] = 0
                            i -= 1

        def get_combinations(self):
            if self.item_matrix:
                combinations = []
                for matrix in self.item_matrix:
                    combinations_one_matrix = 1
                    for sublist in matrix:
                        combinations_one_matrix *= len(sublist)
                    combinations.append(combinations_one_matrix)
                return max(combinations)
            else:
                return 0

        @staticmethod
        def forward_generator(value_list):
            while True:
                for sample in value_list:
                    yield [sample]

        def get_generator_list(self):
            function_map = {function['name']: function['data'] for function in self.forward_function_list}

            independent_generators = [
                {'name': i,
                 'generator': self.forward_generator(function_map[i]),
                 'type': "forward"} for i in self.independent_list if
                i in function_map
            ]

            dependent_generators = [
                {'name': val,
                 'generator': self.combination_generator(self.item_matrix[index]),
                 'type': 'forward',
                 'matrix': self.item_matrix[index]} for index, val in enumerate(self.dependent_list)
            ]
            gens = independent_generators + dependent_generators
            return gens

    class PairwiseMatrixGenerator:
        def __init__(self):
            self.pairwise_function_list = []
            self.pairwise_variable_list = []
            self.parameters_matrix = []
            self.item_matrix = []
            self.combinations = 0

        def add_pairwise(self, pairwise_variable):   # 'name': var_name, 'data': data_list,'function': content['function'],'dependence': dependence}
            self.pairwise_function_list.append(pairwise_variable)
            self.pairwise_variable_list.append(pairwise_variable)

            if len(self.pairwise_function_list) > 1:
                self.pairwise_function_list = sorted(self.pairwise_function_list, key=lambda d: len(d['data']), reverse=True)
                self.pairwise_variable_list = [function['name'] for function in self.pairwise_function_list]
                self.parameters_matrix = [function['data'] for function in self.pairwise_function_list]
                self.item_matrix = list(AllPairs(self.parameters_matrix))
                self.combinations = len(self.item_matrix)



        def pairwise_generator(self, pairwise_matrix):
            """
            Given a list of parameter value-lists, generate exactly
            (size of two largest lists) combinations by taking the full
            Cartesian product of those two and cycling through the others.
            """

            for values in pairwise_matrix:
                yield values


        def get_generator_list(self):

            if self.pairwise_function_list:
                pairwise_generators = [
                    {'name': self.pairwise_variable_list,
                     'generator': self.pairwise_generator(self.item_matrix),
                     'type': 'pairwise',
                     'matrix': self.item_matrix
                     }
                ]
            else:
                pairwise_generators = []

            return pairwise_generators

        def get_combinations(self):
            # self.combinations = len(self.parameters_matrix[0]) * len(self.parameters_matrix[1])
            return self.combinations

    def create_generator_list(self):
        generator_list = []
        my_forward = self.ForwardMatrixGenerator()
        my_pairwise = self.PairwiseMatrixGenerator()
        for variable in self.variable_list:
            name = variable['name']
            data = variable['data']
            pattern = r'(\w+)\((\w*)\)'
            if not variable['function'] or variable['function'] == 'default()':
                generator = self.default_generator(data)
                generator_list.append({'name': name, 'generator': generator})
            else:
                match = re.search(pattern, variable['function'])
                if match:
                    handler_name = match.group(1)
                    count = match.group(2) if match.group(2) else ''
                    if handler_name == 'random':
                        if count == '':
                            generator = self.random_choice_generator(data)
                            generator_list.append({'name': name, 'generator': generator})
                        elif count.isdigit():
                            count_digit = int(count)
                            generator = self.random_choice_count_generator(data, count_digit)
                            generator_list.append({'name': name, 'generator': generator})
                        elif count == 'rand':
                            generator = self.random_choice_random_count_generator(data)
                            generator_list.append({'name': name, 'generator': generator})

                    elif handler_name == 'forward':
                        my_forward.add_forward(variable)

                    elif handler_name == 'pairwise':
                        my_pairwise.add_pairwise(variable)

                    elif handler_name == 'another':
                        if count == '':
                            generator = self.another_generator(data)
                            generator_list.append({'name': name, 'generator': generator})
                        elif count.isdigit():
                            count_digit = int(count)
                            generator = self.another_count_generator(data, count_digit)
                            generator_list.append({'name': name, 'generator': generator})
                    else:
                        raise InvalidGenerator(f'Invalid generator function: {handler_name}')
                else:
                    raise InvalidFormat(f"an invalid function format was used: {variable['function']}")


        generators = generator_list + my_forward.get_generator_list() + my_pairwise.get_generator_list()
        self.forward_combinations = my_forward.get_combinations()
        self.pairwise_combinations = my_pairwise.get_combinations()
        return generators

    @staticmethod
    def default_generator(data):
        while True:
            yield [data]

    @staticmethod
    def random_choice_generator(data):
        while True:
            yield [random.choice(data)]

    @staticmethod
    def random_choice_count_generator(data, count):
        while True:
            sample = random.sample(data, min(count, len(data)))
            yield sample

    @staticmethod
    def random_choice_random_count_generator(data):
        while True:
            count = random.randint(1, len(data))
            sample = random.sample(data, min(count, len(data)))
            yield sample

    @staticmethod
    def another_count_generator(data, count):
        while True:
            copy_list = data[:]
            random.shuffle(copy_list)
            for i in range(0, len(copy_list), count):
                yield copy_list[i:i + count]

    @staticmethod
    def another_generator(data):
        while True:
            copy_list = data[:]
            random.shuffle(copy_list)
            for sample in copy_list:
                yield [sample]


class AskAboutClass:
    """
    Handles goal-related variables and phrases for user simulation.

    This class processes a YAML-defined set of goals, extracting
    variables, generating value combinations, and building natural
    language prompts to guide chatbot testing scenarios.

    Key responsibilities:
        - Extract and validate variables from structured goal definitions.
        - Support different data types: string, int, float, and custom types.
        - Generate variable combinations (forward and pairwise).
        - Handle dynamic values via custom functions, date generators,
          or 'any()' placeholders using LLM assistance.
        - Maintain both structured variable data and natural language
          phrases for use in simulated conversations.

    Attributes:
        variable_list (list[dict]): Extracted variables with name,
            data, function, and dependencies.
        str_list (list[str]): Raw string phrases from input data.
        var_generators (list): Variable generator objects for iteration.
        forward_combinations (int): Total number of forward combinations.
        pairwise_combinations (int): Total number of pairwise combinations.
        phrases (list[str]): Current working list of phrases after
            variable replacement.
        picked_elements (list[dict]): Variables and values already
            used in phrase replacement.
    """
    def __init__(self, data):

        self.variable_list = self.get_variables(data)
        self.str_list = self.get_phrases(data)
        self.var_generators, self.forward_combinations, self.pairwise_combinations = self.variable_generator(self.variable_list)
        self.phrases = self.str_list.copy()
        self.picked_elements = []


    @staticmethod
    def validate_type_format(data_list: list, data_type: str) -> bool:
        """
        Validate that all items in a list follow the regex format of a given type.

        Args:
            data_list (list): Values to check.
            data_type (str): The type key in config.types_dict.

        Returns:
            bool: True if all items match the type format, False otherwise.
        """
        type_format = config.types_dict[data_type]["format"]
        t_format = normalize_regex_pattern(type_format)
        regex = re.compile(t_format)
        match = all(regex.fullmatch(item) for item in data_list)
        return match


    def get_variables(self, data: list) -> list[dict]:
        """
        Extract structured variables from input goal definitions.

        Supports:
          - Lists of values (string, int, float, custom types).
          - Ranges with min/max/step or linspace.
          - External generators via file/function calls.
          - Date-based generators.
          - 'any()' placeholders for dynamic expansion.

        Args:
            data (list): Input goals from YAML.

        Returns:
            list[dict]: List of variable dictionaries with name, data,
            function, and dependencies.

        Raises:
            InvalidDataType, InvalidFormat, EmptyListExcept: If
            validation fails.
        """
        variables = []

        for item in data:
            if isinstance(item, dict):
                var_name = list(item.keys())[0]
                content = item[var_name]
                content_data = content['data'].copy()
                if isinstance(content_data, dict) and 'file' in content_data:  # check for personalized functions
                    path = content_data['file']
                    function = content_data['function_name']
                    if 'args' in content_data:
                        function_arguments = content_data['args']
                        data_list = execute_list_function(path, function, function_arguments)
                    else:
                        data_list = execute_list_function(path, function)
                elif isinstance(content_data, dict) and 'date' in content_data:  # check for date generator
                    data_list = get_date_list(content_data['date'])
                else:
                    if content_data:
                        data_list = content_data
                    else:
                        raise EmptyListExcept(f'Data list is empty.')

                any_list = []
                item_list = []

                if isinstance(content_data, list):  # check for any() in data list

                    for index, value in enumerate(data_list):
                        if isinstance(value, str):
                            if 'any(' in value:
                                any_list.append(value)
                            else:
                                item_list.append(value)
                        else:
                            item_list.append(value)

                if content['type'] == 'string':
                    for i in item_list:
                        if type(i) is not str:
                            raise InvalidDataType(f'The following item is not a string: {i}')
                    output_data_list = self.get_any_items(item_list, any_list, "string")
                    if not data_list:
                        raise EmptyListExcept(f'Data list is empty.')

                elif content['type'] == 'int':
                    if isinstance(data_list, list):
                        for i in data_list:
                            if type(i) is not int:
                                raise InvalidDataType(f'The following item is not an integer: {i}')
                        if data_list:
                            output_data_list = data_list
                        else:
                            raise EmptyListExcept(f'Data list is empty.')
                    elif isinstance(data_list, dict) and 'min' in data_list:
                        keys = list(data_list.keys())
                        data = data_list
                        if 'step' in keys:
                            if isinstance(data['min'], int) and isinstance(data['max'], int) and isinstance(
                                    data['step'], int):
                                output_data_list = np.arange(data['min'], data['max'], data['step'])
                                output_data_list = output_data_list.tolist()
                                output_data_list.append(data['max'])

                            else:
                                raise InvalidDataType(f'Some of the range function parameters are not integers.')
                        else:
                            if isinstance(data['min'], int) and isinstance(data['max'], int):
                                output_data_list = np.arange(data['min'], data['max'])
                                output_data_list = output_data_list.tolist()
                            else:
                                raise InvalidDataType(f'Some of the range function parameters are not integers.')
                    else:
                        raise InvalidFormat(f'Data follows an invalid format.')
                elif content['type'] == 'float':
                    if isinstance(data_list, list):
                        for i in data_list:
                            if not isinstance(i, (int, float)):
                                raise InvalidDataType(f'The following item is not a number: {i}')
                        if data_list:
                            output_data_list = data_list
                        else:
                            raise EmptyListExcept(f'Data list is empty.')
                    elif isinstance(data_list, dict) and 'min' in data_list:
                        keys = list(data_list.keys())
                        data = content['data']
                        if 'step' in keys:
                            output_data_list = np.arange(data['min'], data['max'], data['step'])
                            output_data_list = output_data_list.tolist()
                            output_data_list.append(data['max'])

                        elif 'linspace' in keys:
                            output_data_list = np.linspace(data['min'], data['max'], data['linspace'])
                            output_data_list = output_data_list.tolist()
                        else:
                            raise MissingStepDefinition(
                                f'"step" or "lisnpace" parameter missing. A step separation must be defined.')
                    else:
                        raise InvalidFormat(f'Data follows an invalid format.')
                else:
                    custom_types_name = list(config.types_dict.keys())
                    if content["type"] in custom_types_name:
                        output_data_list = self.get_any_items(item_list, any_list, content["type"])
                        if not self.validate_type_format(output_data_list, content["type"]):
                            raise InvalidItemType(f'Invalid data type for variable list.')
                    else:
                        raise InvalidItemType(f'Invalid data type for variable list.')

                pattern = r'(\w+)\((\w*)\)'
                if not content['function']:
                    content['function'] = 'default()'

                match = re.search(pattern, content['function'])
                if match:
                    count = match.group(2) if match.group(2) else ''
                    if not count == '' or count == 'rand' or count.isdigit():
                        dependence = count
                    else:
                        dependence = None
                else:
                    dependence = None

                logger.info(f"{var_name}: {output_data_list}")

                dictionary = {'name': var_name, 'data': output_data_list,
                              'function': content['function'],
                              'dependence': dependence}  # (size, [small, medium], random(), toppings)
                variables.append(dictionary)
        reordered_variables = reorder_variables(variables)
        dependency_error_check(reordered_variables)
        check_circular_dependency(reordered_variables)
        return reordered_variables


    @staticmethod
    def get_phrases(data: list) -> list[str]:
        """
        Collect raw string phrases from goal definitions.

        Args:
            data (list): Input goals from YAML.

        Returns:
            list[str]: Extracted plain phrases.
        """
        str_content = []
        for item in data:
            if isinstance(item, str):
                str_content.append(item)
        return str_content


    @staticmethod
    def variable_generator(variables: list[dict]):
        """
        Build variable generators and compute possible combinations.

        Args:
            variables (list[dict]): Extracted variable definitions.

        Returns:
            tuple:
                - list: Generator objects.
                - int: Forward combination count.
                - int: Pairwise combination count.
        """
        generators = VarGenerators(variables)
        generators_list = generators.generator_list
        forward_combinations = generators.forward_combinations
        pairwise_combinations = generators.pairwise_combinations
        return generators_list, forward_combinations, pairwise_combinations


    @staticmethod
    def get_any_items(item_list: list, any_list: list[str], data_type: str) -> list:
        """
        Resolve 'any()' placeholders by generating new values.

        Uses the LLM when available to expand placeholders into lists
        of values, avoiding duplicates already in `item_list`.

        Args:
            item_list (list): Base list of items.
            any_list (list[str]): Placeholders with 'any(...)'.
            data_type (str): Type of the data (string, int, float, custom).

        Returns:
            list: Expanded list including resolved values.
        """
        # model = config.model
        response_format = {
            "title": "List_of_values",
            "description": "A list of string values.",
            "type": "object",
            "properties": {
                "answer": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "required": ["answer"],
            "additionalProperties": False
        }

        output_list = item_list.copy()

        if any_list:
            for data in any_list:
                content = re.findall(r'any\((.*?)\)', data)

                if data_type not in ("string", "float", "int"): # modifies "content" adding custom type prompts
                    type_yaml = config.types_dict.get(data_type)

                    type_description = f"The type of data is described as follows: {type_yaml['type_description']}"
                    type_format = f"Data follows the following format as a regular expression: {type_yaml['format']}"
                    content = f"{content}.{type_description}. {type_format}"

                if llm is None:
                    logger.error("data gathering module not initialized.")
                    return ""

                system = "You are a helpful assistant that creates a list of whatever the user asks."
                message = f"A list of any of these: {content}. Avoid putting any of these: {output_list}"
                prompt = ChatPromptTemplate.from_messages([("system", system), ("human", "{input}")])
                # input_message = parse_content_to_text(message)
                input_message = system + message

                if max_input_tokens_allowed(input_message, model_used=config.model):
                    logger.error(f"Token limit was surpassed")
                    return output_list

                if config.token_count_enabled:
                    # params["max_completion_tokens"] = max_output_tokens_allowed(model)
                    llm.max_tokens = max_output_tokens_allowed(model)

                structured_llm = llm.with_structured_output(response_format)
                prompted_structured_llm = prompt | structured_llm
                response = prompted_structured_llm.invoke({"input": message})
                # response = client.chat.completions.create(**params)

                try:
                    # raw_data = json.loads(response.choices[0].message.content)
                    # output_data = raw_data["answer"]
                    output_data = response["answer"]
                    ls_to_str = ", ".join(response["answer"])
                    calculate_cost(input_message, ls_to_str, model=model, module="goals_any_list")
                except Exception as e:
                    logger.error(f"Truncated data in message: {response.choices[0].message.content}")
                    output_data = [None]

                output_list += output_data

            return output_list
        else:
            return output_list


    def picked_element_already_in_list(self, match: re.Match, value: Any):
        """
        Add a variable-value mapping to picked_elements if not already present.

        Args:
            match (re.Match): Regex match with the variable name.
            value (Any): The chosen value for this variable.
        """
        element_list = [list(element.keys())[0] for element in self.picked_elements]
        if match.group(1) not in element_list:
            self.picked_elements.append({match.group(1): value})


    def replace_variables(self, generator: dict) -> None:
        """
        Replace placeholders in phrases with generated variable values.

        Args:
            generator (dict): Generator object containing variable name,
                data, and function.

        Updates:
            self.phrases with substituted values.
        """
        pattern = re.compile(r'\{\{(.*?)\}\}')

        # this is for nested forwards
        if isinstance(generator['name'], list) and len(generator['name']) > 1:
            values = next(generator['generator'])
            keys = generator['name']
            mapped_combinations = dict(zip(keys, values))
            self.picked_elements.extend([{key: value} for key, value in mapped_combinations.items()])
            replaced_phrases = []
            for phrase in self.phrases.copy():
                def replace_variable(match):
                    variable = match.group(1)
                    return str(mapped_combinations.get(variable, match.group(0)))

                replaced_phrase = re.sub(r'\{\{(\w+)\}\}', replace_variable, phrase)
                replaced_phrases.append(replaced_phrase)
            self.phrases = replaced_phrases

        # this is for everything else
        else:
            value = next(generator['generator'])
            name = generator['name']

            for index, text in enumerate(self.phrases):
                matches = re.finditer(pattern, text)
                for match in matches:
                    if match.group(1) == name:
                        self.picked_element_already_in_list(match, value)
                        # self.picked_elements.append({match.group(1): value})
                        replacement = ', '.join([str(v) for v in value])
                        text = text.replace(match.group(0), replacement)
                        self.phrases[index] = text
                        break
                else:
                    self.phrases[index] = text


    def ask_about_processor(self) -> list[str]:
        """
        Process all variable generators to replace placeholders in phrases.

        Returns:
            list[str]: Updated phrases with variables replaced.
        """
        for generator in self.var_generators:
            self.replace_variables(generator)
        return self.phrases


    def prompt(self) -> str:
        """
        Build a natural language prompt from processed phrases.

        Returns:
            str: Concatenated phrases as a single prompt.
        """
        phrases = self.ask_about_processor()
        return list_to_phrase(phrases, True)


    def reset(self) -> None:
        """
        Reset the object state to reuse in another simulation.

        Resets:
            - picked_elements → []
            - phrases → copy of str_list
        """
        self.picked_elements = []
        self.phrases = self.str_list.copy()
