import os
from pathlib import Path

from gitignore_parser import parse_gitignore

from code_review.exceptions import SimpleGitToolError


def get_not_ignored(folder: Path, global_patten: str) -> list[Path]:
    """Finds all Dockerfiles in a given folder and its subdirectories,
    excluding those that are listed in a .gitignore file.

    Args:
        folder: The Path object for the root directory to search.
        global_patten: The glob pattern to search for Dockerfiles (e.g., "Dockerfile" or "**/Dockerfile").

    Returns:
        A list of Path objects for the Dockerfiles that are not ignored.
    """
    if not folder.is_dir():
        raise FileNotFoundError(f"The specified folder does not exist: {folder}")

    gitignore_path: Path = folder / ".gitignore"
    if gitignore_path.exists():
        matches = parse_gitignore(gitignore_path)
    else:

        def matches(x) -> bool:
            return False  # No .gitignore file, so nothing is ignored

    files_found = []
    for dockerfile_path in folder.rglob(global_patten):
        if not matches(dockerfile_path):
            files_found.append(dockerfile_path)

    return files_found


def change_directory(folder: Path) -> None:
    """Change the current working directory to the specified folder.

    Args:
        folder: The Path object for the directory to change to.
    """
    if folder:
        if not folder.exists():
            raise SimpleGitToolError(f"Directory does not exist: {folder}")
        if not folder.is_dir():
            raise SimpleGitToolError(f"Not a directory: {folder}")

        # CLI_CONSOLE.print(f"Changing to directory: [cyan]{folder}[/cyan]")
        os.chdir(folder)


def get_all_project_folder(base_folder: Path, exclusion_list: list[str] = None) -> list[Path]:
    """Get all project folders in the base folder that have a .git folder in them.

    Args:
        base_folder: The Path object for the base directory to search.
        exclusion_list: A list of folder names to exclude from the results.
    """
    if exclusion_list is None:
        exclusion_list = []
    project_folders = []
    for item in base_folder.iterdir():
        if item.is_dir() and (item / ".git").exists() and item.name not in exclusion_list:
            project_folders.append(item)
    return project_folders
