import { memo, useEffect, useRef } from 'react'
import type { EventKind, UiEvent } from '../types'

const KIND_ICON: Record<EventKind, string> = {
  start: '▶',
  info: '·',
  tool_call: '⚙',
  warning: '⚠',
  error: '✕',
  result: '✓',
}

interface Props {
  events: UiEvent[]
  busy: boolean
}

function time(ts: number): string {
  return new Date(ts).toLocaleTimeString('en-GB', { hour12: false })
}

const Row = memo(function Row({ event }: { event: UiEvent }) {
  return (
    <li className={`event event-${event.kind}`}>
      <span className="event-icon">{KIND_ICON[event.kind]}</span>
      <div className="event-body">
        <div className="event-head">
          <span className="event-phase">{event.phase}</span>
          <span className="event-time">{time(event.ts)}</span>
        </div>
        <div className="event-message">{event.message}</div>
        {event.kind === 'tool_call' && event.data.tool != null && (
          <code className={`event-tool ${event.data.error ? 'event-tool-error' : ''}`}>
            {String(event.data.tool)}({JSON.stringify(event.data.args ?? {})})
          </code>
        )}
      </div>
    </li>
  )
})

export default function Timeline({ events, busy }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const stickRef = useRef(true)

  useEffect(() => {
    const el = scrollRef.current
    if (el && stickRef.current) el.scrollTop = el.scrollHeight
  }, [events.length, busy])

  const onScroll = () => {
    const el = scrollRef.current
    if (el) stickRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80
  }

  return (
    <div className="panel timeline">
      <h2>Evidence timeline</h2>
      <div className="timeline-scroll" ref={scrollRef} onScroll={onScroll}>
        <ul>
          {events.map((event, i) => (
            <Row key={i} event={event} />
          ))}
          {busy && (
            <li className="event event-working">
              <span className="event-icon pulse">●</span>
              <div className="event-body">
                <div className="event-message muted">Agent working…</div>
              </div>
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
