from pathlib import Path

from code_review.enums import ReviewRuleLevel
from code_review.exceptions import CodeReviewError
from code_review.plugins.gitlab.ci.handlers import handle_multi_targets
from code_review.schemas import RulesResult


def validate_ci_rules(file: Path) -> list[RulesResult]:
    """Validate GitLab CI rules in the given file.

    Args:
        file: Path to the .gitlab-ci.yml file.

    Raises:
        ValueError: If invalid rules are found.
    """
    results = []
    try:
        rules = handle_multi_targets(file.parent, file.name)
        for key, item in rules.items():
            if not isinstance(item, list):
                results.append(
                    RulesResult(
                        name="gitlab-ci",
                        passed=False,
                        level=ReviewRuleLevel.CRITICAL.value,
                        message=f"Invalid 'only' condition for job '{key}': {item}",
                    )
                )
                break
            if len(item) > 1:
                results.append(
                    RulesResult(
                        name="gitlab-ci",
                        passed=False,
                        level=ReviewRuleLevel.CRITICAL.value,
                        message=f"Multiple 'only' conditions for job '{key}': {item}",
                    )
                )
        if not results:
            return [
                RulesResult(
                    name="gitlab-ci", passed=True, level=ReviewRuleLevel.INFO.value, message="All CI rules are valid."
                )
            ]

    except CodeReviewError as e:
        results.append(RulesResult(name="gitlab-ci", passed=False, level=ReviewRuleLevel.ERROR.value, message=str(e)))
    except Exception as e:
        results.append(
            RulesResult(
                name="gitlab-ci", passed=False, level=ReviewRuleLevel.CRITICAL.value, message=f"Unexpected error: {e}"
            )
        )
    return results
