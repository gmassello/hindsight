from typing import Any

from hindsight.datahub.graphql_fallback import document_text, entity_facets, tag_urn
from hindsight.models import mutation_targets

Check = tuple[bool, str]


def check_record(record: dict[str, Any]) -> list[Check]:
    tool = record.get("tool", "")
    args = record.get("args") or {}
    checks: list[Check] = []

    for urn in mutation_targets(args, record.get("urn", "")):
        try:
            facets = entity_facets(urn)
        except Exception as exc:
            checks.append((False, f"could not read {urn}: {exc}"))
            continue

        if tool == "add_tags":
            for tag in args.get("tag_urns") or []:
                checks.append((tag_urn(tag) in facets["tags"], f"tag {tag} on {urn}"))
        elif tool == "update_description":
            expected = args.get("description") or ""
            checks.append((expected in facets["description"], f"incident banner on {urn}"))
        elif tool == "add_owners":
            for owner in args.get("owner_urns") or []:
                checks.append((owner in facets["owners"], f"owner {owner} on {urn}"))
        elif tool == "set_domains":
            expected = args.get("domain_urn") or ""
            checks.append((facets["domain"] == expected, f"domain {expected} on {urn}"))
        else:
            checks.append((False, f"no verification implemented for {tool} on {urn}"))

    return checks


def check_postmortem(document_urn: str, pattern: str) -> Check:
    label = f"postmortem {document_urn} still cites {pattern}"
    try:
        return (pattern in document_text(document_urn), label)
    except Exception as exc:
        return (False, f"could not read {document_urn}: {exc}")


def render_checks(title: str, checks: list[Check]) -> str:
    lines = [f"# Verification of {title}", ""]
    lines.extend(f"- [{'x' if ok else ' '}] {label}" for ok, label in checks)
    passed = sum(1 for ok, _ in checks if ok)
    lines.extend(["", f"verified {passed}/{len(checks)}"])
    return "\n".join(lines) + "\n"
