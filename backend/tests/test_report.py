import json

from hindsight.cli import _write_report
from hindsight.config import settings
from hindsight.models import ActionPlan, TimelineEvent
from tests.conftest import make_state


def _events() -> list[TimelineEvent]:
    return [
        TimelineEvent(phase="resolve", kind="start", message="Resolving asset"),
        TimelineEvent(phase="resolve", kind="tool_call", message="search(fct_orders)"),
        TimelineEvent(phase="resolve", kind="result", message="Resolved to fct_orders"),
    ]


def test_write_report_produces_all_artifacts(tmp_path, monkeypatch):
    audit = tmp_path / "audit.jsonl"
    audit.write_text(
        json.dumps({"incident_id": "abc", "tool": "add_tags"}) + "\n"
        + json.dumps({"incident_id": "other", "tool": "add_tags"}) + "\n"
    )
    monkeypatch.setattr(settings, "audit_log_path", str(audit))

    state = make_state(
        plan=ActionPlan(postmortem_title="Incident X"), tool_calls=7, status="done"
    )
    out = tmp_path / "report"
    _write_report(state, _events(), out)

    for name in [
        "input.txt",
        "timeline.md",
        "blast-radius.md",
        "postmortem.md",
        "audit-log.json",
        "events.json",
        "state.json",
    ]:
        assert (out / name).exists()

    timeline = (out / "timeline.md").read_text()
    assert "## resolve — Resolving asset" in timeline
    assert "DataHub tool calls: 7" in timeline

    blast = (out / "blast-radius.md").read_text()
    assert "exec_revenue" in blast

    assert "# Incident X" in (out / "postmortem.md").read_text()

    records = json.loads((out / "audit-log.json").read_text())
    assert len(records) == 1
    assert records[0]["incident_id"] == "abc"
