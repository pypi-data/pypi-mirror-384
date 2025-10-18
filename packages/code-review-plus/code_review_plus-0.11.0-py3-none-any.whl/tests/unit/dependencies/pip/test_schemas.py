from pathlib import Path

from code_review.plugins.dependencies.pip.schemas import RequirementInfo


def test_equality() -> None:
    req1 = RequirementInfo(line="requests==2.25.1", name="requests", file=Path("requirements.txt"))
    req2 = RequirementInfo(line="requests==2.25.1", name="requests", file=Path("requirements.txt"))
    assert req1 == req2


def test_in_list() -> None:
    reqs = [RequirementInfo(line="requests==2.25.1", name="requests", file=Path("requirements.txt"))]
    req2 = RequirementInfo(line="requests==2.25.1", name="requests", file=Path("requirements.txt"))
    assert req2 in reqs
