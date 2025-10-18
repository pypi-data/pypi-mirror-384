from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from code_review.settings import BANNER, CLI_CONSOLE, TAGLINE


def show_banner() -> None:
    """Display the ASCII art banner."""
    # Create gradient effect with different colors
    banner_lines = BANNER.strip().split("\n")
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    CLI_CONSOLE.print(Align.center(styled_banner))
    CLI_CONSOLE.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))


def display_about_table() -> None:
    from code_review import __version__ as c
    from code_review.config import CONFIG_MANAGER

    table = Table.grid(padding=(0, 2))
    table.add_column(
        style="cyan",
        justify="left",
    )
    table.add_column(style="white", justify="left")

    table.add_row("Version:", c)
    table.add_row("Configuration:", str(CONFIG_MANAGER.config_file))
    # table.add_row("Configuration file:", )
    centered_table = Align.center(table)

    panel = Panel(centered_table, title="", subtitle="", expand=False)
    CLI_CONSOLE.print(Align.center(panel))
