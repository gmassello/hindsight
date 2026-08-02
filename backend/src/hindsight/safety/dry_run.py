from hindsight.models import ActionPlan


def render_plan(plan: ActionPlan) -> str:
    if not plan.mutations:
        return "No mutations proposed."
    lines = ["Proposed mutations (dry-run, nothing executed yet):", ""]
    for i, m in enumerate(plan.mutations, 1):
        args = ", ".join(f"{k}={v}" for k, v in m.args.items())
        lines.append(f"  {i}. + {m.tool} on {m.urn}")
        lines.append(f"       args: {args}")
        lines.append(f"       why:  {m.rationale}")
    if plan.postmortem_title:
        lines.append("")
        lines.append(f"  + save_document: \"{plan.postmortem_title}\"")
    return "\n".join(lines)
