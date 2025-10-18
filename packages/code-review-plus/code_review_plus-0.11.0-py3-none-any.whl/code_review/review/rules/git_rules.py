import logging

from code_review.plugins.git.adapters import is_rebased
from code_review.plugins.git.handlers import compare_branches
from code_review.review.schemas import CodeReviewSchema
from code_review.schemas import RulesResult

logger = logging.getLogger(__name__)


def validate_master_develop_sync(base_branch_name: str, target_branch_name: str) -> list[RulesResult]:
    """Validates that 'master' and 'develop' branches are included in the default branches.

    This function checks if both 'master' and 'develop' branches are present
    in the list of default branches specified in the configuration dictionary.
    It returns True if both branches are found, otherwise it returns False.

    Args:
        base_branch_name (str): The name of the default branch to check. Usually 'master'.
        target_branch_name (str): The name of the target branch to check. Usually 'develop'.

    Returns:
        bool: True if both 'master' and 'develop' are in the default branches,
              False otherwise.
    """
    rules = []
    rebased = is_rebased(target_branch_name=target_branch_name, source_branch_name=base_branch_name)

    if rebased:
        rules.append(
            RulesResult(
                name="Git",
                level="INFO",
                passed=True,
                message=f"'{base_branch_name}' and '{target_branch_name}' branches are in sync.",
            )
        )
    else:
        rules.append(
            RulesResult(
                name="Git",
                level="ERROR",
                passed=False,
                message=f"'{base_branch_name}' and '{target_branch_name}' branches are not in sync.",
            )
        )
    return rules


def validate_master_develop_sync_legacy(default_branches: list[str]) -> list[RulesResult]:
    """Validates that 'master' and 'develop' branches are included in the default branches.

    This function checks if both 'master' and 'develop' branches are present
    in the list of default branches specified in the configuration dictionary.
    It returns True if both branches are found, otherwise it returns False.

    Args:
        default_branches (list[str]): List of default branch names from the configuration.

    Returns:
        bool: True if both 'master' and 'develop' are in the default branches,
              False otherwise.
    """
    rules = []
    results = compare_branches(*default_branches)
    logger.debug("Comparison results between 'master' and 'develop': %s", results)

    if results.get("ahead") == 0 and results.get("behind") == 0:
        rules.append(
            RulesResult(
                name="Git",
                level="INFO",
                passed=True,
                message="'master' and 'develop' branches are in sync.",
            )
        )
    else:
        rules.append(
            RulesResult(
                name="Git",
                level="ERROR",
                passed=False,
                message="'master' and 'develop' branches are not in sync.",
                details=(
                    f"'master' is ahead by {results.get('ahead', 0)} commits and behind by {results.get('behind', 0)} commits compared to 'develop'."
                ),
            )
        )
    return rules


def rebase_rule(code_review_schema: CodeReviewSchema) -> list[RulesResult]:
    """Check if the target branch has been rebased onto the base branch.

    This function checks if the target branch in the provided code review schema
    has been rebased onto the base branch. It returns a list of RulesResult
    indicating whether the rebase check passed or failed.

    Args:
        code_review_schema: An instance of CodeReviewSchema containing branch information.

    Returns:
        list[RulesResult]: A list containing a single RulesResult object with the outcome of the rebase check.
    """
    rules = []
    logger.info("Checking if 'master' branch has been rebased %s.", code_review_schema.is_rebased)
    if code_review_schema.is_rebased:
        rules.append(
            RulesResult(
                name="Git Rebase Check",
                level="INFO",
                passed=True,
                message=f"Target branch '{code_review_schema.target_branch.name}' has been rebased onto base branch '{code_review_schema.source_branch_name}'.",
            )
        )
    else:
        rules.append(
            RulesResult(
                name="Git Rebase Check",
                level="ERROR",
                passed=False,
                message=f"Target branch '{code_review_schema.target_branch.name}' has NOT been rebased onto base branch '{code_review_schema.base_branch.name}'.",
            )
        )
    logger.info("Rebase rule results: %s", rules)
    return rules
