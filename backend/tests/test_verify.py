import json

import pytest
from typer.testing import CliRunner

from hindsight.cli import _write_report, app
from hindsight.config import settings
from hindsight.datahub.graphql_fallback import GraphQLError, run_fallback
from hindsight.safety.verify import check_record
from tests.conftest import make_state

runner = CliRunner()

URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,db.schema.orders,PROD)"
TAG_RECORD = {"tool": "add_tags", "urn": URN, "args": {"tag_urns": ["hindsight-degraded"]}}

APPLIED = {
    "description": "before\n## Incident Report\nnulls in customer_id",
    "tags": ["urn:li:tag:hindsight-degraded"],
    "owners": ["urn:li:corpGroup:data-platform"],
    "domain": "urn:li:domain:sales",
}


@pytest.fixture
def facets(monkeypatch):
    def install(response: dict) -> None:
        monkeypatch.setattr("hindsight.safety.verify.entity_facets", lambda urn: response)

    return install


def test_check_record_confirms_every_target(facets):
    facets(APPLIED)
    record = {
        "tool": "add_tags",
        "urn": URN,
        "args": {"entity_urns": [URN, "urn:li:dashboard:(looker,42)"], "tag_urns": ["hindsight-degraded"]},
    }

    checks = check_record(record)

    assert len(checks) == 2
    assert all(ok for ok, _ in checks)


def test_check_record_detects_a_missing_banner(facets):
    facets({**APPLIED, "description": "someone overwrote this"})
    record = {
        "tool": "update_description",
        "urn": URN,
        "args": {"entity_urn": URN, "description": "## Incident Report"},
    }

    (ok, label) = check_record(record)[0]

    assert not ok
    assert "incident banner" in label


def test_check_record_flags_an_unknown_tool(facets):
    facets(APPLIED)

    (ok, label) = check_record({"tool": "add_glossary_terms", "urn": URN, "args": {}})[0]

    assert not ok
    assert "no verification implemented" in label


def _report(tmp_path, monkeypatch, records: list[dict]):
    audit = tmp_path / "audit.jsonl"
    audit.write_text("".join(json.dumps({"incident_id": "abc", **r}) + "\n" for r in records))
    monkeypatch.setattr(settings, "audit_log_path", str(audit))

    out = tmp_path / "report"
    _write_report(make_state(status="done"), [], out)
    return out


def test_verify_passes_when_everything_landed(tmp_path, monkeypatch, facets):
    facets(APPLIED)
    out = _report(tmp_path, monkeypatch, [TAG_RECORD])

    result = runner.invoke(app, ["verify", str(out)])

    assert result.exit_code == 0
    assert "verified 1/1" in result.stdout
    assert "verified 1/1" in (out / "verify.txt").read_text()


def test_verify_exits_nonzero_when_a_mutation_is_gone(tmp_path, monkeypatch, facets):
    facets({**APPLIED, "tags": []})
    out = _report(tmp_path, monkeypatch, [TAG_RECORD])

    result = runner.invoke(app, ["verify", str(out)])

    assert result.exit_code == 1
    assert "verified 0/1" in result.stdout


def test_verify_without_audit_log_fails(tmp_path):
    result = runner.invoke(app, ["verify", str(tmp_path)])

    assert result.exit_code == 1
    assert "No audit-log.json" in result.stdout


def test_run_fallback_without_a_target_raises(monkeypatch):
    written: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        "hindsight.datahub.graphql_fallback.add_tags",
        lambda urn, tags: written.append((urn, tags)),
    )
    args = {"tag_urns": ["hindsight-degraded"]}

    with pytest.raises(GraphQLError):
        run_fallback("add_tags", args)
    assert written == []

    run_fallback("add_tags", args, URN)
    assert written == [(URN, ["hindsight-degraded"])]
