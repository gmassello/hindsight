from typing import Any

import httpx

from hindsight.config import settings
from hindsight.models import mutation_targets


class GraphQLError(RuntimeError):
    pass


_client = httpx.Client(timeout=30)


def _execute(query: str, variables: dict[str, Any]) -> Any:
    headers = {"Content-Type": "application/json"}
    if settings.datahub_gms_token:
        headers["Authorization"] = f"Bearer {settings.datahub_gms_token}"
    response = _client.post(
        f"{settings.datahub_gms_url.rstrip('/')}/api/graphql",
        json={"query": query, "variables": variables},
        headers=headers,
    )
    response.raise_for_status()
    body = response.json()
    if body.get("errors"):
        raise GraphQLError(str(body["errors"])[:500])
    return body.get("data")


def dataset_description(urn: str) -> str:
    data = _execute(
        "query($urn: String!) { dataset(urn: $urn) {"
        " editableProperties { description } properties { description } } }",
        {"urn": urn},
    )
    dataset = data.get("dataset") or {}
    editable = (dataset.get("editableProperties") or {}).get("description")
    original = (dataset.get("properties") or {}).get("description")
    return editable or original or ""


def _tag_urn(tag: str) -> str:
    return tag if tag.startswith("urn:li:tag:") else f"urn:li:tag:{tag}"


def ensure_tag(tag: str) -> None:
    name = _tag_urn(tag).removeprefix("urn:li:tag:")
    try:
        _execute(
            "mutation($input: CreateTagInput!) { createTag(input: $input) }",
            {"input": {"id": name, "name": name}},
        )
    except GraphQLError as exc:
        if "already exists" not in str(exc).lower():
            raise


def add_tags(urn: str, tags: list[str]) -> None:
    _execute(
        "mutation($input: AddTagsInput!) { addTags(input: $input) }",
        {"input": {"tagUrns": [_tag_urn(t) for t in tags], "resourceUrn": urn}},
    )


def update_description(urn: str, description: str) -> None:
    _execute(
        "mutation($input: DescriptionUpdateInput!) { updateDescription(input: $input) }",
        {"input": {"description": description, "resourceUrn": urn}},
    )


def add_owners(urn: str, owners: list[str]) -> None:
    bare = [o for o in owners if not o.startswith("urn:li:")]
    if bare:
        raise ValueError(
            f"Owner identifiers must be full URNs, cannot tell a user from a group: {bare}"
        )
    owner_inputs = [
        {
            "ownerUrn": o,
            "ownerEntityType": "CORP_GROUP" if "corpGroup" in o else "CORP_USER",
            "type": "TECHNICAL_OWNER",
        }
        for o in owners
    ]
    _execute(
        "mutation($input: AddOwnersInput!) { addOwners(input: $input) }",
        {"input": {"owners": owner_inputs, "resourceUrn": urn}},
    )


def set_domain(urn: str, domain: str) -> None:
    _execute(
        "mutation($entityUrn: String!, $domainUrn: String!) {"
        " setDomain(entityUrn: $entityUrn, domainUrn: $domainUrn) }",
        {"entityUrn": urn, "domainUrn": domain},
    )


def run_fallback(tool: str, args: dict[str, Any]) -> None:
    for urn in mutation_targets(args):
        if tool == "add_tags":
            add_tags(urn, args.get("tag_urns", []))
        elif tool == "update_description":
            update_description(urn, args.get("description", ""))
        elif tool == "add_owners":
            add_owners(urn, args.get("owner_urns", []))
        elif tool == "set_domains":
            if domain := args.get("domain_urn"):
                set_domain(urn, domain)
        else:
            raise GraphQLError(f"No GraphQL fallback for tool {tool}")
