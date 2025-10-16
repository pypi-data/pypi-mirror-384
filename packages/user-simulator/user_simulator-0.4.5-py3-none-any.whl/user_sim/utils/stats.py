import os
import yaml
import pandas as pd
from typing import Any
from user_sim.utils import config
from user_sim.utils.utilities import get_encoding
import logging
logger = logging.getLogger('Info Logger')


def get_error_stats(error_df: pd.DataFrame) -> list[dict]:
    """
    Generate a summary report of errors from a DataFrame of error logs.

    This function groups errors by their error code and counts their occurrences,
    also listing the conversations where each error appeared.

    Args:
        error_df (pd.DataFrame): A DataFrame containing at least the following columns:
            - 'error_code' (int or str): Identifier of the error.
            - 'conversation' (str or int): Identifier of the conversation where the error occurred.

    Returns:
        list[dict]: A list of dictionaries, where each dictionary contains:
            - 'error' (int or str): The error code.
            - 'count' (int): Number of times the error occurred.
            - 'conversations' (list): List of conversation identifiers where the error was found.
    """
    error_list = error_df['error_code'].unique()

    error_report = []
    for error in error_list:
        error_report.append({'error': error,
                             'count': error_df[error_df['error_code'] == error].shape[0],
                             'conversations': list(error_df[error_df['error_code'] == error]['conversation'])
                             })

    return error_report


def get_time_stats(response_time: Any) -> dict:
    """
    Compute descriptive statistics (average, maximum, minimum) for response times.

    This function takes a sequence of response times in seconds, converts them into
    pandas Timedelta objects, and calculates the average, maximum, and minimum values
    in seconds with six decimal places of precision.

    Args:
        response_time (list[float] or pd.Series): A list or pandas Series of response
            times in seconds.

    Returns:
        dict: A dictionary with the following keys:
            - 'average' (float): The mean response time in seconds.
            - 'max' (float): The maximum response time in seconds.
            - 'min' (float): The minimum response time in seconds.
    """
    times = pd.to_timedelta(response_time, unit='s')

    time_report = {
        'average': round(times.mean().total_seconds(), 6),
        'max': round(times.max().total_seconds(), 6),
        'min': round(times.min().total_seconds(), 6)
    }
    return time_report


def save_test_conv(
        history: dict,
        metadata: dict,
        test_name: str,
        path: str,
        serial: str,
        conversation_time: float,
        response_time: list[float],
        av_data: tuple,
        counter: int
) -> None:
    """
    Save the results of a chatbot test conversation, including metadata,
    timing information, conversation history, and optionally verification data.

    The function creates a dedicated folder structure for the test output,
    then exports the data both as a YAML file (for structured logging) and
    optionally as a CSV file (if verification data is available).

    Args:
        history (dict): The full conversation history between user and assistant.
        metadata (dict): Test metadata such as user profile, configuration, etc.
        test_name (str): Name of the test case or scenario.
        path (str): Root directory where results will be stored.
        serial (str): Unique identifier (timestamp-based serial) for the test run.
        conversation_time (float): Total duration of the conversation in seconds.
        response_time (list[float]): List of assistant response times for each turn.
        av_data (tuple): A tuple where:
            - av_data[0] (pd.DataFrame): Verification/data gathering results.
            - av_data[1] (bool): Whether the DataFrame should be saved.
        counter (int): Conversation index (for multiple runs in the same test).

    Side Effects:
        - Creates folders in the specified path if they do not exist.
        - Writes a `.yml` file containing metadata, timing, and conversation history.
        - Optionally writes a `.csv` file with assistant verification/data results.
        - Clears the `config.errors` list after saving.
    """
    print("Saving conversation...")

    cr_time = {'conversation time': conversation_time,
               'assistant response time': response_time,
               "response time report": get_time_stats(response_time)}

    path_folder = path + f"/conversation_outputs/{test_name}"
    if not os.path.exists(path_folder):
        os.makedirs(path_folder)

    data = [metadata, cr_time, history]
    test_folder = path_folder + f"/{serial}"

    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    file_path_yaml = os.path.join(test_folder, f'{counter}_{test_name}_{serial}.yml')
    file_path_csv = os.path.join(test_folder, f'{counter}_{test_name}_{serial}.csv')

    with open(file_path_yaml, "w", encoding="UTF-8") as archivo:
        yaml.dump_all(data, archivo, allow_unicode=True, default_flow_style=False, sort_keys=False)
    if av_data[1]:
        av_data[0].to_csv(file_path_csv, index=True, sep=';', header=True, columns=['verification', 'data'])

    print(f"Conversation saved in {path}")
    print('------------------------------')
    config.errors.clear()


class ExecutionStats:
    """
    Collects, analyzes, and exports execution statistics for chatbot test cases.

    This class processes test case outputs (YAML files), extracts assistant
    response times, errors, and costs, and provides utilities to display or export
    both per-test and global statistics. It is mainly used for benchmarking and
    reporting chatbot performance during simulations.

    Attributes:
        path (str): Root folder containing test case outputs.
        test_names (list[str]): List of test case names to analyze.
        serial (str): Serial identifier for the current execution.
        export (bool): Flag indicating whether stats have been exported.
        profile_art (list[list[float]]): Collected assistant response times per test case.
        profile_edf (list[pd.DataFrame]): Collected error DataFrames per test case.
        global_time_stats (list[float]): Combined response times across all tests.
        global_error_stats (pd.DataFrame): Combined error statistics across all tests.
    """

    def __init__(self, test_cases_folder: str, serial: str) -> None:

        self.path = test_cases_folder
        self.test_names = []
        self.serial = serial
        self.export = False
        self.profile_art = []
        self.profile_edf = []
        self.global_time_stats = []
        self.global_error_stats = None

    def add_test_name(self, test_name: str) -> None:
        """
        Add one or multiple test names to the list of tracked test cases.

        Args:
            test_name (str or list[str]): Name(s) of the test case(s) to add.
        """
        if isinstance(test_name, str):
            self.test_names.append(test_name)
        elif isinstance(test_name, list):
            self.test_names += test_name

    def reset(self) -> None:
        """
        Reset tracked test names and export flag.
        """
        self.test_names = []
        self.export = False

    def get_stats(self) -> None:
        """
        Collect statistics for the most recently added test case.

        Reads YAML conversation output files, extracts assistant response times,
        and builds error reports, storing results into `profile_art` and `profile_edf`.
        """
        path_folder = self.path + f"/conversation_outputs/{self.test_names[-1]}" + f"/{self.serial}" # todo: except for empty test_names list

        assistant_response_times = []
        error_df = pd.DataFrame(columns=["conversation", "error_code"])

        for file in os.listdir(path_folder):
            if file.endswith(('.yaml', '.yml')):
                file_path = os.path.join(path_folder, file)
                file_name = file
                with open(file_path, 'r', encoding='utf-8') as yaml_file:
                    try:
                        yaml_content = list(yaml.safe_load_all(yaml_file))
                        if "assistant response time" in yaml_content[1]:
                            assistant_response_times += yaml_content[1]['assistant response time']

                        if "errors" in yaml_content[0] and 'serial' in yaml_content[0]:
                            for error in yaml_content[0]['errors']:

                                error_df = pd.concat(
                                    [error_df, pd.DataFrame({'conversation': [file_name],
                                                             'error_code': list(error.keys())})],
                                    ignore_index=True
                                )
                    except yaml.YAMLError as e:
                        print(f'error while processing the file {yaml_file}: {e}')

        self.profile_art.append(assistant_response_times)
        self.profile_edf.append(error_df)

    def show_last_stats(self) -> None:
        """
        Display statistics for the last processed test case.

        Shows assistant response time statistics, error statistics, and total cost.
        """
        cost_ds = pd.read_csv(config.cost_ds_path, encoding=get_encoding(config.cost_ds_path)["encoding"])
        self.get_stats()

        time_stats = get_time_stats(self.profile_art[-1])
        print(f"Average assistant response time: {time_stats['average']} (s)")
        print(f"Maximum assistant response time: {time_stats['max']} (s)")
        print(f"Minimum assistant response time: {time_stats['min']} (s)")

        error_stats = get_error_stats(self.profile_edf[-1])
        for error in error_stats:
            print(f"Found error {error['error']}: \n "
                  f"- Count: {error['count']} \n "
                  f"- Conversations: {error['conversations']}")

        total_cost = round(float(cost_ds[cost_ds["Test Name"] == config.test_name]["Total Cost"].sum()), 8)
        print(f"Total Cost: ${total_cost}")

        print('------------------------------\n'
              '------------------------------')

    def show_global_stats(self) -> None:
        """
        Display statistics aggregated across all processed test cases.

        Shows assistant response time statistics, error statistics, and total cost.
        """
        cost_ds = pd.read_csv(config.cost_ds_path, encoding=get_encoding(config.cost_ds_path)["encoding"])
        self.global_time_stats = [time for profile in self.profile_art for time in profile]
        self.global_error_stats = pd.concat(self.profile_edf, ignore_index=True)

        time_stats = get_time_stats(self.global_time_stats)
        print(f"Average assistant response time: {time_stats['average']} (s)")
        print(f"Maximum assistant response time: {time_stats['max']} (s)")
        print(f"Minimum assistant response time: {time_stats['min']} (s)")

        error_stats = get_error_stats(self.global_error_stats)
        for error in error_stats:
            print(f"Found error {error['error']}: \n "
                  f"- Count: {error['count']} \n "
                  f"- Conversations: {error['conversations']}")

        total_cost = round(float(cost_ds["Total Cost"].sum()), 8)
        print(f"Total Cost: ${total_cost}")

        print('------------------------------\n'
              '------------------------------')

    def export_stats(self) -> None:
        """
        Export collected statistics to a YAML report.

        Generates both per-test reports and a global report, including:
        - Assistant response times
        - Errors
        - Total cost

        The output file is saved under `reports/__stats_reports__/report_<serial>.yml`.
        """
        export_path = self.path + f"/reports/__stats_reports__"
        cost_ds = pd.read_csv(config.cost_ds_path, encoding=get_encoding(config.cost_ds_path)["encoding"])

        if not os.path.exists(export_path):
            os.makedirs(export_path)

        single_reports = []
        for index, name in enumerate(self.test_names):
            time_stats = get_time_stats(self.profile_art[index])
            error_stats = get_error_stats(self.profile_edf[index])
            total_cost = round(float(cost_ds[cost_ds["Test Name"]==name]["Total Cost"].sum()), 8)

            single_reports.append({
                "Test name": name,
                "Average assistant response time": time_stats['average'],
                "Maximum assistant response time": time_stats['max'],
                "Minimum assistant response time": time_stats['min'],
                "Errors":  error_stats,
                "Total Cost": total_cost
            })

        glb_time_stats = get_time_stats(self.global_time_stats)
        glb_error_stats = get_error_stats(self.global_error_stats)
        glb_total_cost = round(float(cost_ds["Total Cost"].sum()), 8)

        global_reports = {
            "Global report": {
                "Average assistant response time": glb_time_stats['average'],
                "Maximum assistant response time": glb_time_stats['max'],
                "Minimum assistant response time": glb_time_stats['min'],
                "Errors": glb_error_stats,
                "Total Cost": glb_total_cost
            }
        }

        export_file_name = export_path + f"/report_{self.serial}.yml"
        data = [global_reports] + single_reports

        with open(export_file_name, "w", encoding="UTF-8") as archivo:
            yaml.dump_all(data, archivo, allow_unicode=True, default_flow_style=False, sort_keys=False)
            logger.info(f"report file saved at {export_file_name}")