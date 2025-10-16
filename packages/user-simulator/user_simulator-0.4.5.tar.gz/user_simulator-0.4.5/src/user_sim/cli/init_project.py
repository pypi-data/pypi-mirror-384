import os
from user_sim.cli.cli import parse_init_project_arguments


def generate_untitled_name(path: str) -> str:
    """
    Generate a unique default project name inside a given path.

    Iterates over names like `Untitled_project_1`, `Untitled_project_2`, etc.,
    until it finds one that does not already exist in the target directory.

    Args:
        path (str): Directory in which to check for existing project names.

    Returns:
        str: A unique project name that does not yet exist in the directory.
    """
    i = 1
    while True:
        name = f"Untitled_project_{i}"
        full_path = os.path.join(path, name)
        if not os.path.exists(full_path):
            return name
        i += 1


def _setup_configuration() -> tuple[str, str]:
    """
    Prepare project initialization settings.

    Parses CLI arguments, determines the project name (using a generated
    default if not provided), and resolves the base path.

    Returns:
        tuple[str, str]: A tuple `(project_name, path)` where:
            - `project_name` is the provided or auto-generated name.
            - `path` is the directory where the project will be created.
    """
    args = parse_init_project_arguments()
    base_path = os.path.abspath(args.path)

    if not args.name:
        project_name = generate_untitled_name(base_path)
    else:
        project_name = args.name

    path = args.path

    return project_name, path


def make_unique_dir(path: str) -> str:
    """
    Create a new directory, ensuring the path is unique.

    If the given path already exists, appends an incremental suffix
    (e.g., `_1`, `_2`, ...) until a unique directory name is found.
    Then creates that directory.

    Args:
        path (str): Desired directory path.

    Returns:
        str: The actual path of the newly created unique directory.
    """
    base_path = path
    counter = 1

    while os.path.exists(path):
        path = f"{base_path}_{counter}"
        counter += 1

    os.makedirs(path)
    return path


def init_proj(project_name: str, path: str) -> None:
    """
       Initialize a new Sensei project folder structure.

       This function creates a new project directory with subfolders for
       profiles, rules, types, and personalities. It also generates a
       `run.yml` configuration file with basic placeholders if one does not
       already exist.

       Args:
           project_name (str): The name of the new project folder.
           path (str): The parent directory where the project will be created.

       Returns:
           None

       Side Effects:
           - Creates a unique project directory (ensuring no overwrite).
           - Creates subfolders: `profiles`, `rules`, `types`, and `personalities`.
           - Places a `PlaceDataHere.txt` file in each subfolder as a placeholder.
           - Writes a template `run.yml` configuration file if not already present.
           - Prints the path of the newly created project to stdout.

       Example:
           >>> init_proj("my_project", "./workspace")
           --- Project created at: './workspace/my_project' ---

           The resulting structure:
           ./workspace/my_project/
           ├── profiles/
           │   └── PlaceDataHere.txt
           ├── rules/
           │   └── PlaceDataHere.txt
           ├── types/
           │   └── PlaceDataHere.txt
           ├── personalities/
           │   └── PlaceDataHere.txt
           └── run.yml
       """
    project_path = os.path.join(path, project_name)
    project_path = make_unique_dir(project_path)
    run_yml_content = f"""\
project_folder: {project_name}

user_profile:
technology:
connector_params:
extract:
#execution_parameters:
    # - verbose
    # - clean_cache
    # - update_cache
    # - ignore_cache
    """

    folder_list = ["profiles", "rules", "types", "personalities"]
    for folder in folder_list:
        folder_path = os.path.join(project_path, folder)
        os.makedirs(folder_path)
        with open(f'{folder_path}/PlaceDataHere.txt', 'w') as f:
            pass

    run_yml_path = os.path.join(project_path, "run.yml")
    if not os.path.exists(run_yml_path):
        with open(run_yml_path, "w") as archivo:
            archivo.write(run_yml_content)

    print(f"--- Project created at: '{project_path}' ---")


def main() -> None:
    """
    CLI entry point for project initialization.

    Parses arguments and creates the project folder structure.
    """
    project_name, path = _setup_configuration()
    init_proj(project_name, path)


if __name__ == "__main__":
    main()
