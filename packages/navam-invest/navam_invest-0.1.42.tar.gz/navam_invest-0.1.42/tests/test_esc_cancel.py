#!/usr/bin/env python3
"""Test script to verify ESC cancellation is working."""

import asyncio
from textual.app import App
from textual.widgets import RichLog, Input
from textual.containers import Container


class TestCancelApp(App):
    """Minimal test app to verify ESC cancellation."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.cancellation_requested = False
        self.is_processing = False

    def compose(self):
        yield RichLog(id="log")
        yield Input(id="input", placeholder="Type 'test' and press Enter, then press ESC")

    def action_cancel(self):
        """Handle ESC key."""
        if self.is_processing:
            self.cancellation_requested = True
            log = self.query_one("#log", RichLog)
            log.write("[yellow]ESC pressed - cancellation requested![/yellow]")

    async def on_input_submitted(self, event):
        """Simulate long-running agent task."""
        text = event.value.strip()
        if not text:
            return

        input_widget = self.query_one("#input", Input)
        log = self.query_one("#log", RichLog)

        input_widget.value = ""
        input_widget.disabled = True
        input_widget.placeholder = "Processing... (Press ESC to cancel)"

        self.cancellation_requested = False
        self.is_processing = True

        log.write(f"[cyan]You:[/cyan] {text}")
        log.write("[green]Starting 10-second simulation...[/green]")

        try:
            # Simulate long-running task with cancellation checks
            for i in range(10):
                if self.cancellation_requested:
                    log.write("[yellow]🛑 Cancelled by user![/yellow]")
                    break

                log.write(f"[dim]Processing step {i+1}/10...[/dim]")
                await asyncio.sleep(1)
            else:
                log.write("[green]✓ Completed successfully![/green]")

        finally:
            self.is_processing = False
            input_widget.disabled = False
            input_widget.placeholder = "Type 'test' and press Enter, then press ESC"


if __name__ == "__main__":
    app = TestCancelApp()
    app.run()
