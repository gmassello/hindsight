import { useEffect, useState } from 'react'
import type { Recording } from '../types'

const REPO = 'https://github.com/gmassello/hindsight/tree/main'

interface Props {
  onPick: (recording: Recording) => void
}

export default function ScenarioPicker({ onPick }: Props) {
  const [recordings, setRecordings] = useState<Recording[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}recordings.json`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(String(res.status)))))
      .then(setRecordings)
      .catch((exc) => setError(String(exc)))
  }, [])

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
          <p className="scenario-meta">
            {recording.state.tool_calls} DataHub tool calls ·{' '}
            <a href={`${REPO}/${recording.source}`} target="_blank" rel="noreferrer">
              {recording.source}
            </a>
          </p>
        </div>
      ))}
    </div>
  )
}
