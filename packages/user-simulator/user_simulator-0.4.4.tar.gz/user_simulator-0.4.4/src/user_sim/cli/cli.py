import os
import yaml
import sys
import argparse
from argparse import Namespace
from chatbot_connectors import parse_connector_params


def _load_yaml_arguments(project_path: str) -> dict:
    """
    Load execution arguments from a `run.yml` or `run.yaml` file in a project folder.

    This function looks for a YAML configuration file inside the given
    `project_path`, parses its contents, and normalizes keys for
    compatibility with CLI argument parsing.

    Behavior:
        - If `execution_parameters` is present in the YAML, it is treated
          as a list of flags. Each entry is expanded into a dictionary
          entry with value `True`.
        - Keys containing dashes (`-`) are converted to underscores (`_`)
          to match Python attribute conventions.
        - Always adds `"project_path"` to the returned dictionary.

    Args:
        project_path (str): Path to the project directory that contains
            either `run.yml` or `run.yaml`.

    Returns:
        dict: A dictionary of normalized arguments that can be passed
        directly to `argparse.Namespace`.

    Raises:
        FileNotFoundError: If neither `run.yml` nor `run.yaml` is found
        in the provided project path.
    """
    files = os.listdir(project_path)

    run_file = next((f for f in files if f in ["run.yml", "run.yaml"]), None)

    if not run_file:
        raise FileNotFoundError(f"Couldn't find run.yml file.")

    run_yaml_path = os.path.join(project_path, run_file)

    with open(run_yaml_path, 'r', encoding='utf-8') as f:
        yaml_args = yaml.safe_load(f) or {}

        if "execution_parameters" in yaml_args:
            parameters = yaml_args.pop("execution_parameters") or []
            yaml_args.update({param: True for param in parameters})

    normalized = {}
    for k, v in yaml_args.items():
        normalized[k.replace("-", "_")] = v

    normalized["project_path"] = project_path
    return normalized


def parse_init_project_arguments(argv: list[str] | None = None) -> Namespace:
    """
    Parse command-line arguments for initializing a new project.

    This parser supports creating a new project folder structure for Sensei.
    It accepts a base directory path and an optional project name.

    Args:
        argv (list[str] | None, optional): Custom list of arguments to parse.
            If None, defaults to `sys.argv`.

    Returns:
        argparse.Namespace: A namespace object containing parsed arguments:
            - `path` (str): Directory where the project will be created.
              Defaults to the current directory (`"."`).
            - `name` (str | None): Optional name of the project. If not provided,
              the default naming scheme will be used.

    Example:
        From the command line:
            $ python -m sensei init -p ./workspace -n my_project

        Programmatically:
            >>> args = parse_init_project_arguments(["--path", "./workspace", "--name", "my_project"])
            >>> args.path
            './workspace'
            >>> args.name
            'my_project'
    """
    parser = argparse.ArgumentParser(description="Initialize Project - Creates a sensei project folder structure.")

    parser.add_argument(
        '-p',
        '--path',
        type=str,
        default='.',
        help='Directory where the project will be created (default: current directory).'
    )

    parser.add_argument(
        '-n',
        '--name',
        type=str,
        help='Name of the project (optional).'
    )

    args = parser.parse_args(argv)

    return args


def parse_validation_arguments(argv: list[str] | None = None) -> Namespace:
    """
    Parse command-line arguments for the Sensei profile validator.

    This parser configures arguments used to validate user profiles and
    export validation reports. It supports specifying the profile location,
    output directory, and verbosity/debug options.

    Args:
        argv (list[str] | None, optional): Custom list of arguments to parse.
            If None, defaults to `sys.argv`.

    Returns:
        argparse.Namespace: A namespace object containing parsed arguments:
            - `profile` (str): Directory where the profile is located.
              Defaults to the current directory (`"."`).
            - `output` (str): Directory where the validation report will be saved.
              Defaults to the current directory (`"."`).
            - `verbose` (bool): If True, enables debug/verbose output.
            - `combined_matrix` (bool): If True, generates a combined validation
              matrix (intended for debugging/analysis).

    Example:
        From the command line:
            $ python -m sensei validate --profile ./profiles --output ./reports --verbose

        Programmatically:
            >>> args = parse_validation_arguments([
            ...     "--profile", "./profiles",
            ...     "--output", "./reports",
            ...     "--verbose",
            ...     "--combined-matrix"
            ... ])
            >>> args.profile
            './profiles'
            >>> args.output
            './reports'
            >>> args.verbose
            True
            >>> args.combined_matrix
            True
    """
    parser = argparse.ArgumentParser(description='Sensei profile validator.')

    parser.add_argument(
        '--profile',
        default='.',
        help='Directory where the profile is located.')

    parser.add_argument(
        "--output",
        default='.',
        help="Directory where the report will be exported")

    parser.add_argument(
        '-v',
        '--verbose',
        action='store_true',
        help='Shows debug prints')

    parser.add_argument(
        '--combined-matrix',
        dest="combined_matrix",
        action='store_true',
        help='Shows debug prints')

    args = parser.parse_args(argv)

    return args


def parse_chat_arguments(argv: list[str] | None = None) -> Namespace:
    """
    Parse command-line arguments for the user simulator.

    This function configures an argument parser to support two modes:

    1. **YAML mode** (`--run-from-yaml`):
       - Reads configuration values from a `run.yaml` file inside a project folder.
       - Rejects additional CLI arguments if provided simultaneously.
       - Applies fallback defaults if some arguments are not specified in YAML.

    2. **CLI mode**:
       - Requires explicit arguments for technology, user profile, and connector params.
       - Accepts optional arguments for project path, output directory, verbosity,
         cache handling, and listing available connectors.

    Args:
        argv (list[str] | None, optional): Custom list of arguments to parse.
            If None, defaults to `sys.argv`.

    Returns:
        argparse.Namespace: A namespace object containing parsed arguments.
            Possible attributes include:
            - `run_from_yaml` (str | None)
            - `ignore_cache` (bool)
            - `technology` (str)
            - `connector_params` (str | None)
            - `project_path` (str | None)
            - `user_profile` (str | None)
            - `output` (str)
            - `verbose` (bool)
            - `clean_cache` (bool)
            - `update_cache` (bool)
            - `list_connector_params` (str | None)
            - `list_connectors` (bool)

    Raises:
        SystemExit: If required arguments are missing or invalid combinations
            are provided (e.g., extra arguments when using `--run-from-yaml`).

    Notes:
        - The defaults for technology and output directory are `"taskyto"`
          and `"output"` respectively.
        - Connector parameters can be passed as JSON strings or as key=value pairs.
        - When `--run-from-yaml` is used, the arguments are loaded via
          `load_yaml_arguments()`.

    Example:
        >>> args = parse_chat_arguments([
        ...     "--technology", "taskyto",
        ...     "--connector-params", "base_url=http://localhost,port=8080",
        ...     "--user-profile", "user1.yml"
        ... ])
        >>> args.technology
        'taskyto'
    """
    parser = argparse.ArgumentParser(description="User Simulator - Converses with chatbots to test capabilities.")

    default_output_dir = "output"
    default_technology = "taskyto"

    parser.add_argument(
        "-rfy",
        "--run-from-yaml",
        dest="run_from_yaml",
        type=str,
        default=None,
        help=(
             "Path to the project folder which contains run.yaml."
             "Runs Sensei with CLI arguments contained in the run.yaml file."
             "Example: --run-from-yaml /path/to/project/folder"
        ),
    )

    parser.add_argument(
        "-ic",
        "--ignore-cache",
        dest="ignore_cache",
        action="store_true",
        help="Cache is ignored during the testing process.",
    )

    parser.add_argument(
        "-t",
        "--technology",
        type=str,
        default=default_technology,
        help=f"Chatbot technology to use (default: {default_technology})",
    )

    parser.add_argument(
        "-cp",
        "--connector-params",
        dest="connector_params",
        type=str,
        help=(
            'Connector parameters as JSON string or key=value pairs separated by commas. '
            'Examples: \'{"base_url": "http://localhost", "port": 8080}\' or '
            '"base_url=http://localhost,port=8080". '
            "Use --list-connector-params <technology> to see required parameters for each connector."
        ),
    )

    parser.add_argument(
        "-pp", "--project-path",
        dest="project_path",
        type=str,
        default=None,
        help="The project path where all testing content is stored for a specific project."
    )

    parser.add_argument(
        "-up", "--user-profile",
        dest="user_profile",
        type=str,
        default=None,
        help="Name of the user profile YAML or the folder containing user profiles to use in the testing process."
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=default_output_dir,
        help=f"Output directory for results and profiles (default: {default_output_dir})",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Increase output verbosity",
    )

    parser.add_argument(
        "-cc",
        "--clean-cache",
        dest="clean_cache",
        action="store_true",
        help=f"Cache is cleaned after the testing process",
    )

    parser.add_argument(
        "-uc",
        "--update-cache",
        dest="update_cache",
        action="store_true",
        help=f"Cache is updated with new content if previous cache was saved",
    )

    #todo: implement
    parser.add_argument(
        "--list-connector-params",
        dest="list_connector_params",
        type=str,
        metavar="TECHNOLOGY",
        help="List the available parameters for a specific chatbot technology and exit",
    )

    parser.add_argument(
        "--list-connectors",
        dest="list_connectors",
        action="store_true",
        help="List all available chatbot connector technologies and exit",
    )

    args, unknown = parser.parse_known_args(argv)   # if argv, uses argv arguments

    if args.run_from_yaml:
        # Detect if the user passed other non-default options besides the YAML
        # Define here the "default" values that should NOT be considered as "user passed something extra"
        defaults_guard = {
            "technology": default_technology,
            "output": default_output_dir,
            "connector_params": None,
            "project_path": None,
            "user_profile": None,
            "verbose": False,
            "clean_cache": False,
            "ignore_cache": False,
            "update_cache": False,
            "list_connector_params": None,
            "list_connectors": False,
        }


        non_default_passed = []
        for k, default_v in defaults_guard.items():
            if k == "run_from_yaml":
                continue
            current_v = getattr(args, k, None)
            if current_v != default_v:
                non_default_passed.append(k)

        if non_default_passed or unknown:
            parser.error(
                "No other arguments can be provided when using --run-from-yaml. "
                f"Detected: {', '.join(non_default_passed + unknown)}"
            )

        yaml_args = _load_yaml_arguments(args.run_from_yaml)

        # Minimum default values if the YAML does not provide them
        yaml_defaults = {
            "technology": default_technology,
            "connector_params": None,
            "user_profile": None,
            "output": default_output_dir,
            "verbose": False,
            "clean_cache": False,
            "ignore_cache": False,
            "update_cache": False,
        }
        for k, v in yaml_defaults.items():
            yaml_args.setdefault(k, v)

        return argparse.Namespace(**yaml_args)


    # Normal CLI mode: validate required arguments
    required_args = ["technology", "user_profile", "connector_params"]
    missing = [arg for arg in required_args if getattr(args, arg) in (None, "")]
    if missing:
        parser.error(
            "The following arguments are required when not using --run-from-yaml: "
            + ", ".join(missing)
        )

    return args



