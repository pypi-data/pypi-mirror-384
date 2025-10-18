import json
import logging
from datetime import datetime
from pathlib import Path

from code_review.enums import ReviewRuleLevelIcon
from code_review.review.schemas import CodeReviewSchema
from code_review.settings import CLI_CONSOLE

logger = logging.getLogger(__name__)


def display_review(review: CodeReviewSchema, base_branch_name: str = "develop") -> None:
    """Display the details of a code review."""
    CLI_CONSOLE.print(f"[bold blue]Code Review for Project:[/bold blue] {review.name} by {review.target_branch.author}")
    CLI_CONSOLE.print(f"[bold blue]Branch: {review.target_branch.name}[/bold blue]")
    if review.is_rebased:
        CLI_CONSOLE.print(
            f"[bold green]{ReviewRuleLevelIcon.INFO.value} Branch {review.target_branch.name} is rebased on {base_branch_name}.[/bold green]"
        )
    else:
        CLI_CONSOLE.print(
            f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Branch {review.target_branch.name} is not rebased on {base_branch_name}![/bold red]"
        )
    # Linting comparison
    if review.target_branch.linting_errors > review.base_branch.linting_errors:
        CLI_CONSOLE.print(
            f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Linting Issues Increased![/bold red] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )
    elif (
        review.target_branch.linting_errors == review.base_branch.linting_errors
        and review.target_branch.linting_errors != 0
    ):
        CLI_CONSOLE.print(
            f"[bold yellow]{ReviewRuleLevelIcon.WARNING.value} Linting Issues Stayed the Same![/bold yellow] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )
    else:
        CLI_CONSOLE.print(
            f"[bold green]{ReviewRuleLevelIcon.INFO.value} Linting Issues Decreased or Stayed the Same.[/bold green] base has "
            f"{review.base_branch.linting_errors} while {review.target_branch.name} "
            f"has {review.target_branch.linting_errors}"
        )
    # Requirements to update
    requirements_pending_update_count = len(review.target_branch.requirements_to_update)
    if requirements_pending_update_count > 0:
        CLI_CONSOLE.print(
            f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Dependencies to Update:[/bold red] {requirements_pending_update_count} need updates."
        )
    else:
        CLI_CONSOLE.print(f"[bold green]{ReviewRuleLevelIcon.INFO.value} No Dependencies to Update![/bold green]")

    for dockerfile in review.docker_files or []:
        if dockerfile.version != dockerfile.expected_version:
            CLI_CONSOLE.print(
                f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Dockerfile {dockerfile.file.relative_to(review.source_folder)} need to be "
                f"updated {dockerfile.version} -> {dockerfile.expected_version}:[/bold red]"
            )
        else:
            CLI_CONSOLE.print(
                f"[bold green]{ReviewRuleLevelIcon.INFO.value} Dockerfile {dockerfile.file.relative_to(review.source_folder)} has "
                f"is up to date ![/bold green]"
            )

    if review.target_branch.formatting_errors != 0:
        CLI_CONSOLE.print(
            f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Code Formatting Issues Detected![/bold red] {review.target_branch.formatting_errors} files need formatting."
        )
    else:
        CLI_CONSOLE.print(f"[bold green]{ReviewRuleLevelIcon.INFO.value} All Files Properly Formatted![/bold green]")

    logger.debug("Review Details: %s", review.target_branch.changelog_versions)
    logger.debug("Review version: %s", review.target_branch.version)
    print("-" * 80)
    # Rules validated
    CLI_CONSOLE.print("[bold blue]>>> Rules Validated <<<[/bold blue]")
    if review.rules_validated:
        for rule in review.rules_validated:
            if rule.passed:
                CLI_CONSOLE.print(
                    f"[bold green]{ReviewRuleLevelIcon.INFO.value} Rule Passed: {rule.name} {rule.message}[/bold green]"
                )
            else:
                CLI_CONSOLE.print(
                    f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Rule Failed: {rule.name} {rule.message}[/bold red]"
                )

    if len(review.target_branch.changelog_versions) == 0 or review.target_branch.version is None:
        logger.error("Skipping version check due to missing information")
        return

    changelog_latest_version = review.target_branch.changelog_versions[0]
    logger.debug("Latest changelog version: %s", changelog_latest_version)
    if review.target_branch.version < changelog_latest_version:
        CLI_CONSOLE.print(
            f"[bold green]{ReviewRuleLevelIcon.INFO.value} Versioning is correct expected to move from {review.target_branch.version} "
            f"to {changelog_latest_version}![/bold green] "
        )
    else:
        CLI_CONSOLE.print(
            f"[bold red]{ReviewRuleLevelIcon.ERROR.value} Versioning is not correct expected to move from {review.target_branch.version} "
            f"to {changelog_latest_version}![/bold red] "
        )


def write_review_to_file(review: CodeReviewSchema, folder: Path) -> tuple[Path, Path | None]:
    """Write the code review details to a JSON file."""
    dated_folder = folder / "code_reviews" / datetime.now().strftime("%Y-%m-%d")
    dated_folder.mkdir(parents=True, exist_ok=True)
    file = dated_folder / f"{review.ticket}-{review.name}_code_review.json"
    backup_file = None
    if file.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_file = dated_folder / f"{review.ticket}-{review.name}_code_review_{timestamp}.json"
        file.rename(backup_file)

    with open(file, "w") as f:
        json.dump(review.model_dump(), f, indent=4, default=str)

    return file, backup_file
