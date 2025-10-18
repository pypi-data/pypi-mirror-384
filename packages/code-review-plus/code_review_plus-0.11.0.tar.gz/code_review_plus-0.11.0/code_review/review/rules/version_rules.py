from code_review.schemas import BranchSchema, RulesResult


def check_change_log_version(base_branch: BranchSchema, target_branch: BranchSchema) -> list[RulesResult]:
    """Check if the target branch has a version in the changelog greater than the base branch.

    Args:
        base_branch: The base branch schema containing version information.
        target_branch: The target branch schema containing version information.

    Returns:
        True if the target branch has a greater version in the changelog, False otherwise.
    """
    rules = []
    if len(base_branch.changelog_versions) == 0:
        rules.append(
            RulesResult(
                name="Versioning",
                passed=False,
                level="WARNING",
                message=f"No versions found in the changelog of the base {base_branch.name} branch.",
            )
        )
    if len(target_branch.changelog_versions) == 0:
        rules.append(
            RulesResult(
                name="Versioning",
                passed=False,
                level="WARNING",
                message=f"No versions found in the changelog of the target {target_branch.name} branch.",
            )
        )
    if len(base_branch.changelog_versions) > 0 and len(target_branch.changelog_versions) > 0:
        if target_branch.changelog_versions[0] > base_branch.changelog_versions[0]:
            rules.append(
                RulesResult(
                    name="Versioning",
                    passed=True,
                    level="INFO",
                    message=(
                        f"Target branch {target_branch.name} has a greater version "
                        f"({target_branch.changelog_versions[0].major}."
                        f"{target_branch.changelog_versions[0].minor}."
                        f"{target_branch.changelog_versions[0].patch}) in the changelog "
                        f"than the base branch {base_branch.name} "
                        f"({base_branch.changelog_versions[0].major}."
                        f"{base_branch.changelog_versions[0].minor}."
                        f"{base_branch.changelog_versions[0].patch})."
                    ),
                )
            )
        else:
            rules.append(
                RulesResult(
                    name="Versioning",
                    passed=False,
                    level="CRITICAL",
                    message=(
                        f"Target branch {target_branch.name} does not have a greater version "
                        f"in the changelog than the base branch {base_branch.name}. "
                        f"Current versions are: "
                        f"{base_branch.name} - {base_branch.changelog_versions[0].major}."
                        f"{base_branch.changelog_versions[0].minor}."
                        f"{base_branch.changelog_versions[0].patch}, "
                        f"{target_branch.name} - {target_branch.changelog_versions[0].major}."
                        f"{target_branch.changelog_versions[0].minor}."
                        f"{target_branch.changelog_versions[0].patch}."
                    ),
                )
            )
    return rules
