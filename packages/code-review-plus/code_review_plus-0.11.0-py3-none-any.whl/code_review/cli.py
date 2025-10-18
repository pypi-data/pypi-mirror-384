import click

from code_review.handlers.display_handlers import display_about_table, show_banner


@click.group()
def cli() -> None:
    """A simple command-line tool for code review operations."""
    pass


@cli.command()
def about() -> None:
    """About the CLI."""
    show_banner()
    display_about_table()
