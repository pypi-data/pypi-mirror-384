import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def parse_yaml_file(file_path: Path) -> dict[str, Any] | None:
    """Parses a YAML file and returns a Python dictionary.

    Args:
      file_path: The path to the YAML file.

    Returns:
      A dictionary representing the parsed YAML content.
    """
    try:
        with open(file_path) as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error("YAML file not found: %s", file_path)
        return None
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML file %s: %s", file_path, e)
        return None
