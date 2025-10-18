import logging
from pathlib import Path

from code_review.exceptions import CodeReviewError
from code_review.handlers.file_handlers import get_not_ignored
from code_review.yaml.adapters import parse_yaml_file

logger = logging.getLogger(__name__)


def handle_multi_targets(folder: Path, filename: str = ".gitlab-ci.yml") -> dict[str, list] | None:
    """Parse the .gitlab-ci.yml file to extract jobs with 'only' conditions.

    Args:
        folder: Project folder path.
        filename: Name of the GitLab CI configuration file.

    Returns:

    """
    files = get_not_ignored(folder, filename)
    if not files:
        raise CodeReviewError("No %s file found in the directory: %s", filename, folder)
    if len(files) > 1:
        logger.error("Multiple .gitlab-ci.yml files found in the directory: %s", folder)
        raise CodeReviewError("Multiple %s files found in the directory: %s", filename, folder)

    ci_file = files[0]
    result = parse_yaml_file(ci_file)
    data = {}
    for key, value in result.items():
        if isinstance(value, dict) and "only" in value and isinstance(value["only"], list):
            data[key] = value["only"]
    return data
