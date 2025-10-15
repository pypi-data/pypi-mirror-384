import os
import json
import time
import pandas as pd
from user_sim.utils.show_logs import *
import logging
from user_sim.core.role_structure import RoleData
from user_sim.utils.utilities import read_yaml
from user_sim.cli.cli import parse_validation_arguments


logger = logging.getLogger('Info Logger')


def _setup_configuration():
    args = parse_validation_arguments()

    logger = create_logger(args.verbose, 'Info Logger')
    logger.info('Logs enabled!')

    profile = args.profile
    export = args.export
    combined_matrix = args.combined_matrix

    return profile, export, combined_matrix


class ProfileValidation:
    """
    Validate a profile and export validation results.

    This class loads and validates a chatbot user profile, collects errors,
    and optionally exports combination matrices and reports for debugging
    and analysis.

    Attributes:
        profile (str): Path to the profile YAML file to validate.
        export_path (str): Path where validation reports will be saved.
        timestamp (int): Unique identifier (UNIX timestamp) for this run.
        profile_errors (list): Collected validation errors.
        error_number (int): Total number of detected errors.
        conversation_number (int): Number of conversations defined in the profile.
        combinations_dict (dict): Data about possible conversation combinations.
    """

    def __init__(self, profile: str, export_path: str) -> None:
        """
        Initialize the validator.

        Args:
            profile (str): Path to the profile YAML file.
            export_path (str): Directory where results will be exported.
        """
        self.profile = profile
        self.timestamp = int(time.time())
        self.export_path = export_path + f"/run_{self.timestamp}"
        self.profile_errors = []
        self.error_number = 0
        self.conversation_number = 0
        self.combinations_dict = {}


    def export_matrix_to_csv(self, matrix_combination: bool =False) -> None:
        """
        Export combination matrices to CSV.

        Args:
            matrix_combination (bool, optional): If True, exports a single
                combined matrix containing all results. If False, exports
                one CSV file per combination type.

        Side Effects:
            - Creates `combination_matrices/` inside the export path.
            - Writes one or more CSV files with matrix data.
            - Logs success or errors during export.
        """
        df = pd.DataFrame()
        combinations = 0

        for combinations_dict in self.combinations_dict:
            name = "_".join(combinations_dict.get('name', []))
            matrix = combinations_dict.get('matrix', [])
            func_type = combinations_dict.get("type", '')
            combinations = combinations_dict.get('combinations', 0)

            if matrix_combination:
              if df.empty:
                  df = pd.DataFrame(matrix, columns=combinations_dict.get('name'))
              else:
                  df_new = pd.DataFrame(matrix, columns=combinations_dict.get('name'))
                  df = pd.concat([df, df_new], axis=1)
                  combinations = len(df)

            else:
                filename = f"{name}_{func_type}_{combinations}_{self.timestamp}.csv"
                path = f"{self.export_path}/combination_matrices"
                filepath = f"{path}/{filename}"
                if not os.path.exists(path):
                    os.makedirs(path)
                try:
                    df = pd.DataFrame(matrix, columns=combinations_dict.get('name'))
                    df.to_csv(filepath, index=False)
                except Exception as e:
                    logger.error(f"Couldn't export matrix dataframe: {e}")
                logger.info(f"Combinations file saved as: {filepath}")

        if matrix_combination:
            filename = f"full_matrix_{combinations}_{self.timestamp}.csv"
            path = f"{self.export_path}/combination_matrices"
            filepath = f"{path}/{filename}"
            if not os.path.exists(path):
                os.makedirs(path)
            try:
                df.to_csv(filepath, index=False)
            except Exception as e:
                logger.error(f"Couldn't export matrix dataframe: {e}")
            logger.info(f"Combinations file saved as: {filepath}")


    def collect_errors(self, e: Exception, prefix: str = "", message: str | None =None) -> None:
        """
        Collect an error and store it in the profile error list.

        Args:
            e (Exception): The exception object.
            prefix (str, optional): Location or context of the error.
            message (str | None, optional): Custom error message.

        Side Effects:
            - Appends a structured error entry to `self.profile_errors`.
        """
        e_msg = f"{message}: {str(e)}" if message else str(e)
        self.profile_errors.append(
            {"field": 'unknown',
             "error": e_msg,
             "type": type(e).__name__,
             "location": prefix}
        )


    def validate(self) -> None:
        """
        Validate the YAML profile.

        Attempts to parse the YAML file, build a `RoleData` object, and
        collect errors and conversation data.

        Side Effects:
            - Updates `self.profile_errors`, `self.error_number`,
              `self.conversation_number`, and `self.combinations_dict`.
            - On parsing error, records an "Invalid YAML syntax" error.
        """
        try:
            profile = read_yaml(self.profile)
            user_profile = RoleData(profile, validation=True)
            self.profile_errors, self.error_number = user_profile.get_errors()
            self.conversation_number = user_profile.conversation_number
            self.combinations_dict = user_profile.combinations_dict
        except Exception as e:
            self.collect_errors(e, "YAML_file", message="Invalid YAML syntax")


    def show_report(self, matrix_combination: bool = False) -> None:
        """
        Generate and export the validation report.

        Creates a JSON file with collected errors and their count, and
        optionally exports combination matrices.

        Args:
            matrix_combination (bool, optional): If True, exports a single
                combined matrix CSV file. If False, exports one CSV file
                per matrix. Defaults to False.

        Side Effects:
            - Creates the export directory if it does not exist.
            - Writes `errors_<timestamp>.json` with validation errors.
            - Calls `export_matrix_to_csv()` to save matrix data.
            - Logs directory creation and file export events.
        """
        if not os.path.exists(self.export_path):
            os.makedirs(self.export_path)
            logger.info(f"Validation report directory created at {self.export_path}")

        error_result = {
            "errors": self.profile_errors,
            "total_errors": self.error_number
        }

        json_result = json.dumps(error_result, indent=4, ensure_ascii=False)
        filepath = f"{self.export_path}/errors_{self.timestamp}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(json_result)

        for c_dict in self.combinations_dict:
            self.export_matrix_to_csv(matrix_combination)


def validate_profile() -> None:
    """
    Run the profile validation workflow.

    This function loads configuration arguments, validates a user profile,
    and generates a validation report.

    Workflow:
        1. Parse CLI arguments with `_setup_configuration()`.
        2. Create a `ProfileValidation` instance for the given profile.
        3. Run validation checks.
        4. Display/export the validation report.

    Returns:
        None
    """
    profile, export, combined_matrix = _setup_configuration()
    validation = ProfileValidation(profile, export)
    validation.validate()
    validation.show_report(combined_matrix)


def main() -> None:
    """
    CLI entry point for profile validation.

    Runs the profile validator workflow.
    """
    validate_profile()


if __name__ == "__main__":
    main()