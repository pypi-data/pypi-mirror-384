from code_review.plugins.docker.docker_hub.schemas import ImageTag


def exclude_by_content(tag: ImageTag, exclusion_criteria: list[str]) -> bool:
    """Exclude images based on specific content criteria."""
    return any(criterion in tag.name for criterion in exclusion_criteria)
