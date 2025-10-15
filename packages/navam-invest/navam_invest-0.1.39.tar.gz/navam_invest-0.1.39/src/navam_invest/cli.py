"""Typer CLI entry point for Navam Invest."""

import asyncio

import typer
from rich.console import Console

from navam_invest.tui.app import run_tui

app = typer.Typer(
    name="navam",
    help="Navam Invest - AI-powered investment advisor",
    add_completion=False,
)
console = Console()


@app.command()
def invest() -> None:
    """Launch the interactive investment advisor chat interface."""
    console.print("[bold green]Launching Navam Invest...[/bold green]")
    asyncio.run(run_tui())


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]Navam Invest v0.1.4[/bold]")
    console.print("AI-powered investment advisor for retail investors")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Navam Invest - AI-powered investment advisor.

    Run 'navam invest' to launch the interactive interface.
    """
    if ctx.invoked_subcommand is None:
        console.print(
            "[bold cyan]Navam Invest[/bold cyan] - AI-powered investment advisor\n"
        )
        console.print("Usage: [bold]navam invest[/bold] - Launch interactive interface")
        console.print("       [bold]navam version[/bold] - Show version")
        console.print("\nRun [bold]navam --help[/bold] for more information.")


if __name__ == "__main__":
    app()
