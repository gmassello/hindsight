import { useCallback, useEffect, useRef, useState } from 'react'
import BlastRadiusPanel from './components/BlastRadius'
import HypothesesPanel from './components/HypothesesPanel'
import IncidentInput from './components/IncidentInput'
import PlanPanel from './components/PlanPanel'
import RecallPanel from './components/RecallPanel'
import ResolvedAsset from './components/ResolvedAsset'
import ScenarioPicker from './components/ScenarioPicker'
import Timeline from './components/Timeline'
import type { Recording } from './types'
import { useInvestigation } from './useInvestigation'

const DEMO_MODE = Boolean(import.meta.env.VITE_DEMO_MODE)
const APPROVE_AFTER = 4000
const NEXT_RUN_AFTER = 3000

export default function App() {
  const { state, events, uiPhase, error, start, startReplay, reset, approve, reject } =
    useInvestigation()
  const [recordings, setRecordings] = useState<Recording[] | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const autoplay = useRef(DEMO_MODE)
  const cursor = useRef(0)
  const approveRef = useRef(approve)
  approveRef.current = approve

  useEffect(() => {
    if (!DEMO_MODE) return
    fetch(`${import.meta.env.BASE_URL}recordings.json`)
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error(String(res.status)))))
      .then(setRecordings)
      .catch((exc) => setLoadError(String(exc)))
  }, [])

  const playNext = useCallback(() => {
    if (!recordings?.length) return
    startReplay(recordings[cursor.current % recordings.length])
    cursor.current += 1
  }, [recordings, startReplay])

  useEffect(() => {
    if (!autoplay.current || !recordings?.length) return
    if (uiPhase === 'idle') {
      playNext()
      return
    }
    if (uiPhase === 'awaiting_approval') {
      const timer = setTimeout(() => approveRef.current(), APPROVE_AFTER)
      return () => clearTimeout(timer)
    }
    if (uiPhase === 'done') {
      const timer = setTimeout(playNext, NEXT_RUN_AFTER)
      return () => clearTimeout(timer)
    }
  }, [uiPhase, recordings, playNext])

  const stopAutoplay = () => {
    autoplay.current = false
  }

  const pickRun = (recording: Recording) => {
    stopAutoplay()
    startReplay(recording)
  }

  const backToRuns = () => {
    stopAutoplay()
    reset()
  }

  const approveNow = () => {
    stopAutoplay()
    return approve()
  }

  const rejectNow = () => {
    stopAutoplay()
    return reject()
  }

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">◉</span> Hindsight
          <span className="brand-sub">on-call agent for your data platform</span>
        </div>
        <div className="header-right">
          {DEMO_MODE && uiPhase !== 'idle' && (
            <button className="link-btn" onClick={backToRuns}>
              ← Other runs
            </button>
          )}
          <span className={`status-pill status-${uiPhase}`}>
            {uiPhase === 'idle' ? 'ready' : uiPhase.replace('_', ' ')}
          </span>
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {uiPhase === 'idle' ? (
        <main className="hero">
          <h1>Something broke in your data platform?</h1>
          <p className="hero-sub">
            Describe the incident. Hindsight walks the DataHub lineage, computes the blast
            radius, proposes root causes and writes the postmortem back — with your approval.
          </p>
          {DEMO_MODE ? (
            <>
              <p className="panel demo-note">
                This is a <strong>recording</strong>, played back in the real UI. Every event below
                came from an actual run against a live DataHub — the tool calls, the scores and the
                mutations are the ones that were executed. Nothing here talks to a backend, so
                nothing can break. Pick a run:
              </p>
              <ScenarioPicker recordings={recordings} error={loadError} onPick={pickRun} />
            </>
          ) : (
            <IncidentInput onSubmit={start} />
          )}
        </main>
      ) : (
        <>
          {DEMO_MODE && (
            <p className="demo-ribbon">
              <strong>Recording</strong>, played back in the real UI — every event came from an
              actual run against a live DataHub. Nothing here talks to a backend.
            </p>
          )}
          <main className="workspace">
            <section className="timeline-col">
              <Timeline events={events} busy={uiPhase === 'investigating' || uiPhase === 'committing'} />
            </section>
            <section className="panels-col">
              {state?.resolution && <ResolvedAsset resolution={state.resolution} incident={state.incident} />}
              {state?.recall && <RecallPanel recall={state.recall} />}
              {state?.blast_radius && <BlastRadiusPanel blastRadius={state.blast_radius} />}
              {state && (state.hypotheses.length > 0 || state.verdict === 'exonerated') && (
                <HypothesesPanel hypotheses={state.hypotheses} verdict={state.verdict} />
              )}
              {state?.plan && (
                <PlanPanel
                  plan={state.plan}
                  committed={state.committed}
                  postmortemRef={state.postmortem_ref}
                  uiPhase={uiPhase}
                  onApprove={approveNow}
                  onReject={rejectNow}
                />
              )}
              {uiPhase === 'failed' && (
                <div className="panel failed-note">Investigation failed — reload the page to start over.</div>
              )}
            </section>
          </main>
        </>
      )}
    </div>
  )
}
