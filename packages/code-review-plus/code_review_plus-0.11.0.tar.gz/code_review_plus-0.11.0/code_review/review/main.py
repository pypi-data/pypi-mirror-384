from pathlib import Path

import click

from code_review.adapters.generics import parse_for_ticket
from code_review.cli import cli
from code_review.handlers.file_handlers import change_directory
from code_review.plugins.git.handlers import _get_unmerged_branches, display_branches, sync_branches, \
    _are_there_uncommited_changes
from code_review.review.adapters import build_code_review_schema
from code_review.review.handlers import display_review, write_review_to_file
from code_review.settings import CLI_CONSOLE, CURRENT_CONFIGURATION, OUTPUT_FOLDER


@cli.group()
def review() -> None:
    """Tools for code review."""
    pass


@review.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
@click.option("--author", "-a", type=str, help="Name of the author", default=None)
@click.option("--page-size", "-p", type=int, help="Page size. If zero all", default=0)
def make(folder: Path, author: str, page_size: int) -> None:
    """List branches in the specified Git repository."""
    change_directory(folder)
    CLI_CONSOLE.print(f"Changing to directory: [cyan]{folder}[/cyan]")
    uncommited_changes =_are_there_uncommited_changes()
    if uncommited_changes:
        CLI_CONSOLE.print(f"[red]You have uncommited changes, please commit or stash them before running the review.[/red]")
        return

    sync_branches(CURRENT_CONFIGURATION["default_branches"])


    unmerged_branches = _get_unmerged_branches("master", author_pattern=author)
    if not unmerged_branches:
        click.echo("No unmerged branches found.")
        return
    display_branches(unmerged_branches, page_size=page_size)
    branch_num = click.prompt("Select a branch by number", type=int)
    selected_branch = unmerged_branches[branch_num - 1]
    click.echo(f"You selected branch: {selected_branch.name}")

    code_review_schema = build_code_review_schema(folder, selected_branch.name)

    ticket_number = parse_for_ticket(selected_branch.name)

    ticket = ticket_number or click.prompt("Select a ticket by number", type=str)

    code_review_schema.ticket = ticket
    base_branch_to_check = "develop"
    if code_review_schema.target_branch.name.startswith("hotfix"):
        base_branch_to_check = "master"

    display_review(code_review_schema, base_branch_name=base_branch_to_check)

    new_file, backup_file = write_review_to_file(review=code_review_schema, folder=OUTPUT_FOLDER)
    CLI_CONSOLE.print("[bold blue]Code review written to:[/bold blue] " + str(new_file))
