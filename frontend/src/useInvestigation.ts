import { useCallback, useRef, useState } from 'react'
import { API_URL, approveInvestigation, createInvestigation, rejectInvestigation } from './api'
import { KINDS } from './types'
import type {
  ActionPlan,
  BlastRadius,
  EventKind,
  Hypothesis,
  Incident,
  InvestigationState,
  RecallResult,
  Recording,
  ResolveResult,
  Status,
  TimelineEvent,
  UiEvent,
} from './types'

export type UiPhase = 'idle' | Status

const CADENCE: Record<EventKind, number> = {
  start: 350,
  info: 150,
  tool_call: 200,
  warning: 450,
  error: 450,
  result: 700,
}

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

interface ReplayRun {
  tail: TimelineEvent[]
  state: InvestigationState
}

export function useInvestigation() {
  const [state, setState] = useState<InvestigationState | null>(null)
  const [events, setEvents] = useState<UiEvent[]>([])
  const [override, setOverride] = useState<UiPhase | null>(null)
  const [error, setError] = useState<string | null>(null)
  const replay = useRef<ReplayRun | null>(null)
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

  const handleEvent = useCallback(
    (event: TimelineEvent) => {
      pushEvent(event)
      if (event.kind === 'result') mergeResult(event)
    },
    [pushEvent, mergeResult],
  )

  const feed = useCallback(
    async (timeline: TimelineEvent[], run: ReplayRun) => {
      for (const event of timeline) {
        if (replay.current !== run) return false
        handleEvent(event)
        await sleep(CADENCE[event.kind])
      }
      return replay.current === run
    },
    [handleEvent],
  )

  const reset = useCallback(() => {
    replay.current = null
    setState(null)
    setEvents([])
    setOverride(null)
    setError(null)
  }, [])

  const startReplay = useCallback(
    async (recording: Recording) => {
      reset()

      const gate = recording.events.findIndex((e) => e.phase === 'commit')
      const cut = gate === -1 ? recording.events.length : gate
      const run: ReplayRun = { tail: recording.events.slice(cut), state: recording.state }
      replay.current = run

      setState({
        id: recording.state.id,
        input_text: recording.state.input_text,
        tool_calls: recording.state.tool_calls,
        incident: null,
        resolution: null,
        recall: null,
        blast_radius: null,
        hypotheses: [],
        plan: null,
        committed: [],
        postmortem_ref: null,
        status: 'investigating',
      })

      if (await feed(recording.events.slice(0, cut), run)) {
        setState((prev) => (prev ? { ...prev, status: 'awaiting_approval' } : prev))
      }
    },
    [feed, reset],
  )

  const start = useCallback(
    async (text: string) => {
      reset()
      try {
        const created = await createInvestigation(text)
        setState(created)

        const es = new EventSource(`${API_URL}/investigations/${created.id}/stream`)
        for (const kind of KINDS) {
          es.addEventListener(kind, (e) => {
            handleEvent(JSON.parse((e as MessageEvent).data) as TimelineEvent)
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
    [pushEvent, handleEvent, reset],
  )

  const approve = useCallback(async () => {
    const run = replay.current
    if (run) {
      setOverride('committing')
      if (await feed(run.tail, run)) {
        setState(run.state)
        setOverride(null)
      }
      return
    }

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
  }, [state, pushEvent, feed])

  const reject = useCallback(async () => {
    if (replay.current) {
      setState((prev) => (prev ? { ...prev, status: 'rejected' } : prev))
      return
    }
    if (!state) return
    try {
      setState(await rejectInvestigation(state.id))
    } catch (exc) {
      setError(String(exc))
    }
  }, [state])

  return { state, events, uiPhase, error, start, startReplay, reset, approve, reject }
}
