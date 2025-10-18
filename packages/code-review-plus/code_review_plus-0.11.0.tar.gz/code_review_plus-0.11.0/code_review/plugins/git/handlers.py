import json
import logging
import re
import subprocess
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn

from code_review.exceptions import SimpleGitToolError
from code_review.plugins.git.adapters import parse_git_date
from code_review.schemas import BranchSchema
from code_review.settings import CLI_CONSOLE

logger = logging.getLogger(__name__)


def _are_there_uncommited_changes() -> bool:
    """Check if there are any committed changes in the current git repository.

    Returns:
        bool: True if there are committed changes, False otherwise.
    """
    try:
        # Run the git log command to check for commits
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        # If the output is not empty, there are committed changes
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        # If git command fails, we assume there are no committed changes
        return False


def _get_git_version() -> str:
    """Internal helper function to get the current git version.

    Returns:
        str: The version of git as a string (e.g., '2.3.4').

    Raises:
        SimpleGitToolError: If git is not installed or cannot be found.
    """
    try:
        # Run the git --version command and capture its output
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, check=True)
        # The output is typically "git version X.Y.Z", so we split to get the version number
        return result.stdout.strip().split()[-1]
    except FileNotFoundError:
        # This error occurs if the 'git' command is not found on the system
        raise SimpleGitToolError("Git is not installed or not in the system's PATH.")
    except subprocess.CalledProcessError:
        # This handles any other issues with running the command
        raise SimpleGitToolError("An unexpected error occurred while checking the git version.")


def _compare_versions(current_version: str, min_version: str) -> bool:
    """Internal helper function to compare two version strings.

    Args:
        current_version (str): The version of git currently installed.
        min_version (str): The minimum required version.

    Returns:
        bool: True if current_version is greater than or equal to min_version,
              False otherwise.
    """
    # Split the versions into a list of integers for comparison
    current_parts = [int(v) for v in re.findall(r"\d+", current_version)]
    min_parts = [int(v) for v in re.findall(r"\d+", min_version)]

    # Pad the shorter list with zeros to ensure they have the same length for comparison
    max_len = max(len(current_parts), len(min_parts))
    current_parts.extend([0] * (max_len - len(current_parts)))
    min_parts.extend([0] * (max_len - len(min_parts)))

    return tuple(current_parts) >= tuple(min_parts)


def _get_latest_tag() -> str:
    latest_tag = "No tags found"
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            check=True,
        )
        latest_tag = result.stdout.strip()
        # console.print(f"Latest tag: [bold cyan]{latest_tag}[/bold cyan]")

    except subprocess.CalledProcessError:
        # console.print("[bold yellow]No tags found in the repository.[/bold yellow]")
        pass
    return latest_tag


def get_current_git_branch() -> str:
    """Gets the currently checked out Git branch.

    This function executes a Git command to determine the name of the current
    branch. It assumes that the current working directory is inside a Git
    repository.

    Returns:
        str: The name of the currently checked out Git branch, or an empty
             string if an error occurs.
    """
    try:
        # Check if we are inside a git repository
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True, text=True)

        # Get the branch name
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            # The shell=True argument can be a security risk if the command
            # string comes from untrusted user input, but here it's
            # a hardcoded command so it's safe.
            shell=False,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")
        # Return an empty string or handle the error as appropriate
        return ""
    except FileNotFoundError:
        print("Git command not found. Please ensure Git is installed and in your system's PATH.")
        return ""


def get_branch_info(branch_name: str) -> str:
    """Retrieves the author of the most recent commit on a given Git branch."""
    try:
        # Step 1: Check if the branch exists and get its latest commit hash.
        # `check=True` will raise an exception if the command fails (e.g., branch not found).
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes the output as a string.
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_hash_result.stdout.strip()

        # Step 2: Get the author of the commit.
        # The `--pretty=format:'%an'` flag formats the output to just the author's name.
        formatting = '{"hash": "%h", "author": "%an", "email": "%ce", "date": "%ad"}'
        author_result = subprocess.run(
            ["git", "log", "-1", f"--pretty=format:{formatting}", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        return author_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # If `git rev-parse` failed, it's likely because the branch doesn't exist.
        # The stderr output usually contains "unknown revision or path not in the working tree".
        if "unknown revision" in e.stderr or "not in the working tree" in e.stderr:
            raise ValueError(f"Error: The branch '{branch_name}' does not exist.") from e
        # Re-raise the exception if the error is for another reason.
        raise e


def get_author(branch_name: str) -> str:
    """Retrieves the author of the most recent commit on a given Git branch.

    This function uses subprocess calls to execute Git commands on the local
    repository. It first checks if the branch exists and then retrieves the
    author of the last commit.

    Args:
        branch_name: The name of the Git branch (e.g., "main", "feature/my-branch").

    Returns:
        The name of the author as a string.

    Raises:
        ValueError: If the specified branch does not exist in the repository.
        subprocess.CalledProcessError: If a Git command fails for another reason
                                      (e.g., not a Git repository, Git not installed).
    """
    try:
        # Step 1: Check if the branch exists and get its latest commit hash.
        # `check=True` will raise an exception if the command fails (e.g., branch not found).
        # `capture_output=True` captures stdout and stderr.
        # `text=True` decodes the output as a string.
        commit_hash_result = subprocess.run(
            ["git", "rev-parse", branch_name],
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_hash_result.stdout.strip()

        # Step 2: Get the author of the commit.
        # The `--pretty=format:'%an'` flag formats the output to just the author's name.
        author_result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%an", commit_hash],
            capture_output=True,
            text=True,
            check=True,
        )
        return author_result.stdout.strip()

    except subprocess.CalledProcessError as e:
        # If `git rev-parse` failed, it's likely because the branch doesn't exist.
        # The stderr output usually contains "unknown revision or path not in the working tree".
        if "unknown revision" in e.stderr or "not in the working tree" in e.stderr:
            raise ValueError(f"Error: The branch '{branch_name}' does not exist.") from e
        # Re-raise the exception if the error is for another reason.
        raise e


def check_out_and_pull(branch: str, check: bool = True) -> None:
    subprocess.run(["git", "checkout", branch], check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["git", "pull", "origin", branch], check=check, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _get_merged_branches(base: str) -> list:
    result = subprocess.run(
        ["git", "branch", "-r", "--merged", base],
        capture_output=True,
        text=True,
        check=True,
    )
    # Process and display merged branches
    merged_branches = []
    for line in result.stdout.strip().split("\n"):
        branch_name = line.strip()
        if branch_name and not branch_name.startswith("*") and f"origin/{base}" not in branch_name:
            # Remove the asterisk from the current branch if present
            branch_name = branch_name.replace("* ", "")
            branch_name = branch_name.replace("origin/", "")
            merged_branches.append(branch_name)
    return merged_branches


def _get_unmerged_branches(base: str, author_pattern: str = None) -> list[BranchSchema]:
    unmerged_branches = []

    refresh_from_remote("origin")

    command_list = ["git", "branch", "-r", "--no-merged", base]
    logger.debug("Running command: %s", " ".join(command_list))
    result = subprocess.run(
        command_list,
        capture_output=True,
        text=True,
        check=True,
    )

    # Process and display unmerged branches
    try:
        for line in result.stdout.strip().split("\n"):
            clean_line = line.strip()
            logger.debug("Clean line: %s", clean_line)
            if "->" in clean_line:
                logger.warning("Found '->' in unmerged branches from '%s'", clean_line)
                continue
            branch_dict = branch_line_to_dict(clean_line)

            branch_schema = BranchSchema(**branch_dict)
            if author_pattern:
                if author_pattern.lower() in branch_schema.author.lower():
                    unmerged_branches.append(branch_schema)
            else:
                unmerged_branches.append(branch_schema)
    except ValueError as e:
        logger.error("Branch not found: %s", e)
    return sorted(unmerged_branches, reverse=True)


def branch_line_to_dict(branch_name: str) -> dict[str, Any]:
    logger.debug("Branch found: %s", branch_name)
    branch_info = get_branch_info(branch_name)
    logger.debug("Branch info: %s", branch_info)
    branch_dict = json.loads(branch_info)
    branch_dict["name"] = branch_name.replace("origin/", "")
    branch_dict["date"] = parse_git_date(branch_dict["date"])
    logger.debug("Branch info: %s", branch_dict)
    return branch_dict


def display_branches(branches: list[BranchSchema], page_size: int) -> None:
    if page_size:
        branches = branches[:page_size]
    for i, branch in enumerate(branches, 1):
        CLI_CONSOLE.print(f" {i} [yellow]{branch.name}[/yellow] {branch.date}(by [blue]{branch.author}[/blue])")


def refresh_from_remote(remote_source: str) -> None:
    try:
        subprocess.run(
            ["git", "fetch", remote_source], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        raise SimpleGitToolError(f"Could not refresh from remote '{remote_source}'")


def compare_branches(base: str, target: str, raise_error: bool = False) -> dict[str, int]:
    """Compare two branches and return how many commits one is ahead or behind the other.

    Args:
        base (str): The base branch to compare against (e.g., "master").
        target (str): The target branch to compare (e.g., "feature-branch").
    """
    status = {"ahead": -1, "behind": -1}
    try:
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", f"{base}...{target}"],
            capture_output=True,
            text=True,
            check=True,
        )
        behind_ahead = result.stdout.strip()
        behind, ahead = map(int, behind_ahead.split())
        status["ahead"] = ahead
        status["behind"] = behind
        return status
        # return f"Branch '{target}' is {ahead} commits ahead and {behind} commits behind '{base}'."
    except subprocess.CalledProcessError as e:
        logger.error("Error comparing branches: %s", e.stderr.strip())
        if raise_error:
            raise SimpleGitToolError(f"Error comparing branches: {e.stderr.strip()}") from e
        return status


def sync_branches_legacy(branches: list[str], verbose: bool = True) -> None:
    if verbose:
        CLI_CONSOLE.print("[bold blue]Syncing branches...[/bold blue]")

    refresh_from_remote("origin")
    if verbose:
        CLI_CONSOLE.print("Refreshed from remote 'origin'.")
    for branch in branches:
        if verbose:
            CLI_CONSOLE.print(f"Checking out and pulling branch: [yellow]{branch}[/yellow]")
        check_out_and_pull(branch, check=False)

def sync_branches(branches: list[str], verbose: bool = True) -> None:
    """Syncs branches with a single progress bar for both remote fetch and branch processing.
    """
    if verbose:
        CLI_CONSOLE.print("[bold blue]Starting unified branch sync process...[/bold blue]")

    # --- 1. Estimate Total Work ---
    # Give the refresh a "weight" of 1 unit of work.
    FETCH_WORK_UNIT = 1
    # Each branch sync is 1 unit of work.
    BRANCH_WORK_UNIT = 1

    total_branches = len(branches)

    # The total will be (1 unit for the fetch) + (N branches * 1 unit/branch)
    total_work = FETCH_WORK_UNIT + (total_branches * BRANCH_WORK_UNIT)

    with Progress(
            SpinnerColumn(), # Use a spinner column for dynamic status updates
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=CLI_CONSOLE,
            transient=True
    ) as progress:

        # Add a single task that covers the entire process
        main_task = progress.add_task("[cyan]Total Sync Progress[/cyan]", total=total_work)

        # ----------------------------------------------------
        # 2. Execute Refresh from Remote (The first unit of work)
        # ----------------------------------------------------
        progress.update(
            main_task,
            description="[yellow]Fetching remote changes from 'origin'[/yellow]"
        )
        refresh_from_remote("origin")

        # Advance the progress bar by the fetch work unit (1)
        progress.update(
            main_task,
            advance=FETCH_WORK_UNIT,
            description="[green]Refreshed from remote 'origin'.[/green]"
        )

        # ----------------------------------------------------
        # 3. Iterate and Sync Branches
        # ----------------------------------------------------
        for branch in branches:
            # Update the description to show the current branch being processed
            progress.update(
                main_task,
                description=f"[cyan]Syncing branch: [yellow]{branch}[/yellow][/cyan]"
            )

            # Perform the sync action
            check_out_and_pull(branch, check=False)

            # Advance the progress bar by the branch work unit (1)
            progress.advance(main_task)

    if verbose:
        CLI_CONSOLE.print("🎉 [bold green]All branches synced successfully![/bold green]")
