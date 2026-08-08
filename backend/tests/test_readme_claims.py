import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "examples"

COVERED = {
    "01-schema-drift",
    "02-cold-vs-warm/cold",
    "02-cold-vs-warm/warm",
    "03-orphaned-asset",
    "04-skill-portability",
}


def _table_rows() -> dict[str, list[str]]:
    readme = (REPO / "README.md").read_text()
    header = "| Run | Tool calls | Consumers | Impact score | Deduped owners | `verify` |"
    assert header in readme, "the per-run results table is gone from README.md"
    body = readme.split(header, 1)[1].split("\n\n", 1)[0]

    rows = {}
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0].startswith("---"):
            continue
        rows[cells[0].strip("`")] = cells[1:]
    assert set(rows) == COVERED, f"README table rows changed: {sorted(rows)}"
    return rows


def _number(cell: str) -> float | None:
    if cell in {"—", "none"}:
        return None
    match = re.search(r"\d+(?:\.\d+)?", cell)
    return float(match.group()) if match else None


@pytest.fixture(scope="module")
def rows() -> dict[str, list[str]]:
    return _table_rows()


@pytest.mark.parametrize(
    "run", ["01-schema-drift", "02-cold-vs-warm/cold", "02-cold-vs-warm/warm", "03-orphaned-asset"]
)
def test_row_matches_state_json(rows, run):
    calls, consumers, score, owners, _ = rows[run]
    state = json.loads((EXAMPLES / run / "state.json").read_text())
    blast = state["blast_radius"] or {"impacted": [], "total_score": 0.0, "owners_to_notify": []}

    assert _number(calls) == state["tool_calls"]
    assert _number(consumers) == len(blast["impacted"])
    assert _number(score) == pytest.approx(blast["total_score"])
    assert (_number(owners) or 0) == len(blast["owners_to_notify"])


def test_skill_portability_row_matches_blast_radius(rows):
    _, consumers, score, owners, verify = rows["04-skill-portability"]
    text = (EXAMPLES / "04-skill-portability" / "blast-radius.md").read_text()

    assert _number(score) == pytest.approx(float(re.search(r"Total score: ([\d.]+)", text).group(1)))
    listed = re.search(r"Owners to notify: (.+)", text).group(1)
    assert _number(owners) == len({o.strip() for o in listed.split(",")})
    table = [line for line in text.splitlines() if line.startswith("|")]
    assert _number(consumers) == len(table) - 2
    assert verify == "—", "04-skill-portability has no verify.txt; the cell must stay a dash"


@pytest.mark.parametrize(
    "run", ["01-schema-drift", "02-cold-vs-warm/cold", "02-cold-vs-warm/warm", "03-orphaned-asset"]
)
def test_verify_column_matches_verify_txt(rows, run):
    claimed = rows[run][4].strip("`")
    actual = (EXAMPLES / run / "verify.txt").read_text().strip().splitlines()[-1]
    assert claimed == actual


def test_headline_cold_vs_warm_claim():
    readme = (REPO / "README.md").read_text()
    cold = json.loads((EXAMPLES / "02-cold-vs-warm/cold/state.json").read_text())["tool_calls"]
    warm = json.loads((EXAMPLES / "02-cold-vs-warm/warm/state.json").read_text())["tool_calls"]

    assert f"{cold} tool calls cold and {warm} warm" in readme
    assert f"{cold} tool calls cold vs. {warm} warm" in readme
    assert f"{round((cold - warm) / cold * 100)}% fewer calls" in readme
