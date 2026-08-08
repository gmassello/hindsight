from hindsight.memory.postmortem import default_title, render_markdown
from hindsight.models import ActionPlan
from tests.conftest import make_state


def test_render_contains_all_sections():
    md = render_markdown(make_state(), "Incident X")
    for fragment in [
        "# Incident X",
        "urn:li:dataset:(dbt,fct_orders,PROD)",
        "## Blast radius",
        "exec_revenue",
        "## Root cause hypotheses",
        "confidence 80%",
        "## Detection signals",
        "## Tags",
        "nulls, schema_drift_upstream",
    ]:
        assert fragment in md


def test_default_title_uses_asset_and_symptom():
    title = default_title(make_state())
    assert "fct_orders" in title
    assert "nulls" in title
    assert "2026-08-08" in title


def test_exonerated_run_is_not_documented_as_an_incident():
    state = make_state(
        verdict="exonerated",
        plan=ActionPlan(rationale="Upstream fresh, schema intact, no failed jobs."),
    )

    md = render_markdown(state, "Not an incident")

    assert "**Status**: no action required" in md
    assert "**Verdict**: exonerated" in md
    assert "## Causes ruled out" in md
    assert "Upstream fresh, schema intact, no failed jobs." in md
    assert "schema_drift_upstream" not in md.split("## Tags")[1]
    assert "Pending human confirmation." not in md


def test_exonerated_default_title_does_not_say_incident():
    assert default_title(make_state(verdict="exonerated")).startswith("Not an incident")
