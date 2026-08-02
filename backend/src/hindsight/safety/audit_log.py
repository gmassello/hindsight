import json
from datetime import UTC, datetime
from pathlib import Path

from hindsight.config import settings
from hindsight.models import CommitRecord


def record(incident_id: str, entry: CommitRecord) -> None:
    path = Path(settings.audit_log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "timestamp": datetime.now(UTC).isoformat(),
        "incident_id": incident_id,
        **entry.model_dump(),
    }
    with path.open("a") as fh:
        fh.write(json.dumps(line, ensure_ascii=False, default=str) + "\n")
