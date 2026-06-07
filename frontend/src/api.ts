import type { Bundle, Analysis } from './types'

export interface RawResearchResponse {
  bundle: Bundle
  analysis: Analysis
}

export async function fetchCompanies(): Promise<string[]> {
  const res = await fetch('/api/companies')
  if (!res.ok) throw new Error('Failed to fetch companies')
  const data = await res.json()
  return data.companies as string[]
}

export async function researchCompany(company: string): Promise<RawResearchResponse> {
  const res = await fetch('/api/research', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ company }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `Research failed (${res.status})`)
  }
  return res.json() as Promise<RawResearchResponse>
}
