from hindsight.datahub.lineage import build_blast_radius, impact_score, type_weight
from hindsight.models import ConsumerReport


def test_type_weight_from_type_and_urn():
    assert type_weight("Dashboard", "urn:li:dashboard:(looker,x)") == 3.0
    assert type_weight("", "urn:li:dashboard:(looker,x)") == 3.0
    assert type_weight("dataset", "urn:li:dataset:(x,y,PROD)") == 1.0
    assert type_weight("unknown", "urn:li:unknown:x") == 1.0


def test_impact_score_formula():
    score = impact_score("dashboard", "urn:li:dashboard:x", 1, True, True, True)
    assert score == round(3.0 / 2 * 1.5 * 2.0 * 1.3, 2)
    assert impact_score("dataset", "urn:li:dataset:x", 0, False, False, False) == 1.0


def test_build_blast_radius_orders_and_dedupes_owners():
    blast = build_blast_radius(
        [
            ConsumerReport(urn="urn:li:dataset:a", type="dataset", hops=1, owners=["u1"]),
            ConsumerReport(
                urn="urn:li:dashboard:b",
                type="dashboard",
                hops=2,
                owners=["u1", "u2"],
                is_critical=True,
            ),
        ]
    )
    assert blast.impacted[0].urn == "urn:li:dashboard:b"
    assert blast.owners_to_notify == ["u1", "u2"]
    assert blast.total_score == round(sum(a.score for a in blast.impacted), 2)


def test_build_blast_radius_dedupes_consumers_by_urn():
    dashboard = "urn:li:dashboard:b"
    blast = build_blast_radius(
        [
            ConsumerReport(urn=dashboard, type="dashboard", hops=3),
            ConsumerReport(urn=dashboard, type="dashboard", hops=2),
        ]
    )
    assert len(blast.impacted) == 1
    assert blast.impacted[0].hops == 2
    assert blast.total_score == impact_score("dashboard", dashboard, 2, False, False, False)
