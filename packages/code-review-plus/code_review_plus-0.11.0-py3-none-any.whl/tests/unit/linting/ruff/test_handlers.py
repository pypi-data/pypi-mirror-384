from pathlib import Path

from code_review.plugins.linting.ruff.handlers import count_ruff_issues


def test_count():
    folder = Path.home() / "adelantos" / "clave-adelantos"
    c = count_ruff_issues(folder)
    assert c > 0, "Issue count should be non-negative"
