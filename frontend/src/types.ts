export interface Signal {
  source_url: string
  source_type: string
  dimension: string
  signal_type: string
  content: string
  raw_snippet: string
  confidence: number
  extracted_at: string
}

export interface ATSDetection {
  ats_name: string | null
  evidence_url: string | null
  detection_method: string
  confidence: number
}

export interface CoverageScore {
  dimension: string
  score: number
  signal_count: number
  is_thin: boolean
  thin_reason: string | null
}

export interface Bundle {
  company_name: string
  domain: string | null
  sources_attempted: string[]
  sources_fetched: string[]
  signals: Signal[]
  ats: ATSDetection
  coverage: CoverageScore[]
  fetched_at: string
}

export interface DimensionData {
  score: number
  currentState: string
  evidence: string[]
  gaps: string[]
  coverage: string
}

export interface Prototype {
  phenomProduct: string
  gap: string
  evidenceRef?: string
  whatItDoes: string
  successMetric?: string
  priority: 'high' | 'medium' | 'low'
}

export type PitchItem = string | Record<string, string>

export interface Pitch {
  hook?: string
  strengths?: PitchItem[]
  weaknesses?: PitchItem[]
  opportunities?: PitchItem[]
  roi?: string
  cta?: string
}

export interface DetectedStack {
  ats: string | null
  confidence: number
  source: string | null
}

export interface RevenuePoint {
  period: string
  amount: string
}

export interface Analysis {
  company: string
  industry?: string
  companySize?: string
  description?: string
  revenueHistory?: RevenuePoint[]
  detectedStack?: DetectedStack
  dimensions: Record<string, DimensionData>
  solutionPrototypes: Prototype[]
  topOpportunity?: string
  pitch?: Pitch
}

export interface ResearchResult {
  bundle: Bundle
  analysis: Analysis
  fitScore: number
  timestamp: string
}
