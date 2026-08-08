export const KINDS = ['start', 'info', 'tool_call', 'warning', 'error', 'result'] as const
export type EventKind = (typeof KINDS)[number]

export type SymptomType = 'nulls' | 'freshness' | 'schema' | 'volume' | 'failure' | 'other'

export type CauseType =
  | 'schema_drift_upstream'
  | 'query_change'
  | 'upstream_incident'
  | 'data_source_issue'
  | 'historical_precedent'
  | 'unknown'

export type Status =
  | 'investigating'
  | 'awaiting_approval'
  | 'committing'
  | 'done'
  | 'rejected'
  | 'failed'

export interface TimelineEvent {
  phase: string
  kind: EventKind
  message: string
  data: Record<string, unknown>
}

export interface UiEvent extends TimelineEvent {
  ts: number
}

export interface Incident {
  mentioned_assets: string[]
  symptom_type: SymptomType
  symptom_description: string
  detected_at: string | null
}

export interface EntityRef {
  urn: string
  name: string
  type: string
}

export interface ResolveResult {
  resolved_asset: EntityRef
  alternatives: EntityRef[]
  ambiguity_note: string | null
}

export interface PriorIncident {
  title: string
  reference: string
  similarity: 'high' | 'medium' | 'low'
  prior_resolution: string
  summary: string
}

export interface InvestigationHint {
  urn: string
  cause_type: CauseType
  reason: string
}

export interface RecallResult {
  prior_incidents: PriorIncident[]
  investigation_hints: InvestigationHint[]
}

export interface ImpactedAsset {
  urn: string
  name: string
  type: string
  hops: number
  score: number
  owners: string[]
}

export interface BlastRadius {
  impacted: ImpactedAsset[]
  total_score: number
  owners_to_notify: string[]
}

export interface Hypothesis {
  cause_type: CauseType
  statement: string
  confidence: number
  evidence: string[]
  evidence_urns: string[]
}

export interface Mutation {
  tool: 'add_tags' | 'update_description' | 'add_owners' | 'set_domains'
  urn: string
  args: Record<string, unknown>
  rationale: string
}

export interface ActionPlan {
  mutations: Mutation[]
  postmortem_title: string
}

export interface CommitRecord {
  tool: string
  urn: string
  args: Record<string, unknown>
  rationale: string
  via: string
  ok: boolean
  error: string | null
}

export interface InvestigationState {
  id: string
  input_text: string
  incident: Incident | null
  resolution: ResolveResult | null
  recall: RecallResult | null
  blast_radius: BlastRadius | null
  hypotheses: Hypothesis[]
  plan: ActionPlan | null
  committed: CommitRecord[]
  postmortem_ref: string | null
  tool_calls: number
  status: Status
}

export interface CommitResponse {
  state: InvestigationState
  events: TimelineEvent[]
}

export interface Recording {
  id: string
  title: string
  blurb: string
  source: string
  events: TimelineEvent[]
  state: InvestigationState
}
