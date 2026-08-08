import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "frontend" / "public" / "recordings.json"

RECORDINGS = [
    (
        "02-cold",
        "examples/02-cold-vs-warm/cold",
        "Cold run — empty memory",
        "The catalog has never been investigated. The agent walks the lineage from scratch.",
    ),
    (
        "02-warm",
        "examples/02-cold-vs-warm/warm",
        "Warm run — the same incident, one postmortem later",
        "recall retrieves what the cold run wrote minutes earlier and steers the investigation.",
    ),
    (
        "01-schema-drift",
        "examples/01-schema-drift",
        "Schema drift upstream",
        "A migration drops a NOT NULL constraint; six prior postmortems point at the ingestion job.",
    ),
    (
        "03-orphaned-asset",
        "examples/03-orphaned-asset",
        "Governance gap",
        "A stale table nobody owns: the agent closes the gap with add_owners.",
    ),
]


def main() -> None:
    recordings = []
    for rid, source, title, blurb in RECORDINGS:
        directory = ROOT / source
        events = json.loads((directory / "events.json").read_text())
        assert any(e["phase"] == "commit" for e in events), f"{source} has no commit events"
        recordings.append(
            {
                "id": rid,
                "title": title,
                "blurb": blurb,
                "source": source,
                "events": events,
                "state": json.loads((directory / "state.json").read_text()),
            }
        )

    OUT.write_text(json.dumps(recordings, separators=(",", ":")) + "\n")
    size = OUT.stat().st_size // 1024
    print(f"Wrote {len(recordings)} recordings to {OUT.relative_to(ROOT)} ({size} KB)")


if __name__ == "__main__":
    main()
