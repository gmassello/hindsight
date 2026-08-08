import type { Recording } from '../types'

interface Props {
  recordings: Recording[] | null
  error: string | null
  onPick: (recording: Recording) => void
}

export default function ScenarioPicker({ recordings, error, onPick }: Props) {
  if (error) return <div className="error-banner">Could not load the recordings: {error}</div>
  if (!recordings) return <div className="muted">Loading recordings…</div>

  return (
    <div className="scenario-list">
      {recordings.map((recording) => (
        <div key={recording.id} className="panel scenario-card">
          <button className="scenario-pick" onClick={() => onPick(recording)}>
            <span className="scenario-title">{recording.title}</span>
            <span className="scenario-blurb muted">{recording.blurb}</span>
          </button>
          <p className="scenario-meta">{recording.state.tool_calls} DataHub tool calls</p>
        </div>
      ))}
    </div>
  )
}
