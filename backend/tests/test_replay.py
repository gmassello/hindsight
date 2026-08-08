from typer.testing import CliRunner

from hindsight.cli import _write_report, app
from hindsight.models import ActionPlan, Mutation, TimelineEvent
from tests.conftest import make_state

runner = CliRunner()


def test_replay_reprints_a_recorded_run(tmp_path):
    state = make_state(
        plan=ActionPlan(
            mutations=[
                Mutation(
                    tool="add_tags",
                    urn="urn:li:dataset:(dbt,fct_orders,PROD)",
                    args={"tag_urns": ["urn:li:tag:hindsight-degraded"]},
                    rationale="the source of the nulls",
                )
            ],
            postmortem_title="Incident X",
        ),
        tool_calls=17,
        status="done",
    )
    events = [
        TimelineEvent(phase="resolve", kind="start", message="Resolving asset"),
        TimelineEvent(phase="resolve", kind="result", message="Resolved to fct_orders"),
    ]
    out = tmp_path / "report"
    _write_report(state, events, out)

    result = runner.invoke(app, ["replay", str(out)])

    assert result.exit_code == 0
    assert "Resolved to fct_orders" in result.stdout
    assert "add_tags" in result.stdout
    assert "Incident X" in result.stdout
    assert "17" in result.stdout


def test_replay_without_events_fails(tmp_path):
    result = runner.invoke(app, ["replay", str(tmp_path)])

    assert result.exit_code == 1
    assert "No events.json" in result.stdout
