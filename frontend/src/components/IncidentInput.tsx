import { useState } from 'react'

const EXAMPLE =
  'orders table in order_entry_db is showing nulls in customer_id since 03:00 UTC today'

interface Props {
  onSubmit: (text: string) => void
}

export default function IncidentInput({ onSubmit }: Props) {
  const [text, setText] = useState('')

  const submit = () => {
    if (text.trim()) onSubmit(text.trim())
  }

  return (
    <div className="incident-input">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit()
        }}
        placeholder="e.g. fct_orders has nulls in customer_id since 03:00 UTC…"
        rows={3}
      />
      <div className="incident-input-actions">
        <button className="link-btn" onClick={() => setText(EXAMPLE)}>
          Use example incident
        </button>
        <button className="primary-btn" onClick={submit} disabled={!text.trim()}>
          Investigate
        </button>
      </div>
    </div>
  )
}
