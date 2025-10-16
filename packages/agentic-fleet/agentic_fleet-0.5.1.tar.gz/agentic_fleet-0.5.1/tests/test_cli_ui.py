"""Integration-style tests for the console UI output and callbacks."""

import pytest
from rich.console import Console

from agenticfleet.cli.ui import AgentMessage, ConsoleUI
from agenticfleet.fleet.callbacks import ConsoleCallbacks


def _record_output(action) -> str:
    console = Console(record=True, width=80)
    ui = ConsoleUI(console=console)
    action(ui)
    return console.export_text(clear=False)


def test_log_plan_structure() -> None:
    text = _record_output(lambda ui: ui.log_plan(["fact one", "fact two"], ["step A", "step B"]))
    assert "Plan · Iteration" in text
    assert "Facts:" in text
    assert "  - fact one" in text
    assert "1. step A" in text


def test_log_progress_structure() -> None:
    text = _record_output(
        lambda ui: ui.log_progress("In progress", "researcher", "Collect sources")
    )
    assert "Progress" in text
    assert "Status      : In progress" in text
    assert "Next speaker: researcher" in text
    assert "Collect sources" in text


def test_log_agent_message_structure() -> None:
    text = _record_output(
        lambda ui: ui.log_agent_message(AgentMessage("researcher", "Line one\nLine two"))
    )
    assert "Agent · researcher" in text
    assert "Line one" in text
    assert "Line two" in text


def test_log_final_structure() -> None:
    console = Console(record=True, width=80)
    ui = ConsoleUI(console=console)
    ui.log_final("Completed output")
    text = console.export_text(clear=False)
    assert "Result" in text
    assert "Completed output" in text
    assert "Raw Output" in text
    assert "Completed output" in text


def test_log_final_with_structured_message() -> None:
    class FinalPayload:
        def __init__(self) -> None:
            self.facts = ["fact one"]
            self.plan = ["step one", "step two"]
            self.status = "satisfied"
            self.content = "Completed output"

    class FinalEvent:
        def __init__(self) -> None:
            self.message = FinalPayload()

    console = Console(record=True, width=80)
    ui = ConsoleUI(console=console)
    ui.log_final(FinalEvent())
    text = console.export_text(clear=False)
    assert "Facts" in text
    assert "fact one" in text
    assert "Plan" in text
    assert "step one" in text
    assert "Status" in text
    assert "satisfied" in text
    assert "Raw Output" in text
    assert "Completed output" in text


@pytest.mark.asyncio
async def test_agent_deltas_are_buffered(monkeypatch) -> None:
    class Delta:
        agent_name = "researcher"
        delta = "First chunk"

    class Final:
        agent_name = "researcher"
        content = "Second chunk"

    console = Console(record=True, width=80)
    ui = ConsoleUI(console=console)
    handlers = ConsoleCallbacks(ui)

    await handlers.agent_delta_callback(Delta())
    await handlers.agent_message_callback(Final())

    text = console.export_text(clear=False)
    assert text.count("First chunk") == 1
    assert "Second chunk" in text
