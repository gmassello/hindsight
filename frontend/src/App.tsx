import BlastRadiusPanel from './components/BlastRadius'
import HypothesesPanel from './components/HypothesesPanel'
import IncidentInput from './components/IncidentInput'
import PlanPanel from './components/PlanPanel'
import RecallPanel from './components/RecallPanel'
import ResolvedAsset from './components/ResolvedAsset'
import Timeline from './components/Timeline'
import { useInvestigation } from './useInvestigation'

export default function App() {
  const { state, events, uiPhase, error, start, approve, reject } = useInvestigation()

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">◉</span> Hindsight
          <span className="brand-sub">on-call agent for your data platform</span>
        </div>
        <span className={`status-pill status-${uiPhase}`}>
          {uiPhase === 'idle' ? 'ready' : uiPhase.replace('_', ' ')}
        </span>
      </header>

      {error && <div className="error-banner">{error}</div>}

      {uiPhase === 'idle' ? (
        <main className="hero">
          <h1>Something broke in your data platform?</h1>
          <p className="hero-sub">
            Describe the incident. Hindsight walks the DataHub lineage, computes the blast
            radius, proposes root causes and writes the postmortem back — with your approval.
          </p>
          <IncidentInput onSubmit={start} />
        </main>
      ) : (
        <main className="workspace">
          <section className="timeline-col">
            <Timeline events={events} busy={uiPhase === 'investigating' || uiPhase === 'committing'} />
          </section>
          <section className="panels-col">
            {state?.resolution && <ResolvedAsset resolution={state.resolution} incident={state.incident} />}
            {state?.recall && <RecallPanel recall={state.recall} />}
            {state?.blast_radius && <BlastRadiusPanel blastRadius={state.blast_radius} />}
            {state && state.hypotheses.length > 0 && <HypothesesPanel hypotheses={state.hypotheses} />}
            {state?.plan && (
              <PlanPanel
                plan={state.plan}
                committed={state.committed}
                postmortemRef={state.postmortem_ref}
                uiPhase={uiPhase}
                onApprove={approve}
                onReject={reject}
              />
            )}
            {uiPhase === 'failed' && (
              <div className="panel failed-note">Investigation failed — reload the page to start over.</div>
            )}
          </section>
        </main>
      )}
    </div>
  )
}
