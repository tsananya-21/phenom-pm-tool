import type { Analysis, PitchItem } from './types'

export function to100(v: number | null | undefined): number {
  if (v == null) return 0
  return v > 1 ? Math.round(v) : Math.round(v * 100)
}

export function fitScore(analysis: Analysis): number {
  const dims = Object.values(analysis.dimensions)
  if (!dims.length) return 50
  const scores = dims.map(d => to100(d.score))
  const avg = scores.reduce((a, b) => a + b, 0) / scores.length
  return Math.min(100, Math.max(10, Math.round(110 - avg * 0.6)))
}

export function fitLabel(score: number): string {
  if (score >= 80) return 'Strong fit'
  if (score >= 65) return 'Good fit'
  if (score >= 50) return 'Moderate fit'
  return 'Weak fit'
}

export function fitScoreColor(score: number): string {
  if (score >= 80) return 'text-emerald-400'
  if (score >= 65) return 'text-blue-400'
  if (score >= 50) return 'text-amber-400'
  return 'text-red-400'
}

export function scoreTextColor(score: number): string {
  if (score >= 70) return 'text-emerald-400'
  if (score >= 40) return 'text-amber-400'
  return 'text-red-400'
}

export function scoreBarColor(score: number): string {
  if (score >= 70) return 'bg-emerald-400'
  if (score >= 40) return 'bg-amber-400'
  return 'bg-red-400'
}

export function coverageLabel(cov: string): string {
  const map: Record<string, string> = {
    high: 'Strong evidence',
    medium: 'Moderate evidence',
    low: 'Limited data',
    inferred: 'Inferred',
  }
  return map[cov?.toLowerCase()] ?? cov ?? '—'
}

export function bulletText(item: PitchItem | unknown): string {
  if (typeof item === 'string') return item
  if (item && typeof item === 'object') {
    const obj = item as Record<string, string>
    const product = obj.phenomProduct || obj.product || ''
    const desc = obj.description || obj.whatItDoes || JSON.stringify(item)
    return product ? `${product}: ${desc}` : desc
  }
  return String(item)
}

export function buildExportMarkdown(
  analysis: Analysis,
  bundle: { company_name: string; signals: Array<{ source_type: string; content: string }> },
  fit: number,
  notes: string,
): string {
  const company = analysis.company || bundle.company_name
  const lines: string[] = [`# ${company} — Phenom Intelligence Report`, '']

  const meta = [analysis.industry, analysis.companySize].filter(Boolean).join(' · ')
  if (meta) lines.push(meta, '')

  const stack = analysis.detectedStack
  if (stack?.ats) lines.push(`ATS: ${stack.ats} (${to100(stack.confidence)}% confidence)`, '')
  if (analysis.topOpportunity) lines.push(`**Top opportunity:** ${analysis.topOpportunity}`, '')

  lines.push('---', '## Talent Operations', '')
  for (const [key, d] of Object.entries(analysis.dimensions)) {
    const label = key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    lines.push(`### ${label} — ${to100(d.score)}/100`, d.currentState || '', '')
    for (const g of d.gaps || []) lines.push(`- ${g}`)
    lines.push('')
  }

  const pitch = analysis.pitch || {}
  lines.push('---', '## Summary', '')
  if (pitch.strengths?.length) {
    lines.push('**Doing well:**')
    for (const s of pitch.strengths) lines.push(`- ${bulletText(s)}`)
    lines.push('')
  }
  if (pitch.weaknesses?.length) {
    lines.push('**Can do better:**')
    for (const w of pitch.weaknesses) lines.push(`- ${bulletText(w)}`)
    lines.push('')
  }
  if (pitch.opportunities?.length) {
    lines.push('**Opportunity:**')
    for (const o of pitch.opportunities) lines.push(`- ${bulletText(o)}`)
    lines.push('')
  }
  lines.push(`**Phenom Fit Score:** ${fit}/100 — ${fitLabel(fit)}`, '')

  lines.push('---', '## Sales Pitch', '')
  if (pitch.hook) lines.push(`*${pitch.hook}*`, '')
  for (const p of analysis.solutionPrototypes || []) {
    lines.push(`**${p.phenomProduct}**`, p.whatItDoes || '')
    if (p.successMetric) lines.push(`*${p.successMetric}*`)
    lines.push('')
  }
  if (pitch.roi) lines.push(`**ROI:** ${pitch.roi}`, '')
  if (pitch.cta) lines.push(`**Next step:** ${pitch.cta}`, '')

  if (notes.trim()) lines.push('---', '## Notes', '', notes)

  return lines.join('\n')
}
