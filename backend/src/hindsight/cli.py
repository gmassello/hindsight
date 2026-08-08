import asyncio
import json
from pathlib import Path

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
from hindsight.memory.postmortem import blast_table, postmortem_title, render_markdown
from hindsight.models import ActionPlan, InvestigationState, TimelineEvent
from hindsight.safety.audit_log import records_for
from hindsight.safety.dry_run import render_plan
from hindsight.safety.verify import Check, check_postmortem, check_record, render_checks

app = typer.Typer(add_completion=False)
console = Console()

REPORT_OPTION = typer.Option(
    None, "--report", help="Write investigation artifacts to this directory"
)

REPLAY_ARGUMENT = typer.Argument(..., help="Report directory written by --report")

VERIFY_ARGUMENT = typer.Argument(..., help="Report directory to re-check against DataHub")

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


def _write_report(state: InvestigationState, events: list[TimelineEvent], path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "input.txt").write_text(state.input_text + "\n")

    timeline: list[str] = [f"# Investigation {state.id}"]
    for event in events:
        if event.kind == "start":
            timeline.append("")
            timeline.append(f"## {event.phase} — {event.message}")
        else:
            timeline.append(f"- {event.kind}: {event.message}")
    timeline.append("")
    timeline.append(f"Status: {state.status} · DataHub tool calls: {state.tool_calls}")
    (path / "timeline.md").write_text("\n".join(timeline) + "\n")

    blast = ["# Blast radius", ""]
    if state.blast_radius and state.blast_radius.impacted:
        radius = state.blast_radius
        blast.append(f"Total score: {radius.total_score}")
        blast.append(f"Owners to notify: {', '.join(radius.owners_to_notify) or 'none'}")
        blast.append("")
        blast.extend(blast_table(radius, owners=True))
    else:
        blast.append("No blast radius computed.")
    (path / "blast-radius.md").write_text("\n".join(blast) + "\n")

    title = postmortem_title(state)
    (path / "postmortem.md").write_text(render_markdown(state, title) + "\n")

    (path / "audit-log.json").write_text(json.dumps(records_for(state.id), indent=2) + "\n")

    (path / "events.json").write_text(
        json.dumps([e.model_dump(mode="json") for e in events], indent=2) + "\n"
    )
    (path / "state.json").write_text(state.model_dump_json(indent=2) + "\n")


async def _run(state: InvestigationState, events: list[TimelineEvent], auto_approve: bool) -> int:
    async with DataHubMCP() as datahub:
        ctx = Ctx(state=state, datahub=datahub)
        async for event in run_investigation(ctx):
            events.append(event)
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
            events.append(event)
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
    report: Path | None = REPORT_OPTION,
) -> None:
    state = InvestigationState.new(text)
    events: list[TimelineEvent] = []
    try:
        code = asyncio.run(_run(state, events, auto_approve))
    finally:
        if report:
            _write_report(state, events, report)
            console.print(f"\nReport written to {report}", style="dim")
    raise typer.Exit(code)


@app.command()
def replay(
    directory: Path = REPLAY_ARGUMENT,
) -> None:
    events_file = directory / "events.json"
    if not events_file.exists():
        console.print(f"No events.json in {directory}", style="red")
        raise typer.Exit(1)

    for raw in json.loads(events_file.read_text()):
        _print_event(TimelineEvent.model_validate(raw))

    state = InvestigationState.model_validate_json((directory / "state.json").read_text())
    console.print()
    console.print(
        Panel(render_plan(state.plan or ActionPlan()), title="Action plan", border_style="cyan")
    )
    console.print(
        f"Status: {state.status}. DataHub tool calls used: {state.tool_calls}.", style="bold"
    )


@app.command()
def verify(
    directory: Path = VERIFY_ARGUMENT,
) -> None:
    audit_file = directory / "audit-log.json"
    if not audit_file.exists():
        console.print(f"No audit-log.json in {directory}", style="red")
        raise typer.Exit(1)

    state = InvestigationState.model_validate_json((directory / "state.json").read_text())
    checks: list[Check] = []
    for record in json.loads(audit_file.read_text()):
        checks.extend(check_record(record))

    if state.postmortem_ref and state.resolution:
        checks.append(check_postmortem(state.postmortem_ref, state.resolution.resolved_asset.urn))

    for ok, label in checks:
        console.print(f"  {'✔' if ok else '✖'} {label}", style="green" if ok else "red")
    (directory / "verify.txt").write_text(render_checks(directory.name, checks))

    passed = sum(1 for ok, _ in checks if ok)
    all_ok = bool(checks) and passed == len(checks)
    console.print()
    console.print(f"verified {passed}/{len(checks)}", style="bold green" if all_ok else "bold red")
    raise typer.Exit(0 if all_ok else 1)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1"),
    port: int = typer.Option(8000),
) -> None:
    uvicorn.run("hindsight.api.main:app", host=host, port=port)


if __name__ == "__main__":
    app()
