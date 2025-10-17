#!/usr/bin/env python3
"""Test script to verify ESC cancellation with worker pattern."""

import asyncio
from textual.app import App
from textual.widgets import RichLog, Input
from textual.worker import Worker


class TestWorkerApp(App):
    """Minimal test app to verify worker-based ESC cancellation."""

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.cancellation_requested = False
        self.agent_worker = None

    def compose(self):
        yield RichLog(id="log")
        yield Input(id="input", placeholder="Type 'test' and press Enter, then press ESC")

    def action_cancel(self):
        """Handle ESC key."""
        if self.agent_worker and not self.agent_worker.is_finished:
            self.cancellation_requested = True
            log = self.query_one("#log", RichLog)
            log.write("[yellow]⚠️  ESC pressed - cancelling worker...[/yellow]")
            self.agent_worker.cancel()

    async def _simulate_long_task(self, log):
        """Simulate long-running agent task with cancellation checks."""
        try:
            for i in range(10):
                # Check for cancellation
                if self.cancellation_requested:
                    return False  # Cancelled

                log.write(f"[dim]Processing step {i+1}/10...[/dim]")
                await asyncio.sleep(1)

            return True  # Completed

        except asyncio.CancelledError:
            return False  # Cancelled

    async def on_input_submitted(self, event):
        """Simulate agent execution with worker."""
        text = event.value.strip()
        if not text:
            return

        input_widget = self.query_one("#input", Input)
        log = self.query_one("#log", RichLog)

        input_widget.value = ""
        input_widget.disabled = True
        input_widget.placeholder = "Processing... (Press ESC to cancel)"

        self.cancellation_requested = False

        log.write(f"[cyan]You:[/cyan] {text}")
        log.write("[green]Starting 10-second simulation with worker...[/green]")

        try:
            # Run in worker (non-blocking)
            self.agent_worker = self.run_worker(
                self._simulate_long_task(log),
                name="test_worker",
                group="agent",
                exclusive=True,
            )

            # Wait for completion
            completed = await self.agent_worker.wait()

            if completed:
                log.write("[green]✓ Completed successfully![/green]")
            else:
                log.write("[yellow]🛑 Cancelled by user![/yellow]")

        finally:
            input_widget.disabled = False
            input_widget.placeholder = "Type 'test' and press Enter, then press ESC"


if __name__ == "__main__":
    app = TestWorkerApp()
    app.run()
