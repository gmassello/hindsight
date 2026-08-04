from hindsight.memory.postmortem import default_title, render_markdown
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
