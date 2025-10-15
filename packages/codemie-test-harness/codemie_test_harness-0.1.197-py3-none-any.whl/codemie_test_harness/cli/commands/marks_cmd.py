"""CLI command for listing pytest marks."""

from __future__ import annotations
import click
from ..marks_utils import discover_all_marks, print_marks_list
from ..constants import CONSOLE


@click.command(name="marks")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed information in table format with line numbers",
)
@click.option(
    "--count", "-c", is_flag=True, help="Show only the count of available marks"
)
def marks_cmd(verbose: bool, count: bool):
    """List all available pytest marks in the test suite.

    Examples:
        codemie-test-harness marks                    # List all marks
        codemie-test-harness marks --verbose          # List marks with file details in table format
        codemie-test-harness marks --count            # Show only count
    """
    try:
        if count:
            # For count mode, we don't need detailed information
            marks_info = discover_all_marks(include_details=False)
            CONSOLE.print(f"[green]{len(marks_info)}[/green] pytest marks available")
            return

        # Let print_marks_list handle the discovery with appropriate details
        print_marks_list(marks_info=None, show_files=verbose)

    except Exception as e:
        CONSOLE.print(f"[red]Error discovering marks: {str(e)}[/red]")
        raise click.ClickException("Failed to discover pytest marks")
