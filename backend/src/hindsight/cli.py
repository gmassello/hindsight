import asyncio

import typer
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from hindsight.agent.context import Ctx
from hindsight.agent.orchestrator import commit_and_learn
from hindsight.agent.orchestrator import investigate as run_investigation
from hindsight.config import settings
from hindsight.datahub.mcp_client import DataHubMCP
from hindsight.models import InvestigationState, TimelineEvent
from hindsight.safety.dry_run import render_plan

app = typer.Typer(add_completion=False)
console = Console()

STYLES = {
    "start": ("bold cyan", "▶"),
    "info": ("white", "·"),
    "tool_call": ("dim", "⚙"),
    "warning": ("yellow", "⚠"),
    "error": ("red", "✖"),
    "result": ("green", "✔"),
}


def _print_event(event: TimelineEvent) -> None:
    style, icon = STYLES.get(event.kind, ("white", "·"))
    indent = "" if event.kind == "start" else "  "
    label = f"[{event.phase}] " if event.kind == "start" else ""
    console.print(f"{indent}{icon} {label}{event.message}", style=style, highlight=False)


async def _run(text: str, auto_approve: bool) -> int:
    state = InvestigationState.new(text)
    async with DataHubMCP() as datahub:
        ctx = Ctx(state=state, datahub=datahub)
        async for event in run_investigation(ctx):
            _print_event(event)
        if state.status == "failed":
            console.print("\nInvestigation failed.", style="bold red")
            return 1

        console.print()
        console.print(Panel(render_plan(state.plan), title="Action plan", border_style="cyan"))
        approved = auto_approve or settings.hindsight_auto_approve
        if not approved:
            approved = Confirm.ask("Apply these changes to DataHub?", default=False)
        if not approved:
            state.status = "rejected"
            console.print("Plan rejected. Nothing was written to DataHub.", style="yellow")
            return 0

        console.print()
        async for event in commit_and_learn(ctx):
            _print_event(event)

    console.print()
    console.print(
        f"Done. Status: {state.status}. DataHub tool calls used: {state.tool_calls}.",
        style="bold",
    )
    return 0 if state.status in {"done", "rejected"} else 1


@app.command()
def investigate(
    text: str = typer.Argument(..., help="Free-text incident report or alert JSON"),
    auto_approve: bool = typer.Option(
        False, "--auto-approve", help="Skip the human gate and apply the plan directly"
    ),
) -> None:
    raise typer.Exit(asyncio.run(_run(text, auto_approve)))


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    uvicorn.run("hindsight.api.main:app", host=host, port=port)


if __name__ == "__main__":
    app()
