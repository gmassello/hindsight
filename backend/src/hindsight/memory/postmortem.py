from hindsight.models import BlastRadius, InvestigationState


def default_title(state: InvestigationState) -> str:
    asset = state.resolution.resolved_asset.name if state.resolution else "unknown asset"
    symptom = state.incident.symptom_type if state.incident else "incident"
    return f"Incident {state.started_at}: {symptom} in {asset}"


def postmortem_title(state: InvestigationState) -> str:
    return (state.plan.postmortem_title if state.plan else "") or default_title(state)


def save_document_args(
    schema: dict, title: str, content: str, related_urn: str | None = None
) -> dict:
    args: dict = {"title": title, "content": content}
    properties = schema.get("properties", {})
    if "related_assets" in properties and related_urn:
        args["related_assets"] = [related_urn]
    doc_type = properties.get("document_type", {})
    allowed = doc_type.get("enum") or [
        option["const"] for option in doc_type.get("anyOf", []) if option.get("const")
    ]
    if allowed:
        args["document_type"] = "Analysis" if "Analysis" in allowed else allowed[0]
    return args


def blast_table(blast: BlastRadius, owners: bool = False) -> list[str]:
    if owners:
        lines = ["| Asset | Type | Hops | Score | Owners |", "|---|---|---|---|---|"]
    else:
        lines = ["| Asset | Type | Hops | Score |", "|---|---|---|---|"]
    for a in blast.impacted:
        row = f"| {a.name or a.urn} | {a.type} | {a.hops} | {a.score} |"
        if owners:
            row += f" {', '.join(a.owners) or '—'} |"
        lines.append(row)
    return lines


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
        lines.extend(blast_table(blast))
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
