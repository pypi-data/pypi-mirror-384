import configparser
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def setup_to_dict(file_path: Path, raise_error: bool = False) -> dict[str, Any]:
    """Parses a .cfg file and extracts all sections and their key-value pairs
    into a nested dictionary.

    Args:
        file_path (Path): The path to the .cfg file.
        raise_error (bool): Whether to raise an error if the file is not found.
                            Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing the parsed configuration.
                        Returns an empty dictionary if the file doesn't exist.
    """
    if not file_path.exists():
        logger.error("File %s was not found.", file_path)
        if raise_error:
            raise FileNotFoundError(f"Error: The file '{file_path}' was not found.")

    config = configparser.ConfigParser()
    try:
        config.read(file_path)
    except configparser.MissingSectionHeaderError as e:
        raise ValueError(f"Error: The file '{file_path}' is not a valid INI-style file.") from e

    # Convert the configparser object to a standard nested dictionary
    parsed_config = {section: dict(config[section]) for section in config.sections()}

    # Check if 'bumpversion' section exists and try to parse boolean values
    if "bumpversion" in parsed_config:
        try:
            # Note: configparser.getboolean() is needed for correct parsing,
            # so we'll re-read those specific keys from the original parser.
            parsed_config["bumpversion"]["tag"] = config.getboolean("bumpversion", "tag", fallback=False)
            parsed_config["bumpversion"]["commit"] = config.getboolean("bumpversion", "commit", fallback=False)
        except (ValueError, configparser.NoOptionError):
            pass  # Keep original string values if parsing fails

    return parsed_config
