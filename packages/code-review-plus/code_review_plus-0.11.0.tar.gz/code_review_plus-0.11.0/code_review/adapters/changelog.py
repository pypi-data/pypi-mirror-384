import logging
import re
from pathlib import Path

from code_review.schemas import SemanticVersion

logger = logging.getLogger(__name__)


def parse_changelog(changelog_file: Path, app_name: str, min_count: int = 2) -> list[SemanticVersion]:
    """Parses a markdown changelog and returns a list of dictionaries
    with the version and date for each entry.

    Args:
        changelog_content (str): The content of the changelog file.

    Returns:
        list: A list of dictionaries, where each dictionary contains
              the 'version' and 'date' for a changelog entry.
    """
    # Regex to find lines like "## [11.4.0] - 2025-08-28"
    # It captures the version string inside the brackets and the date
    if not changelog_file.exists():
        logger.error("File %s does not exist", changelog_file)
        return []

    with open(changelog_file, encoding="utf-8") as f:
        changelog_content = f.read()

    pattern = re.compile(r"^##\s*\[(.*?)\]\s*-\s*(.*)$", re.MULTILINE)

    # Find all matches in the changelog content
    matches = pattern.finditer(changelog_content)

    versions = []

    # Iterate through the matches and extract version and date
    for match in matches:
        version = match.group(1).strip()
        date = match.group(2).strip()
        data_dict = {"version": version, "date": date, "source": changelog_file}
        versions.append(SemanticVersion.parse_version(data_dict.get("version"), app_name, file_path=changelog_file))
    if len(versions) > min_count:
        return versions[:min_count]
    return versions
