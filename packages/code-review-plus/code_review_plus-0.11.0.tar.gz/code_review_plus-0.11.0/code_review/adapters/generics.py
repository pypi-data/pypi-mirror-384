import re


def parse_for_ticket(branch_name: str) -> str | None:
    """Extracts the ticket identifier from a branch name.

    Args:
      branch_name: The name of the branch.

    Returns:
      The extracted ticket identifier or None if not found.
    """
    regex = re.compile(r"feature/(?P<ticket>[A-Za-z]+-\d+).*")
    match = regex.match(branch_name)
    if match:
        return match.group("ticket")
    return None
