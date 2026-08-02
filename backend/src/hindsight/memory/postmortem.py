from datetime import UTC, datetime

from hindsight.models import InvestigationState


def default_title(state: InvestigationState) -> str:
    asset = state.resolution.resolved_asset.name if state.resolution else "unknown asset"
    symptom = state.incident.symptom_type if state.incident else "incident"
    date = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"Incident {date}: {symptom} in {asset}"


def render_markdown(state: InvestigationState, title: str) -> str:
    incident = state.incident
    resolution = state.resolution
    blast = state.blast_radius
    lines = [f"# {title}", ""]
    if resolution:
        lines.append(f"**Asset**: {resolution.resolved_asset.urn}")
    if incident:
        lines.append(f"**Detected**: {incident.detected_at or 'unknown'}")
        lines.append(
            f"**Symptom**: {incident.symptom_type} — {incident.symptom_description}"
        )
    lines.append("**Status**: active")
    lines.append("")

    if blast:
        max_hops = max((a.hops for a in blast.impacted), default=0)
        lines.append("## Blast radius")
        lines.append(
            f"{len(blast.impacted)} affected consumers within {max_hops} hops. "
            f"Score: {blast.total_score}"
        )
        lines.append(f"Owners notified: {', '.join(blast.owners_to_notify) or 'none'}")
        lines.append("")
        lines.append("| Asset | Type | Hops | Score |")
        lines.append("|---|---|---|---|")
        for a in blast.impacted:
            lines.append(f"| {a.name or a.urn} | {a.type} | {a.hops} | {a.score} |")
        lines.append("")

    if state.hypotheses:
        lines.append("## Root cause hypotheses")
        for i, h in enumerate(state.hypotheses, 1):
            lines.append(f"{i}. {h.statement} — confidence {round(h.confidence * 100)}%")
            for e in h.evidence:
                lines.append(f"   - {e}")
            if h.evidence_urns:
                lines.append(f"   - Evidence URNs: {', '.join(h.evidence_urns)}")
        lines.append("")

    lines.append("## Resolution")
    lines.append("Pending human confirmation.")
    lines.append("")
    lines.append("## Detection signals")
    if state.hypotheses:
        top = state.hypotheses[0]
        lines.append(
            f"Watch for {top.cause_type.replace('_', ' ')} on the assets cited above."
        )
    else:
        lines.append("No signals identified.")
    lines.append("")
    lines.append("## Tags")
    tags = ["hindsight"]
    if incident:
        tags.append(incident.symptom_type)
    if state.hypotheses:
        tags.append(state.hypotheses[0].cause_type)
    lines.append(", ".join(tags))
    return "\n".join(lines)
