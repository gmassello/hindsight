from hindsight.models import BlastRadius, ConsumerReport, ImpactedAsset

TYPE_WEIGHTS = {
    "dashboard": 3.0,
    "mlmodel": 3.0,
    "mlfeature": 3.0,
    "mlfeaturetable": 3.0,
    "chart": 2.0,
    "datajob": 2.0,
    "dataset": 1.0,
}

OWNER_MULTIPLIER = 1.5
CRITICAL_MULTIPLIER = 2.0
DOMAIN_MULTIPLIER = 1.3


def type_weight(asset_type: str, urn: str) -> float:
    key = asset_type.lower().replace(" ", "").replace("_", "")
    if key in TYPE_WEIGHTS:
        return TYPE_WEIGHTS[key]
    for known, weight in TYPE_WEIGHTS.items():
        if f"urn:li:{known}:" in urn.lower():
            return weight
    return 1.0


def impact_score(
    asset_type: str,
    urn: str,
    hops: int,
    has_owner: bool,
    is_critical: bool,
    in_domain: bool,
) -> float:
    score = type_weight(asset_type, urn) / (1 + max(hops, 0))
    if has_owner:
        score *= OWNER_MULTIPLIER
    if is_critical:
        score *= CRITICAL_MULTIPLIER
    if in_domain:
        score *= DOMAIN_MULTIPLIER
    return round(score, 2)


def build_blast_radius(consumers: list[ConsumerReport]) -> BlastRadius:
    impacted = []
    for c in consumers:
        owners = [o for o in c.owners if o]
        impacted.append(
            ImpactedAsset(
                urn=c.urn,
                name=c.name,
                type=c.type,
                hops=c.hops,
                owners=owners,
                score=impact_score(
                    asset_type=c.type,
                    urn=c.urn,
                    hops=c.hops,
                    has_owner=bool(owners),
                    is_critical=c.is_critical,
                    in_domain=c.in_domain,
                ),
            )
        )
    impacted.sort(key=lambda a: a.score, reverse=True)
    owners_to_notify = sorted({o for a in impacted for o in a.owners})
    return BlastRadius(
        impacted=impacted,
        total_score=round(sum(a.score for a in impacted), 2),
        owners_to_notify=owners_to_notify,
    )
