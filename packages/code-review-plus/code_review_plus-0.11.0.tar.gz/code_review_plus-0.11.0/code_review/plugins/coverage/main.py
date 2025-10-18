import os
import re
from pathlib import Path


def get_minimum_coverage(file_path: Path, raise_error: bool = False) -> float:
    """Parses a Makefile from a given file path and extracts the value for the
    MINIMUM_COVERAGE variable.

    Args:
        file_path: A pathlib.Path object pointing to the Makefile.

    Returns:
        The float value of the MINIMUM_COVERAGE variable.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If MINIMUM_COVERAGE is not found in the Makefile content.
    """
    try:
        # Read the entire content of the file
        makefile_content = file_path.read_text()
    except FileNotFoundError:
        raise FileNotFoundError(f"Makefile not found at path: {file_path}")

    # Use a regular expression to find the line that defines MINIMUM_COVERAGE.
    # The regex looks for:
    # ^: Start of the line
    # \s*: Zero or more whitespace characters
    # MINIMUM_COVERAGE: The literal string
    # \s*=\s*: Equals sign surrounded by zero or more whitespace characters
    # (.*): Captures everything that follows (the value)
    # $: End of the line
    match = re.search(r"^\s*MINIMUM_COVERAGE\s*=\s*(.*)$", makefile_content, re.MULTILINE)

    if match:
        # If a match is found, return the captured group (the value).
        # We also strip any leading/trailing whitespace from the captured value.
        return float(match.group(1).strip())
    # If no match is found, raise a ValueError as requested.
    if raise_error:
        raise ValueError("MINIMUM_COVERAGE not found in the Makefile content.")
    return -1.0


def get_makefile(folder: Path) -> Path:
    """Returns the path to the Makefile in the specified folder.

    Args:
        folder: A pathlib.Path object pointing to the folder containing the Makefile.

    Returns:
        The path to the Makefile if it exists, otherwise raises FileNotFoundError.
    """
    makefile_path = folder / "Makefile"
    if not makefile_path.exists():
        makefile_path = folder / "makefile"
    if not makefile_path.exists():
        raise FileNotFoundError(f"Makefile not found in folder: {folder}")
    return makefile_path


if __name__ == "__main__":
    projects_folder = Path.home() / "adelantos"
    project_folder = projects_folder / "clave-adelantos"
    makefile_path = project_folder / "Makefile"
    try:
        minimum_coverage = get_minimum_coverage(makefile_path)
        print(f"Minimum coverage is set to: {minimum_coverage}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        os._exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        os._exit(1)
