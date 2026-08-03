import type { Incident, ResolveResult } from '../types'

interface Props {
  resolution: ResolveResult
  incident: Incident | null
}

export default function ResolvedAsset({ resolution, incident }: Props) {
  const asset = resolution.resolved_asset
  return (
    <div className="panel resolved">
      <div className="resolved-row">
        <span className="chip chip-type">{asset.type || 'asset'}</span>
        <span className="resolved-name">{asset.name || asset.urn}</span>
        {incident && <span className="chip chip-symptom">{incident.symptom_type}</span>}
      </div>
      <code className="urn">{asset.urn}</code>
      {resolution.ambiguity_note && (
        <div className="ambiguity">⚠ {resolution.ambiguity_note}</div>
      )}
    </div>
  )
}
