import timeit
from argparse import Namespace
from typing import LiteralString

from user_sim.cli.cli import parse_chat_arguments
from user_sim.core.data_extraction import DataExtraction
from user_sim.core.role_structure import *
from user_sim.core.user_simulator import UserSimulator
from user_sim.utils.show_logs import *
from user_sim.utils.utilities import *
from user_sim.utils import config
from user_sim.utils.token_cost_calculator import create_cost_dataset
from user_sim.utils.register_management import clean_temp_files
from user_sim.utils.stats import ExecutionStats, save_test_conv
from chatbot_connectors.cli import (ChatbotFactory, parse_connector_params,
                                    handle_list_connectors, handle_list_connector_params)
from chatbot_connectors.core import Chatbot
from importlib.resources import files

# check_keys(["OPENAI_API_KEY"])


def configure_project(project_path: str) -> None:
    """
    Configure project-specific and default paths in the global `config` object.

    Args:
        project_path (str): Base path of the project containing
            the `profiles`, `personalities`, and `types` folders.

    Returns:
        None
    """
    # sensei
    config.cache_path = files("data") / "cache"
    config.pdfs_path = files("data") / "pdfs"
    config.audio_files_path = files("data") / "audio_files"
    config.default_types_path = files("config") / "types"
    config.default_personalities_path = files("config") / "personalities"

    # project
    config.project_folder_path = project_path
    config.profiles_path = os.path.join(project_path, "profiles")
    config.custom_personalities_path = os.path.join(project_path, "personalities")
    config.custom_types_path = os.path.join(project_path, "types")
    custom_types = load_yaml_files_from_folder(config.custom_types_path)

    default_types = load_yaml_files_from_folder(config.default_types_path, existing_keys=custom_types.keys())
    config.types_dict = {**default_types, **custom_types}


def _setup_configuration() -> Namespace:
    """Parse command line arguments, validate config, and create output dir.

    Returns:
        The parsed and validated command line arguments

    Raises:
        Error: If the specified technology is invalid
    """

    args = parse_chat_arguments()

    logger = create_logger(args.verbose, 'Info Logger')
    logger.info('Logs enabled!')

    if getattr(args, "list_connector_params", None):
        try:
            handle_list_connector_params(args.list_connector_params)
            sys.exit(0)
        except (ValueError, RuntimeError):
            logger.exception("Failed to list connector parameters")
            sys.exit(1)

    if getattr(args, "list_connectors", None):
        try:
            handle_list_connectors()
            sys.exit(0)
        except RuntimeError:
            logger.error("Failed to list connectors")
            sys.exit(1)

    valid_technologies = ChatbotFactory.get_available_types()
    if args.technology not in valid_technologies:
        logger.error("Invalid technology '%s'. Must be one of: %s", args.technology, valid_technologies)
        raise ("Invalid technology '%s'. Must be one of: %s", args.technology, valid_technologies)

    configure_project(args.project_path)

    # check_keys(["OPENAI_API_KEY"])
    config.test_cases_folder = args.output
    config.ignore_cache = args.ignore_cache
    config.update_cache = args.update_cache
    config.clean_cache = args.clean_cache

    return args


def get_conversation_metadata(user_profile: RoleData, the_user: UserSimulator, serial: str | None = None) -> dict:
    """
    Collect and return metadata for a conversation session.

    This function aggregates information from a user profile, the simulated user,
    and global configuration into a structured metadata dictionary. It includes
    conversation context, interaction styles, goals, extracted data, language,
    cost, and errors.

    Args:
        user_profile (object): The user profile providing conversation
            settings such as interaction styles, context, language, and goals.
        the_user (object): The simulated user instance, expected to contain
            `conversation_history` and data gathering attributes.
        serial (str | None, optional): Unique identifier for the test or session.
            Defaults to None.

    Returns:
        dict: A dictionary containing the conversation metadata with the following keys:
            - `"serial"`: Serial identifier of the session.
            - `"language"`: The language defined in the user profile.
            - `"context"`: Raw context information from the user profile.
            - `"ask_about"`: List of variables or topics the chatbot should ask about.
            - `"conversation"`: List describing interaction style, conversation number,
              and goal style.
            - `"data_output"`: Extracted variables and their values from the conversation.
            - `"errors"`: A list of error entries (e.g., missing goals).
            - `"total_cost($)"`: The total conversation cost (float).

    Side Effects:
        - Appends error entries to `config.errors` if some expected goals
          were not completed (values are `None`).
        - Reads from the cost dataset defined in `config.cost_ds_path`.

    Notes:
        - Relies on helper functions defined within:
            - `conversation_metadata()`
            - `ask_about_metadata()`
            - `data_output_extraction()`
            - `total_cost_calculator()`
        - The `"goal_style"` format differs if `"random steps"` is present in the YAML
          configuration.
    """
    def conversation_metadata(up):
        interaction_style_list = []
        conversation_list = []

        for inter in up.interaction_styles:
            interaction_style_list.append(inter.get_metadata())

        conversation_list.append({'interaction_style': interaction_style_list})

        if isinstance(up.yaml['conversation']['number'], int):
            conversation_list.append({'number': up.yaml['conversation']['number']})
        else:
            conversation_list.append({'number': up.conversation_number})

        if 'random steps' in up.yaml['conversation']['goal_style']:
            conversation_list.append({'goal_style': {'steps': up.goal_style[1]}})
        else:
            conversation_list.append(up.yaml['conversation']['goal_style'])

        return conversation_list


    def ask_about_metadata(up):
        if not up.ask_about.variable_list:
            return up.ask_about.str_list

        if user_profile.ask_about.picked_elements:
            user_profile.ask_about.picked_elements = [
        {clave: (valor[0] if isinstance(valor, list) and len(valor) == 1 else valor)
         for clave, valor in dic.items()}
        for dic in user_profile.ask_about.picked_elements
    ]

        return user_profile.ask_about.str_list + user_profile.ask_about.picked_elements

    def data_output_extraction(u_profile, user):
        output_list = u_profile.output
        data_list = []
        for output in output_list:
            var_name = list(output.keys())[0]
            var_dict = output.get(var_name)
            my_data_extract = DataExtraction(user.conversation_history,
                                             var_name,
                                             var_dict["type"],
                                             var_dict["description"])
            data_list.append(my_data_extract.get_data_extraction())

        data_dict = {k: v for dic in data_list for k, v in dic.items()}
        has_none = any(value is None for value in data_dict.values())
        if has_none:
            count_none = sum(1 for value in data_dict.values() if value is None)
            config.errors.append({1001: f"{count_none} goals left to complete."})

        return data_list

    def total_cost_calculator():
        import pandas as pd
        encoding = get_encoding(config.cost_ds_path)["encoding"]
        cost_df = pd.read_csv(config.cost_ds_path, encoding=encoding)
        total_sum_cost = cost_df[cost_df["Conversation"]==config.conversation_name]['Total Cost'].sum()
        total_sum_cost = round(float(total_sum_cost), 8)

        return total_sum_cost


    data_output = {'data_output': data_output_extraction(user_profile, the_user)}
    context = {'context': user_profile.raw_context}
    ask_about = {'ask_about': ask_about_metadata(user_profile)}
    conversation = {'conversation': conversation_metadata(user_profile)}
    language = {'language': user_profile.language}
    serial_dict = {'serial': serial}
    errors_dict = {'errors': config.errors}
    total_cost = {'total_cost($)': total_cost_calculator()}
    metadata = {**serial_dict,
                **language,
                **context,
                **ask_about,
                **conversation,
                **data_output,
                **errors_dict,
                **total_cost
                }

    return metadata


def build_chatbot(technology: str, connector: str) -> Chatbot:
    """
    Build and return a chatbot instance using the given technology and connector parameters.

    This function parses the connector configuration, then uses the
    `ChatbotFactory` to create a chatbot connector of the specified type.

    Args:
        technology (str): The chatbot technology or framework to use
            (e.g., "taskyto", "rasa", "dialogflow").
        connector (str): Connector configuration parameters, which will
            be parsed by `parse_connector_params`.

    Returns:
        Chatbot: An instance of a chatbot connector created by `ChatbotFactory`.

    Notes:
        - Relies on `parse_connector_params` to validate and prepare
          connector arguments.
    """
    parsed_connector = parse_connector_params(connector)
    chatbot = ChatbotFactory.create_chatbot(chatbot_type=technology, **parsed_connector)
    return chatbot


def generate_conversation(
        technology: str,
        connector: str,
        user: str | LiteralString | bytes,
        personality: str | None,
        output: str,
        project_folder: str
) -> None:
    """
    Run one or more simulated conversations between a chatbot and a user.

    This function orchestrates the full process of creating a chatbot instance,
    simulating conversations based on user profiles, and collecting metadata,
    statistics, and costs. Conversations can be run in either text or speech
    format depending on the profile configuration.

    Args:
        technology (str): Chatbot technology or backend to use (e.g., "taskyto", "rasa").
        connector (str): Connector configuration parameters passed to the chatbot.
        user (str): User profile path used to generate profiles.
        personality (str): Path or identifier of the chatbot’s personality definition.
        output (str): Directory path for saving test results, conversations, and metadata.
        project_folder (str): Path to the project containing configuration and profiles.

    Returns:
        None

    Side Effects:
        - Creates and saves test conversations and metadata files.
        - Updates global `config` attributes such as:
            - `serial`
            - `conversation_name`
            - `test_name`
            - `total_individual_cost`
        - Appends errors to `config.errors` when errors are found during conversations.
        - Writes statistics and costs to disk if `output` is enabled.
        - Cleans temporary files if `config.clean_cache` is set.

    Notes:
        - Each profile may generate multiple conversations depending on
          `user_profile.conversation_number`.
        - Supports both text-based and speech-based interaction formats.
        - Execution times and response times are measured and logged.
        - Uses `ExecutionStats` to track and export test statistics.
        - If speech format is selected, depends on the `STTModule` for ASR.

    """
    profiles = parse_profiles(user)
    serial = generate_serial()
    config.serial = serial
    create_cost_dataset(serial, output)
    my_execution_stat = ExecutionStats(output, serial)
    the_chatbot = build_chatbot(technology, connector)

    # start of the test
    for profile in profiles:
        user_profile = RoleData(profile, project_folder, personality)
        test_name = user_profile.test_name
        config.test_name = test_name
        chat_format = user_profile.format_type
        start_time_test = timeit.default_timer()

        for i in range(user_profile.conversation_number):
            config.conversation_name = f'{i}_{test_name}_{serial}.yml'
            # the_chatbot.fallback = user_profile.fallback
            the_user = UserSimulator(user_profile)
            bot_starter = user_profile.is_starter
            response_time = []

            start_time_conversation = timeit.default_timer()
            response = ''

            if chat_format == "speech":
                from user_sim.handlers.asr_module import STTModule

                stt = STTModule(user_profile.format_config)

                def send_user_message(user_msg):
                    print_user(user_msg)
                    stt.say(user_msg)

                def get_chatbot_response(user_msg):
                    start_response_time = timeit.default_timer()
                    is_ok, response = stt.hear()
                    end_response_time = timeit.default_timer()
                    time_sec = timedelta(seconds=end_response_time - start_response_time).total_seconds()
                    response_time.append(time_sec)
                    return is_ok, response

                def get_chatbot_starter_response():
                    is_ok, response = stt.hear()
                    return is_ok, response

            else:

                if user_profile.format_config:
                    logger.warning("Chat format is text, but an SR configuration was provided. This configuration will"
                                   " be ignored.")

                def send_user_message(user_msg):
                    print_user(user_msg)

                def get_chatbot_response(user_msg):
                    start_response_time = timeit.default_timer()
                    is_ok, response = the_chatbot.execute_with_input(user_msg)
                    end_response_time = timeit.default_timer()
                    time_sec = timedelta(seconds=end_response_time - start_response_time).total_seconds()
                    response_time.append(time_sec)
                    return is_ok, response

                def get_chatbot_starter_response():
                    is_ok, response = the_chatbot.execute_starter_chatbot()
                    return is_ok, response

            start_loop = True
            if bot_starter:
                is_ok, response = get_chatbot_starter_response()
                if not is_ok:
                    if response is not None:
                        the_user.update_history("Assistant", "Error: " + response)
                    else:
                        the_user.update_history("Assistant", "Error: The server did not respond.")
                    start_loop = False
                print_chatbot(response)
                user_msg = the_user.open_conversation()
                if user_msg == "exit":
                    start_loop = False

            else:
                user_msg = the_user.open_conversation()
                if user_msg == "exit":
                    start_loop = False
                else:
                    send_user_message(user_msg)
                    is_ok, response = get_chatbot_response(user_msg)
                    if not is_ok:
                        if response is not None:
                            the_user.update_history("Assistant", "Error: " + response)
                        else:
                            the_user.update_history("Assistant", "Error: The server did not respond.")
                        start_loop = False
                    else:
                        print_chatbot(response)

            if start_loop:
                while True:
                    user_msg = the_user.get_response(response)
                    if user_msg == "exit":
                        break
                    send_user_message(user_msg)
                    is_ok, response = get_chatbot_response(user_msg)
                    if response == 'timeout':
                        break
                    print_chatbot(response)
                    if not is_ok:
                        if response is not None:
                            the_user.update_history("Assistant", "Error: " + response)
                        else:
                            the_user.update_history("Assistant", "Error: The server did not respond.")
                        break

            if output:
                end_time_conversation = timeit.default_timer()
                conversation_time = end_time_conversation - start_time_conversation
                formatted_time_conv = timedelta(seconds=conversation_time).total_seconds()
                print(f"Conversation Time: {formatted_time_conv} (s)")

                history = the_user.conversation_history
                metadata = get_conversation_metadata(user_profile, the_user, serial)
                dg_dataframe = the_user.data_gathering.gathering_register
                csv_extraction = the_user.goal_style[1] if the_user.goal_style[0] == 'all_answered' else False
                answer_validation_data = (dg_dataframe, csv_extraction)
                save_test_conv(history, metadata, test_name, output, serial,
                               formatted_time_conv, response_time, answer_validation_data, counter=i)

            config.total_individual_cost = 0
            user_profile.reset_attributes()

            if hasattr(the_chatbot, 'id'):
                the_chatbot.id = None

        end_time_test = timeit.default_timer()
        execution_time = end_time_test - start_time_test
        formatted_time = timedelta(seconds=execution_time).total_seconds()
        print(f"Execution Time: {formatted_time} (s)")
        print('------------------------------')

        if user_profile.conversation_number > 0:
            my_execution_stat.add_test_name(test_name)
            my_execution_stat.show_last_stats()

    if config.clean_cache:
        clean_temp_files()

    if output and len(my_execution_stat.test_names) == len(profiles):
        my_execution_stat.show_global_stats()
        my_execution_stat.export_stats()
    elif output:
        logger.warning("Stats export was enabled but couldn't retrieve all stats. No stats will be exported.")
    else:
        pass

    end_alarm()


def main() -> None:
    """
    Entry point of the application.

    This function sets up the configuration, then launches the
    conversation generation workflow using the provided arguments.

    Workflow:
        1. Calls `_setup_configuration()` to parse CLI arguments and
           initialize global settings.
        2. Passes the parsed arguments to `generate_conversation` to
           simulate chatbot interactions.

    Returns:
        None

    Side Effects:
        - May create output files in the configured project folder.
        - Modifies global `config` settings.
        - Logs information and potential errors to the configured logger.
    """

    args = _setup_configuration()
    # try:
    generate_conversation(
        technology=args.technology,
        connector=args.connector_params,
        user=os.path.join(config.profiles_path, args.user_profile),
        personality=None, #todo: check this
        output=args.output,
        project_folder=args.project_path
    )
    # except Exception as e:
    #     logger.error(f"An error occurred while generating the conversation: {e}")


if __name__ == '__main__':
    main()