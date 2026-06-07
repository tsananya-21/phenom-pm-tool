import { type ReactNode, useState, useEffect, useRef } from 'react'
import {
  ExternalLink,
  Briefcase, Users, Star, Newspaper, FileText, Globe,
  MessageSquarePlus,
} from 'lucide-react'
import type { ResearchResult, DimensionData, Prototype, PitchItem, Signal, RevenuePoint } from '../types'
import {
  to100, fitLabel, fitScoreColor,
  coverageLabel, bulletText,
} from '../utils'

// ── Colors ────────────────────────────────────────────────────────────────────

const C = {
  surface:   '#0f0f1a',
  raised:    '#16162a',
  border:    '#1e1e38',
  borderLt:  '#2a2a50',
  muted:     '#8585b8',
  dim:       '#a0a0d0',
  text:      '#c8c8f0',
  textBright:'#e8e8ff',
  violet:    '#7c3aed',
  violetLt:  '#a78bfa',
}

// ── Source icon (per source_type) ─────────────────────────────────────────────

function SourceIcon({ type, className = 'w-2.5 h-2.5' }: { type: string; className?: string }) {
  if (type === 'job_posting') return <Briefcase className={className} />
  if (type === 'linkedin')    return <Users className={className} />
  if (type === 'glassdoor')   return <Star className={className} />
  if (type === 'news')        return <Newspaper className={className} />
  if (type === 'filing')      return <FileText className={className} />
  if (type === 'careers_site') return <Globe className={className} />
  return <ExternalLink className={className} />
}

function shortDomain(url: string): string {
  try { return new URL(url).hostname.replace(/^www\./, '') } catch { return url.slice(0, 24) }
}

// ── Source link (inline, at end of sentence) ──────────────────────────────────

function SourceLink({ url, sourceType }: { url: string; sourceType?: string }) {
  if (!url || url === '#' || url === 'mock') return null
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center transition-colors flex-shrink-0 ml-1.5"
      style={{ color: C.muted }}
      onMouseEnter={e => ((e.currentTarget as HTMLAnchorElement).style.color = C.violetLt)}
      onMouseLeave={e => ((e.currentTarget as HTMLAnchorElement).style.color = C.muted)}
      title={url}
    >
      <SourceIcon type={sourceType || ''} />
    </a>
  )
}

// ── Signal bullet with source icon ───────────────────────────────────────────

function SignalBullet({ content, url, sourceType }: { content: string; url: string; sourceType?: string }) {
  return (
    <div className="flex gap-2 text-xs leading-relaxed" style={{ color: C.text }}>
      <span className="flex-shrink-0 mt-0.5" style={{ color: C.muted }}>·</span>
      <span className="flex-1">{content}</span>
      <SourceLink url={url} sourceType={sourceType} />
    </div>
  )
}

// ── Overview section ──────────────────────────────────────────────────────────

function OverviewSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-sm font-semibold mb-2 uppercase tracking-wider" style={{ color: C.muted }}>{title}</p>
      {children}
    </div>
  )
}

// ── Revenue sparkline ─────────────────────────────────────────────────────────

function RevenueSparkline({ data }: { data: RevenuePoint[] }) {
  const parse = (s: string): number | null => {
    const m = s.match(/([\d.]+)\s*([BMKbmk])/i)
    if (!m) return null
    const n = parseFloat(m[1])
    const u = m[2].toUpperCase()
    return u === 'B' ? n * 1000 : u === 'M' ? n : n / 1000
  }
  const entries = data
    .map(d => ({ period: d.period, value: parse(d.amount) }))
    .filter(e => e.value !== null) as { period: string; value: number }[]
  if (entries.length < 2) return null

  const vals = entries.map(e => e.value)
  const min = Math.min(...vals), max = Math.max(...vals), range = max - min || 1
  const W = 96, H = 28, P = 3
  const pts = vals.map((v, i) => [
    P + (i / (vals.length - 1)) * (W - P * 2),
    H - P - ((v - min) / range) * (H - P * 2),
  ])
  const path = pts.map((p, i) => `${i === 0 ? 'M' : 'L'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ')
  const isUp = vals[vals.length - 1] >= vals[0]
  const col = isUp ? '#34d399' : '#f87171'

  return (
    <div className="flex items-center gap-5 mb-3">
      <svg width={W} height={H} className="flex-shrink-0">
        <path d={path} fill="none" stroke={col} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="2.5" fill={col} />
      </svg>
      <div className="flex gap-4 flex-wrap">
        {entries.map((e, i) => (
          <div key={i} className="flex-shrink-0">
            <div className="text-xs font-semibold tabular-nums" style={{ color: C.textBright }}>{data[i].amount}</div>
            <div className="text-xs" style={{ color: C.dim }}>{e.period}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Divider ───────────────────────────────────────────────────────────────────

function Divider() {
  return <div className="my-8" style={{ height: 1, background: C.border }} />
}

// ── Talent card ───────────────────────────────────────────────────────────────

function TalentCard({ label, d, signals }: { label: string; d: DimensionData; signals: Signal[] }) {
  const uniqSources = signals.reduce((acc, s) => {
    if (!acc.some(x => x.url === s.source_url)) acc.push({ url: s.source_url, type: s.source_type })
    return acc
  }, [] as { url: string; type: string }[]).slice(0, 4)

  return (
    <div className="rounded-xl p-4 transition-colors"
         style={{ background: C.surface, border: `1px solid ${C.border}` }}
         onMouseEnter={e => ((e.currentTarget as HTMLDivElement).style.borderColor = C.borderLt)}
         onMouseLeave={e => ((e.currentTarget as HTMLDivElement).style.borderColor = C.border)}
    >
      <h3 className="text-sm font-semibold mb-1" style={{ color: C.textBright }}>{label}</h3>
      <p className="text-xs mb-3" style={{ color: C.dim }}>{coverageLabel(d.coverage)}</p>
      <p className="text-sm leading-relaxed" style={{ color: C.text }}>{d.currentState || 'No data.'}</p>
      {d.gaps && d.gaps.length > 0 && (
        <div className="mt-3 pt-3" style={{ borderTop: `1px solid ${C.border}` }}>
          <p className="text-xs mb-2" style={{ color: C.dim }}>Gaps</p>
          <ul className="space-y-1.5">
            {d.gaps.map((g, i) => (
              <li key={i} className="flex gap-2 text-xs leading-relaxed" style={{ color: C.muted }}>
                <span className="flex-shrink-0 mt-0.5" style={{ color: C.border }}>·</span>
                {g}
              </li>
            ))}
          </ul>
        </div>
      )}
      {uniqSources.length > 0 && (
        <div className="mt-3 pt-3 flex flex-wrap gap-2" style={{ borderTop: `1px solid ${C.border}` }}>
          {uniqSources.map((s, i) => (
            <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
               className="inline-flex items-center gap-1 text-xs transition-colors"
               style={{ color: C.muted }}
               onMouseEnter={e => ((e.currentTarget as HTMLAnchorElement).style.color = C.violetLt)}
               onMouseLeave={e => ((e.currentTarget as HTMLAnchorElement).style.color = C.muted)}
               title={s.url}
            >
              <SourceIcon type={s.type} />
              <span>{s.type.replace(/_/g, ' ')}</span>
            </a>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Prototype card ────────────────────────────────────────────────────────────

function ProtoCard({ proto }: { proto: Prototype }) {
  return (
    <div className="rounded-xl p-4" style={{ border: `1px solid ${C.border}` }}>
      <div className="flex items-start gap-2 mb-2.5">
        {proto.priority === 'high' && (
          <span className="text-xs rounded px-2 py-0.5 flex-shrink-0 mt-0.5"
                style={{ background: 'rgba(245,158,11,0.12)', color: '#fbbf24', border: '1px solid rgba(245,158,11,0.3)' }}>
            Priority
          </span>
        )}
        <div className="min-w-0">
          <span className="text-sm font-semibold" style={{ color: C.textBright }}>{proto.phenomProduct}</span>
          <span className="mx-2 text-xs" style={{ color: C.border }}>·</span>
          <span className="text-sm" style={{ color: C.dim }}>{proto.gap}</span>
          {proto.evidenceRef && <SourceLink url={proto.evidenceRef} sourceType="news" />}
        </div>
      </div>
      <p className="text-sm leading-relaxed" style={{ color: C.text }}>{proto.whatItDoes}</p>
      {proto.successMetric && (
        <p className="mt-2.5 text-xs" style={{ color: C.dim }}>
          <span className="font-semibold" style={{ color: C.muted }}>Success metric: </span>
          {proto.successMetric}
        </p>
      )}
    </div>
  )
}

// ── Summary column ────────────────────────────────────────────────────────────

function SummaryCol({ title, items, accentColor }: { title: string; items: PitchItem[]; accentColor: string }) {
  return (
    <div className="pl-4 py-1" style={{ borderLeft: `2px solid ${accentColor}` }}>
      <p className="text-sm font-semibold mb-3 uppercase tracking-wider" style={{ color: C.dim }}>{title}</p>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className="text-sm leading-relaxed" style={{ color: C.text }}>
            {bulletText(item)}
          </li>
        ))}
      </ul>
    </div>
  )
}

// ── Text-selection comment popup ──────────────────────────────────────────────

function SelectionPopup({ notes, onNotesChange }: { notes: string; onNotesChange: (t: string) => void }) {
  const [sel, setSel] = useState<{ text: string; x: number; y: number } | null>(null)
  const [comment, setComment] = useState('')
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current?.contains(e.target as Node)) return
      const selection = window.getSelection()
      const text = selection?.toString().trim() || ''
      if (text.length < 4) { setSel(null); return }
      try {
        const range = selection!.getRangeAt(0)
        const rect = range.getBoundingClientRect()
        setSel({ text, x: rect.left + rect.width / 2, y: rect.top })
      } catch { setSel(null) }
    }
    document.addEventListener('mouseup', handler)
    return () => document.removeEventListener('mouseup', handler)
  }, [])

  if (!sel) return null

  const excerpt = sel.text.length > 100 ? sel.text.slice(0, 100) + '…' : sel.text
  const left = Math.max(10, Math.min(sel.x - 128, window.innerWidth - 276))
  const top  = sel.y - 8

  const save = () => {
    if (!comment.trim()) return
    const entry = `> "${excerpt}"\n${comment.trim()}`
    onNotesChange(notes ? notes + '\n\n' + entry : entry)
    setSel(null)
    setComment('')
    window.getSelection()?.removeAllRanges()
  }

  const dismiss = () => { setSel(null); setComment('') }

  return (
    <div
      ref={panelRef}
      className="fixed z-[200] w-64 rounded-xl shadow-2xl p-3 scale-in"
      style={{ left, top, transform: 'translateY(-100%)', background: C.surface, border: `1px solid ${C.borderLt}` }}
    >
      <div className="flex items-start gap-1.5 mb-2">
        <MessageSquarePlus className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" style={{ color: C.violetLt }} />
        <p className="text-xs italic leading-relaxed flex-1 truncate" style={{ color: C.dim }}>"{excerpt}"</p>
      </div>
      <textarea
        className="w-full rounded-lg px-2.5 py-2 text-xs outline-none resize-none transition-colors"
        style={{ background: '#08080f', border: `1px solid ${C.border}`, color: C.textBright }}
        placeholder="Add a comment..."
        rows={3}
        autoFocus
        value={comment}
        onChange={e => setComment(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) save() }}
        onFocus={e => (e.target.style.borderColor = C.violet)}
        onBlur={e => (e.target.style.borderColor = C.border)}
      />
      <div className="flex justify-end gap-2 mt-2">
        <button onClick={dismiss} className="text-xs transition-colors" style={{ color: C.muted }}
          onMouseEnter={e => ((e.currentTarget as HTMLButtonElement).style.color = C.dim)}
          onMouseLeave={e => ((e.currentTarget as HTMLButtonElement).style.color = C.muted)}>
          Cancel
        </button>
        <button
          onClick={save}
          disabled={!comment.trim()}
          className="text-xs font-semibold px-2.5 py-1 rounded-md transition-colors"
          style={{ background: comment.trim() ? C.violet : C.raised, color: comment.trim() ? '#fff' : C.muted }}
        >
          Save to notes
        </button>
      </div>
    </div>
  )
}

// ── Main ──────────────────────────────────────────────────────────────────────

interface ResultsPageProps {
  result: ResearchResult
  notes: string
  onNotesChange: (text: string) => void
  onResearch: (company: string) => void
}

export function ResultsPage({ result, notes, onNotesChange }: ResultsPageProps) {
  const { bundle, analysis, fitScore } = result
  const company = analysis.company || bundle.company_name
  const dims = analysis.dimensions || {}
  const prototypes = analysis.solutionPrototypes || []
  const pitch = analysis.pitch || {}
  const stack = analysis.detectedStack

  const strengths: PitchItem[] = pitch.strengths?.length
    ? pitch.strengths
    : Object.values(dims)
        .filter(d => ['high', 'medium'].includes(d.coverage) && d.currentState && !d.gaps?.length)
        .map(d => d.currentState).slice(0, 4)

  const weaknesses: PitchItem[] = pitch.weaknesses?.length
    ? pitch.weaknesses
    : Object.values(dims).flatMap(d => d.gaps || []).slice(0, 4)

  const opportunities: PitchItem[] = pitch.opportunities?.length
    ? pitch.opportunities
    : prototypes.map(p => `${p.phenomProduct}: ${p.whatItDoes}`).slice(0, 4)

  // Group signals by dimension for TalentCards
  const signalsByDim = bundle.signals.reduce((acc, s) => {
    ;(acc[s.dimension] = acc[s.dimension] || []).push(s)
    return acc
  }, {} as Record<string, Signal[]>)

  // Classify signals for overview sections
  const financialSignals = bundle.signals.filter(s => s.source_type === 'filing')
  const maSignals        = bundle.signals.filter(s => s.signal_type === 'integration_complexity')
  const maContents       = new Set(maSignals.map(s => s.content))

  const classifyNews = (s: Signal): string => {
    const c = (s.content + ' ' + s.signal_type).toLowerCase()
    if (c.includes('layoff') || c.includes('rif') || c.includes('job cut')) return 'layoffs'
    if (s.signal_type === 'chro_change' || c.includes('chro') || c.includes('cpo') || c.includes('chief people')) return 'leadership'
    if (s.signal_type === 'ai_strategy' || c.includes(' ai ') || c.includes('llm') || c.includes('openai') || c.includes('anthropic')) return 'ai'
    if (c.includes('hiring') || c.includes('expan') || s.signal_type === 'growth_signal') return 'hiring'
    return 'general'
  }

  const newsByCategory: Record<string, Signal[]> = {}
  bundle.signals
    .filter(s => s.source_type === 'news' && !maContents.has(s.content))
    .forEach(s => { const cat = classifyNews(s); (newsByCategory[cat] = newsByCategory[cat] || []).push(s) })

  // Unique data sources for the overview "Sources" footer
  const overviewSources = [
    ...financialSignals, ...maSignals,
    ...Object.values(newsByCategory).flat(),
  ].reduce((acc, s) => {
    if (!acc.some(x => x.url === s.source_url)) acc.push({ url: s.source_url, type: s.source_type })
    return acc
  }, [] as { url: string; type: string }[])

  const mainDims: [string, string][] = [
    ['hiring', 'How they hire'],
    ['onboarding', 'Onboarding'],
    ['hrit', 'HRIT tools'],
    ['retention', 'Employee retention'],
  ]
  const extraDims: [string, string][] = [
    ['people_analytics', 'People analytics'],
    ['internal_mobility', 'Internal mobility'],
  ]

  return (
    <div className="max-w-5xl mx-auto px-8 py-10 slide-up">

      {/* Text selection popup — globally active on this page */}
      <SelectionPopup notes={notes} onNotesChange={onNotesChange} />

      {/* Company header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex-1 min-w-0 pr-6">
          <h1 className="text-4xl font-bold tracking-tight leading-tight" style={{ color: C.textBright }}>
            {company}
          </h1>
          {bundle.is_mock && (
            <span className="inline-block mt-2 text-xs rounded px-2 py-0.5"
                  style={{ color: C.muted, border: `1px solid ${C.border}` }}>
              Mock data
            </span>
          )}
        </div>
        <div className="flex-shrink-0 text-right">
          <div className={`text-5xl font-bold tabular-nums ${fitScoreColor(fitScore)}`}>
            {fitScore}
          </div>
          <div className="text-xs mt-1" style={{ color: C.dim }}>
            Phenom fit · {fitLabel(fitScore)}
          </div>
        </div>
      </div>

      {/* Top opportunity */}
      {analysis.topOpportunity && (
        <div className="pl-4 py-0.5 mb-6" style={{ borderLeft: `2px solid ${C.violet}` }}>
          <p className="text-sm" style={{ color: C.text }}>
            <span className="font-semibold" style={{ color: C.textBright }}>Top opportunity: </span>
            {analysis.topOpportunity}
          </p>
        </div>
      )}

      {/* ── Company overview ── */}
      <div className="rounded-xl overflow-hidden mb-8" style={{ background: C.surface, border: `1px solid ${C.border}` }}>

        {/* Key facts strip */}
        <div className="px-5 py-4 flex gap-8 flex-wrap" style={{ borderBottom: `1px solid ${C.border}` }}>
          {analysis.industry && (
            <div>
              <p className="text-xs mb-0.5" style={{ color: C.dim }}>Industry</p>
              <p className="text-sm font-semibold" style={{ color: C.textBright }}>{analysis.industry}</p>
            </div>
          )}
          {analysis.companySize && (
            <div>
              <p className="text-xs mb-0.5" style={{ color: C.dim }}>Employees</p>
              <p className="text-sm font-semibold" style={{ color: C.textBright }}>{analysis.companySize}</p>
            </div>
          )}
          {stack?.ats && (
            <div>
              <p className="text-xs mb-0.5" style={{ color: C.dim }}>ATS</p>
              <p className="text-sm font-semibold" style={{ color: C.textBright }}>
                {stack.ats}
                {stack.source && <SourceLink url={stack.source} sourceType="job_posting" />}
                <span className="font-normal text-xs ml-1.5" style={{ color: C.dim }}>
                  {to100(stack.confidence)}% confidence
                </span>
              </p>
            </div>
          )}
        </div>

        {/* Structured sections */}
        <div className="px-5 py-5 space-y-5">

          {analysis.description && (
            <OverviewSection title="What they do">
              <p className="text-sm leading-relaxed" style={{ color: C.text }}>{analysis.description}</p>
            </OverviewSection>
          )}

          {(financialSignals.length > 0 || (analysis.revenueHistory && analysis.revenueHistory.length >= 2)) && (
            <OverviewSection title="Financials">
              {analysis.revenueHistory && analysis.revenueHistory.length >= 2 && (
                <RevenueSparkline data={analysis.revenueHistory} />
              )}
              <div className="space-y-1.5">
                {financialSignals.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {newsByCategory.ai?.length > 0 && (
            <OverviewSection title="AI strategy">
              <div className="space-y-1.5">
                {newsByCategory.ai.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {newsByCategory.leadership?.length > 0 && (
            <OverviewSection title="Leadership">
              <div className="space-y-1.5">
                {newsByCategory.leadership.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {newsByCategory.layoffs?.length > 0 && (
            <OverviewSection title="Layoffs">
              <div className="space-y-1.5">
                {newsByCategory.layoffs.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {newsByCategory.hiring?.length > 0 && (
            <OverviewSection title="Hiring">
              <div className="space-y-1.5">
                {newsByCategory.hiring.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {maSignals.length > 0 && (
            <OverviewSection title="M&A">
              <div className="space-y-1.5">
                {maSignals.map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

          {newsByCategory.general?.length > 0 && (
            <OverviewSection title="Latest news">
              <div className="space-y-1.5">
                {newsByCategory.general.slice(0, 5).map((s, i) => (
                  <SignalBullet key={i} content={s.content} url={s.source_url} sourceType={s.source_type} />
                ))}
              </div>
            </OverviewSection>
          )}

        </div>

        {/* Sources footer */}
        {overviewSources.length > 0 && (
          <div className="px-5 py-3" style={{ borderTop: `1px solid ${C.border}` }}>
            <p className="text-xs mb-2" style={{ color: C.muted }}>Sources</p>
            <div className="flex flex-wrap gap-1.5">
              {overviewSources.map((s, i) => (
                <a key={i} href={s.url} target="_blank" rel="noopener noreferrer"
                   className="inline-flex items-center gap-1 text-xs rounded-md px-2 py-1 transition-colors"
                   style={{ background: C.raised, color: C.dim, border: `1px solid ${C.border}` }}
                   onMouseEnter={e => { (e.currentTarget as HTMLAnchorElement).style.color = C.violetLt; (e.currentTarget as HTMLAnchorElement).style.borderColor = C.violet }}
                   onMouseLeave={e => { (e.currentTarget as HTMLAnchorElement).style.color = C.dim; (e.currentTarget as HTMLAnchorElement).style.borderColor = C.border }}
                   title={s.url}
                >
                  <SourceIcon type={s.type} className="w-2.5 h-2.5" />
                  <span>{shortDomain(s.url)}</span>
                </a>
              ))}
            </div>
          </div>
        )}
      </div>

      <Divider />

      {/* Talent operations */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold mb-4" style={{ color: C.dim }}>Talent operations</h2>
        <div className="grid grid-cols-2 gap-3">
          {[...mainDims, ...extraDims].map(([key, label]) => {
            const d = dims[key]
            if (!d) return null
            return <TalentCard key={key} label={label} d={d} signals={signalsByDim[key] || []} />
          })}
        </div>
      </section>

      <Divider />

      {/* Sales pitch */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4" style={{ color: C.dim }}>Sales pitch</h2>
        <ul className="space-y-3">
          {pitch.hook && (
            <li className="flex gap-3 text-sm leading-relaxed" style={{ color: C.text }}>
              <span className="flex-shrink-0 mt-0.5" style={{ color: C.muted }}>·</span>
              <span>{pitch.hook}</span>
            </li>
          )}
          {prototypes.map((proto, i) => (
            <li key={i} className="flex gap-3 text-sm leading-relaxed" style={{ color: C.text }}>
              <span className="flex-shrink-0 mt-0.5" style={{ color: C.muted }}>·</span>
              <span>
                <span className="font-semibold" style={{ color: C.textBright }}>{proto.phenomProduct}: </span>
                {proto.whatItDoes}
                {proto.successMetric && (
                  <span className="block mt-1">{proto.successMetric}</span>
                )}
              </span>
            </li>
          ))}
          {pitch.roi && (
            <li className="flex gap-3 text-sm leading-relaxed" style={{ color: C.text }}>
              <span className="flex-shrink-0 mt-0.5" style={{ color: C.muted }}>·</span>
              <span>{pitch.roi}</span>
            </li>
          )}
          {pitch.cta && (
            <li className="flex gap-3 text-sm leading-relaxed" style={{ color: C.text }}>
              <span className="flex-shrink-0 mt-0.5" style={{ color: C.muted }}>·</span>
              <span><span className="font-semibold" style={{ color: C.textBright }}>Next step: </span>{pitch.cta}</span>
            </li>
          )}
        </ul>
      </section>

      <Divider />

      {/* Summary — final section */}
      <section className="mb-12">
        <h2 className="text-lg font-semibold mb-5" style={{ color: C.dim }}>Summary</h2>
        <div className="grid grid-cols-3 gap-6">
          <SummaryCol title="Doing well"    items={strengths}    accentColor="#34d399" />
          <SummaryCol title="Can do better" items={weaknesses}   accentColor="#fbbf24" />
          <SummaryCol title="Opportunity"   items={opportunities} accentColor={C.violet} />
        </div>
      </section>

    </div>
  )
}
