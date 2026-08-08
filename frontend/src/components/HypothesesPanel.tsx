import type { Hypothesis, Verdict } from '../types'

interface Props {
  hypotheses: Hypothesis[]
  verdict: Verdict | null
}

const VERDICT_LABEL: Record<Verdict, string> = {
  probable_cause: 'probable cause',
  insufficient_evidence: 'insufficient evidence',
  exonerated: 'not an incident',
}

function confidenceClass(confidence: number): string {
  if (confidence > 0.7) return 'high'
  if (confidence > 0.4) return 'medium'
  return 'low'
}

export default function HypothesesPanel({ hypotheses, verdict }: Props) {
  const sorted = [...hypotheses].sort((a, b) => b.confidence - a.confidence)
  const exonerated = verdict === 'exonerated'
  return (
    <div className="panel">
      <h2>
        {exonerated ? 'Causes ruled out' : 'Root cause hypotheses'}
        {verdict && (
          <span className={`badge verdict verdict-${verdict}`}>{VERDICT_LABEL[verdict]}</span>
        )}
      </h2>
      {exonerated && (
        <p className="muted">
          The agent checked the pipeline and found it healthy. Nothing is being written to the
          catalog, and nobody is being paged.
        </p>
      )}
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
