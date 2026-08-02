from hindsight.memory.postmortem import default_title, render_markdown
from hindsight.models import (
    BlastRadius,
    EntityRef,
    Hypothesis,
    ImpactedAsset,
    Incident,
    InvestigationState,
    ResolveResult,
)


def _state() -> InvestigationState:
    return InvestigationState(
        id="abc",
        input_text="nulls in fct_orders",
        incident=Incident(
            symptom_type="nulls",
            symptom_description="customer_id is null",
            detected_at="2026-08-08 03:00 UTC",
        ),
        resolution=ResolveResult(
            resolved_asset=EntityRef(urn="urn:li:dataset:(dbt,fct_orders,PROD)", name="fct_orders")
        ),
        blast_radius=BlastRadius(
            impacted=[
                ImpactedAsset(
                    urn="urn:li:dashboard:x", name="exec_revenue", type="dashboard",
                    hops=2, score=4.5, owners=["urn:li:corpuser:ana"],
                )
            ],
            total_score=4.5,
            owners_to_notify=["urn:li:corpuser:ana"],
        ),
        hypotheses=[
            Hypothesis(
                cause_type="schema_drift_upstream",
                statement="raw_customers dropped customer_id",
                confidence=0.8,
                evidence=["column missing in schema"],
                evidence_urns=["urn:li:dataset:(dbt,raw_customers,PROD)"],
            )
        ],
    )


def test_render_contains_all_sections():
    md = render_markdown(_state(), "Incident X")
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
    title = default_title(_state())
    assert "fct_orders" in title
    assert "nulls" in title
