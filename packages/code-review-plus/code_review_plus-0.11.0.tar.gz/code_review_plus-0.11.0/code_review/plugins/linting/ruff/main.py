from pathlib import Path

import click

from code_review.cli import cli
from code_review.plugins.linting.ruff.handlers import _check_and_format_ruff, count_ruff_issues
from code_review.settings import CLI_CONSOLE


@cli.group()
def ruff() -> None:
    """Tools for linting and formatting."""
    pass


@ruff.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
def check(folder: Path) -> None:
    """Check and format code using ruff."""
    CLI_CONSOLE.print(f"Running ruff check on folder: {folder}")
    formatting_pending = _check_and_format_ruff(folder)
    if formatting_pending:
        CLI_CONSOLE.print("[bold red]Some files are not formatted![/bold red]")
    else:
        CLI_CONSOLE.print("[bold green]All files are formatted![/bold green]")


@ruff.command()
@click.option("--folder", "-f", type=Path, help="Path to the git repository", default=None)
def count(folder: Path) -> None:
    """Count ruff issues in the specified folder."""
    CLI_CONSOLE.print(f"Counting ruff issues in folder: {folder}")

    issue_count = count_ruff_issues(folder)
    if issue_count > -1:
        CLI_CONSOLE.print(f"[bold blue]Found {issue_count} issue(s).[/bold blue]")
    else:
        CLI_CONSOLE.print("[bold red]Failed to count issues.[/bold red]")
