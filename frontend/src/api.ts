import type { CommitResponse, InvestigationState } from './types'

export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init)
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${body}`)
  }
  return res.json() as Promise<T>
}

export function createInvestigation(text: string): Promise<InvestigationState> {
  return request('/investigations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
}

export function approveInvestigation(id: string): Promise<CommitResponse> {
  return request(`/investigations/${id}/approve`, { method: 'POST' })
}

export function rejectInvestigation(id: string): Promise<InvestigationState> {
  return request(`/investigations/${id}/reject`, { method: 'POST' })
}
