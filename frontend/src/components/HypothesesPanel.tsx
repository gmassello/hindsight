import type { Hypothesis } from '../types'

interface Props {
  hypotheses: Hypothesis[]
}

function confidenceClass(confidence: number): string {
  if (confidence > 0.7) return 'high'
  if (confidence > 0.4) return 'medium'
  return 'low'
}

export default function HypothesesPanel({ hypotheses }: Props) {
  const sorted = [...hypotheses].sort((a, b) => b.confidence - a.confidence)
  return (
    <div className="panel">
      <h2>Root cause hypotheses</h2>
      <ol className="hypothesis-list">
        {sorted.map((hypothesis, i) => (
          <li key={i} className="hypothesis">
            <div className="hypothesis-head">
              <span className="chip chip-cause">{hypothesis.cause_type.replace(/_/g, ' ')}</span>
              <span className={`confidence-label confidence-${confidenceClass(hypothesis.confidence)}`}>
                {Math.round(hypothesis.confidence * 100)}%
              </span>
            </div>
            <p className="hypothesis-statement">{hypothesis.statement}</p>
            <div className="confidence-bar">
              <div
                className={`confidence-bar-fill confidence-${confidenceClass(hypothesis.confidence)}`}
                style={{ width: `${hypothesis.confidence * 100}%` }}
              />
            </div>
            {(hypothesis.evidence.length > 0 || hypothesis.evidence_urns.length > 0) && (
              <details>
                <summary>Evidence</summary>
                <ul className="evidence-list">
                  {hypothesis.evidence.map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                  {hypothesis.evidence_urns.map((urn) => (
                    <li key={urn}>
                      <code className="urn">{urn}</code>
                    </li>
                  ))}
                </ul>
              </details>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
