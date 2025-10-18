import re

from code_review.plugins.docker.docker_hub.schemas import ImageTag


def include_by_regex(tag: ImageTag, regex: str) -> bool:
    """Check if the image name matches the given regex pattern."""
    regexp = re.compile(regex)
    match = regexp.match(tag.name)
    return bool(match)
