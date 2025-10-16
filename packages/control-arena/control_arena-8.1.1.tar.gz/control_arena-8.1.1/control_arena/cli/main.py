"""Main CLI entry point for ControlArena."""

import logging
import sys

import click
from inspect_ai._util.dotenv import init_dotenv
from rich.console import Console

from control_arena.cli.env_manager_cli import cli as env_commands
from control_arena.cli.monitor_eval_cli import monitor as monitor_commands
from control_arena.cli.single_eval_cli import cli as eval_commands
from control_arena.cli.solution_viewer_cli import (
    view_solution as solution_viewer_command,
)
from control_arena.cli.trajectory_export_cli import trajectory as trajectory_commands

logger = logging.getLogger(__name__)
console = Console()


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def cli(ctx: click.Context):
    """ControlArena command line tools."""
    # Set up logging - use minimal format since we have rich for interactive display
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # if this was a subcommand then allow it to execute
    if ctx.invoked_subcommand is not None:
        return

    console.print(
        "[bold blue]ControlArena[/] - Settings and control protocols for agent evaluation",
        style="green",
    )
    click.echo(ctx.get_help())
    ctx.exit()


# Add command groups
cli.add_command(env_commands, name="env")
cli.add_command(eval_commands, name="eval")
cli.add_command(monitor_commands, name="monitor")
cli.add_command(trajectory_commands, name="trajectory")
cli.add_command(solution_viewer_command, name="solution-viewer")


def main():
    """Run the CLI."""
    init_dotenv()
    try:
        cli(auto_envvar_prefix="CA")
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/]")
        sys.exit(1)
    except Exception as e:
        import traceback

        console.print(f"\n[bold red]Error:[/] {str(e)}")
        console.print("\n[dim]Full traceback:[/]")
        console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
