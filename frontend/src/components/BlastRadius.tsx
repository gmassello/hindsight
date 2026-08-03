import type { BlastRadius, ImpactedAsset } from '../types'

interface Props {
  blastRadius: BlastRadius
}

export default function BlastRadiusPanel({ blastRadius }: Props) {
  const maxScore = Math.max(...blastRadius.impacted.map((a) => a.score), 1)
  const sorted = [...blastRadius.impacted].sort((a, b) => a.hops - b.hops || b.score - a.score)
  const byHops = new Map<number, ImpactedAsset[]>()
  for (const asset of sorted) {
    const group = byHops.get(asset.hops)
    if (group) group.push(asset)
    else byHops.set(asset.hops, [asset])
  }

  return (
    <div className="panel">
      <h2>Blast radius</h2>
      <div className="blast-summary">
        <div>
          <span className="blast-score-number">{blastRadius.total_score.toFixed(1)}</span>
          <span className="blast-score-label">total impact score</span>
        </div>
        <div>
          <span className="blast-score-label">owners to notify</span>
          <div className="chips">
            {blastRadius.owners_to_notify.length === 0 ? (
              <span className="muted">none found</span>
            ) : (
              blastRadius.owners_to_notify.map((owner) => (
                <span key={owner} className="chip chip-owner">
                  {owner.replace('urn:li:corpuser:', '').replace('urn:li:corpGroup:', '')}
                </span>
              ))
            )}
          </div>
        </div>
      </div>
      {[...byHops.entries()].map(([hops, assets]) => (
        <div key={hops} className="hop-group">
          <h3>
            {hops} hop{hops > 1 ? 's' : ''} downstream
          </h3>
          <ul className="impact-list">
            {assets.map((asset) => (
              <li key={asset.urn} className="impact-row">
                <div className="impact-head">
                  <span className="impact-name" title={asset.urn}>
                    {asset.name || asset.urn}
                  </span>
                  <span className="chip chip-type">{asset.type}</span>
                  <span className="impact-score">{asset.score.toFixed(2)}</span>
                </div>
                <div className="score-bar">
                  <div className="score-bar-fill" style={{ width: `${(asset.score / maxScore) * 100}%` }} />
                </div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
