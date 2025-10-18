from pathlib import Path

from code_review.plugins.dependencies.pip.handlers import requirements_updated


def test_requirements_handler(fixtures_folder: Path) -> None:
    results = requirements_updated(fixtures_folder)
    assert len(results) > 1
