import type { ActionPlan, CommitRecord } from '../types'
import type { UiPhase } from '../useInvestigation'

interface Props {
  plan: ActionPlan
  committed: CommitRecord[]
  postmortemRef: string | null
  uiPhase: UiPhase
  onApprove: () => void
  onReject: () => void
}

export default function PlanPanel({ plan, committed, postmortemRef, uiPhase, onApprove, onReject }: Props) {
  return (
    <div className={`panel plan ${uiPhase === 'rejected' ? 'plan-rejected' : ''}`}>
      <h2>Proposed action plan</h2>
      {plan.postmortem_title && (
        <p className="plan-postmortem-title">
          Postmortem: <strong>{plan.postmortem_title}</strong>
        </p>
      )}
      <ul className="mutation-list">
        {plan.mutations.map((mutation, i) => {
          const record = committed[i]
          return (
            <li key={i} className="mutation">
              <span className="mutation-gutter">+</span>
              <div className="mutation-body">
                <div className="mutation-head">
                  <span className="chip chip-tool">{mutation.tool}</span>
                  <code className="urn">{mutation.urn}</code>
                </div>
                <code className="mutation-args">{JSON.stringify(mutation.args)}</code>
                {mutation.rationale && <p className="mutation-rationale">{mutation.rationale}</p>}
                {record && (
                  <div className={`mutation-status ${record.ok ? 'ok' : 'err'}`}>
                    {record.ok ? `✓ committed via ${record.via}` : `✕ ${record.error ?? 'failed'}`}
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ul>

      {uiPhase === 'awaiting_approval' && (
        <div className="gate">
          <span className="gate-label">Human approval required — nothing has been written yet.</span>
          <div className="gate-actions">
            <button className="reject-btn" onClick={onReject}>
              Reject
            </button>
            <button className="primary-btn" onClick={onApprove}>
              Approve & commit
            </button>
          </div>
        </div>
      )}
      {uiPhase === 'committing' && (
        <div className="gate">
          <span className="gate-label pulse">Applying mutations to DataHub… (~30–60s)</span>
        </div>
      )}
      {uiPhase === 'done' && postmortemRef && (
        <div className="postmortem-callout">
          ✓ Postmortem saved to DataHub: <code className="urn">{postmortemRef}</code>
        </div>
      )}
      {uiPhase === 'rejected' && (
        <div className="rejected-banner">Plan rejected — no changes were applied.</div>
      )}
    </div>
  )
}
