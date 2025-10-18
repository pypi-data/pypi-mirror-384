from pathlib import Path

from code_review.plugins.gitlab.ci.rules import validate_ci_rules


class TestValidateCIRules:
    def test_valid_ci_rules(self, fixtures_folder: Path):
        ci_file_path = fixtures_folder / "gitlab-ci.yml"
        result = validate_ci_rules(ci_file_path)
        assert isinstance(result, list)
        assert all(hasattr(r, "name") for r in result)
        # Adjust the expected length and checks as needed for your fixture
        assert len(result) == 2

    def test_invalid_file_path(self, tmp_path: Path):
        invalid_file = tmp_path / "nonexistent.yml"
        result = validate_ci_rules(invalid_file)
        assert isinstance(result, list)
        assert any(r.passed is False for r in result)
