import type { RecallResult } from '../types'

interface Props {
  recall: RecallResult
}

export default function RecallPanel({ recall }: Props) {
  return (
    <div className="panel">
      <h2>We've seen this before</h2>
      {recall.prior_incidents.length === 0 ? (
        <p className="muted">
          No prior incidents found — this run's postmortem will seed the memory for next time.
        </p>
      ) : (
        <ul className="prior-list">
          {recall.prior_incidents.map((prior, i) => (
            <li key={i} className="prior-card">
              <div className="prior-head">
                <span className="prior-title">{prior.title}</span>
                <span className={`badge badge-${prior.similarity}`}>{prior.similarity}</span>
              </div>
              {prior.summary && <p className="prior-summary">{prior.summary}</p>}
              {prior.prior_resolution && (
                <p className="prior-resolution">Resolved by: {prior.prior_resolution}</p>
              )}
              {prior.reference && <code className="urn">{prior.reference}</code>}
            </li>
          ))}
        </ul>
      )}
      {recall.investigation_hints.length > 0 && (
        <>
          <h3>Investigation hints</h3>
          <ul className="hint-list">
            {recall.investigation_hints.map((hint, i) => (
              <li key={i}>
                <span className="chip chip-cause">{hint.cause_type.replace(/_/g, ' ')}</span>
                <span className="hint-reason">{hint.reason}</span>
                {hint.urn && <code className="urn">{hint.urn}</code>}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
