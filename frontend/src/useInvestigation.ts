import { useCallback, useState } from 'react'
import { API_URL, approveInvestigation, createInvestigation, rejectInvestigation } from './api'
import { KINDS } from './types'
import type {
  ActionPlan,
  BlastRadius,
  Hypothesis,
  Incident,
  InvestigationState,
  RecallResult,
  ResolveResult,
  Status,
  TimelineEvent,
  UiEvent,
} from './types'

export type UiPhase = 'idle' | Status

export function useInvestigation() {
  const [state, setState] = useState<InvestigationState | null>(null)
  const [events, setEvents] = useState<UiEvent[]>([])
  const [override, setOverride] = useState<UiPhase | null>(null)
  const [error, setError] = useState<string | null>(null)
  const uiPhase: UiPhase = override ?? state?.status ?? 'idle'

  const pushEvent = useCallback((event: TimelineEvent) => {
    setEvents((prev) => [...prev, { ...event, ts: Date.now() }])
  }, [])

  const mergeResult = useCallback((event: TimelineEvent) => {
    if (Object.keys(event.data).length === 0) return
    const data = event.data as unknown
    setState((prev) => {
      if (!prev) return prev
      switch (event.phase) {
        case 'intake':
          return { ...prev, incident: data as Incident }
        case 'resolve':
          return { ...prev, resolution: data as ResolveResult }
        case 'recall':
          return { ...prev, recall: data as RecallResult }
        case 'impact':
          return { ...prev, blast_radius: data as BlastRadius }
        case 'root_cause':
          return { ...prev, hypotheses: (data as { hypotheses: Hypothesis[] }).hypotheses }
        case 'propose':
          return { ...prev, plan: data as ActionPlan }
        default:
          return prev
      }
    })
  }, [])

  const start = useCallback(
    async (text: string) => {
      setError(null)
      setEvents([])
      setOverride(null)
      try {
        const created = await createInvestigation(text)
        setState(created)

        const es = new EventSource(`${API_URL}/investigations/${created.id}/stream`)
        for (const kind of KINDS) {
          es.addEventListener(kind, (e) => {
            const event = JSON.parse((e as MessageEvent).data) as TimelineEvent
            pushEvent(event)
            if (event.kind === 'result') mergeResult(event)
          })
        }
        es.addEventListener('state', (e) => {
          es.close()
          setState(JSON.parse((e as MessageEvent).data) as InvestigationState)
        })
        es.addEventListener('agent_error', (e) => {
          es.close()
          pushEvent(JSON.parse((e as MessageEvent).data) as TimelineEvent)
          setOverride('failed')
        })
        es.onerror = () => {
          es.close()
          setOverride((prev) => prev ?? 'failed')
        }
      } catch (exc) {
        setError(String(exc))
        setOverride('failed')
      }
    },
    [pushEvent, mergeResult],
  )

  const approve = useCallback(async () => {
    if (!state) return
    setOverride('committing')
    try {
      const res = await approveInvestigation(state.id)
      res.events.forEach(pushEvent)
      setState(res.state)
      setOverride(null)
    } catch (exc) {
      setError(String(exc))
      setOverride('failed')
    }
  }, [state, pushEvent])

  const reject = useCallback(async () => {
    if (!state) return
    try {
      setState(await rejectInvestigation(state.id))
    } catch (exc) {
      setError(String(exc))
    }
  }, [state])

  return { state, events, uiPhase, error, start, approve, reject }
}
