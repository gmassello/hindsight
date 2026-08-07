import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SymptomType = Literal["nulls", "freshness", "schema", "volume", "failure", "other"]
CauseType = Literal[
    "schema_drift_upstream",
    "query_change",
    "upstream_incident",
    "data_source_issue",
    "historical_precedent",
    "unknown",
]


class TimelineEvent(BaseModel):
    phase: str
    kind: Literal["start", "info", "tool_call", "warning", "error", "result"]
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class Incident(BaseModel):
    mentioned_assets: list[str] = Field(default_factory=list)
    symptom_type: SymptomType = "other"
    symptom_description: str = ""
    detected_at: str | None = None


class EntityRef(BaseModel):
    urn: str
    name: str = ""
    type: str = ""
    owners: list[str] = Field(default_factory=list)
    domain: str = ""


class ResolveResult(BaseModel):
    resolved_asset: EntityRef
    alternatives: list[EntityRef] = Field(default_factory=list)
    ambiguity_note: str | None = None


class PriorIncident(BaseModel):
    title: str
    reference: str = ""
    similarity: Literal["high", "medium", "low"] = "medium"
    prior_resolution: str = ""
    summary: str = ""


class InvestigationHint(BaseModel):
    urn: str = ""
    cause_type: CauseType = "unknown"
    reason: str = ""


class RecallResult(BaseModel):
    prior_incidents: list[PriorIncident] = Field(default_factory=list)
    investigation_hints: list[InvestigationHint] = Field(default_factory=list)


class ConsumerReport(BaseModel):
    urn: str
    name: str = ""
    type: str = ""
    hops: int = 1
    owners: list[str] = Field(default_factory=list)
    is_critical: bool = False
    in_domain: bool = False


class ConsumersReport(BaseModel):
    consumers: list[ConsumerReport] = Field(default_factory=list)


class ImpactedAsset(BaseModel):
    urn: str
    name: str = ""
    type: str = ""
    hops: int = 1
    score: float = 0.0
    owners: list[str] = Field(default_factory=list)


class BlastRadius(BaseModel):
    impacted: list[ImpactedAsset] = Field(default_factory=list)
    total_score: float = 0.0
    owners_to_notify: list[str] = Field(default_factory=list)


class Hypothesis(BaseModel):
    cause_type: CauseType = "unknown"
    statement: str
    confidence: float = 0.5
    evidence: list[str] = Field(default_factory=list)
    evidence_urns: list[str] = Field(default_factory=list)


def mutation_targets(args: dict[str, Any], default: str = "") -> list[str]:
    targets = args.get("entity_urns") or []
    single = args.get("entity_urn")
    if single:
        targets = [*targets, single]
    if not targets and default:
        targets = [default]
    return [t for t in targets if t]


class Mutation(BaseModel):
    tool: Literal["add_tags", "update_description", "add_owners", "set_domains"]
    urn: str
    args: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""

    def targets(self) -> list[str]:
        return mutation_targets(self.args, self.urn)


class ActionPlan(BaseModel):
    mutations: list[Mutation] = Field(default_factory=list)
    postmortem_title: str = ""


class CommitRecord(BaseModel):
    tool: str
    urn: str
    args: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    via: str = "mcp"
    ok: bool = True
    error: str | None = None


class InvestigationState(BaseModel):
    id: str
    input_text: str
    started_at: str = ""
    incident: Incident | None = None
    resolution: ResolveResult | None = None
    recall: RecallResult | None = None
    blast_radius: BlastRadius | None = None
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    plan: ActionPlan | None = None
    committed: list[CommitRecord] = Field(default_factory=list)
    postmortem_ref: str | None = None
    tool_calls: int = 0
    status: Literal[
        "investigating", "awaiting_approval", "committing", "done", "rejected", "failed"
    ] = "investigating"

    @classmethod
    def new(cls, text: str) -> "InvestigationState":
        return cls(
            id=uuid.uuid4().hex[:8],
            input_text=text,
            started_at=datetime.now(UTC).strftime("%Y-%m-%d"),
        )
