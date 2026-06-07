import { useState, useEffect, useCallback } from 'react'
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { NotebookPen, X, Download, Check } from 'lucide-react'
import { Home } from './components/Home'
import { Sidebar } from './components/Sidebar'
import { ResultsPage } from './components/ResultsPage'
import { researchCompany } from './api'
import { fitScore as calcFitScore, buildExportMarkdown, slug } from './utils'
import type { ResearchResult } from './types'

const LOADING_STEPS = [
  'Searching the web',
  'Reading careers pages & job posts',
  'Detecting their ATS',
  'Analyzing talent operations',
  'Writing the sales pitch',
]

function LoadingScreen({ company }: { company: string }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    // Lock body scroll so the tall page behind this full-screen overlay doesn't
    // show a dead scrollbar while loading.
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    // Time-based progression — no real per-stage events from the backend, so the
    // dwell times roughly track the pipeline (fast search, slow synthesis). The
    // final step holds until the request resolves and this screen unmounts.
    const dwell = [5000, 5000, 4000, 40000]
    const timers: ReturnType<typeof setTimeout>[] = []
    let elapsed = 0
    dwell.forEach((d, i) => {
      elapsed += d
      timers.push(setTimeout(() => setStep(i + 1), elapsed))
    })
    return () => {
      timers.forEach(clearTimeout)
      document.body.style.overflow = prevOverflow
    }
  }, [])

  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center z-[100] overflow-hidden fade-in" style={{ background: '#08080f' }}>
      {/* Ambient glow */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: 'radial-gradient(circle at 50% 42%, rgba(124,58,237,0.16), transparent 60%)' }}
      />

      <div className="relative flex flex-col items-center text-center">
        <span className="text-sm font-semibold tracking-[0.25em] text-violet-400 uppercase mb-3">
          Researching
        </span>
        <h1 className="text-5xl sm:text-6xl font-bold text-white tracking-tight mb-3">{company}</h1>
        <p className="text-base mb-12" style={{ color: '#6a6aa0' }}>This usually takes a minute…</p>

        {/* Timeline */}
        <div className="relative flex flex-col gap-6 text-left">
          {/* connecting track */}
          <div className="absolute left-[11px] top-3 bottom-3 w-px" style={{ background: '#20203a' }} />
          {LOADING_STEPS.map((label, i) => {
            const done = i < step
            const active = i === step
            return (
              <div key={i} className="relative flex items-center gap-4">
                <span
                  className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 z-10 transition-colors"
                  style={{
                    background: done ? 'rgba(52,211,153,0.12)' : active ? 'rgba(124,58,237,0.18)' : '#0f0f1a',
                    border: `1px solid ${done ? '#34d399' : active ? '#7c3aed' : '#20203a'}`,
                  }}
                >
                  {done ? (
                    <Check className="w-3.5 h-3.5" style={{ color: '#34d399' }} />
                  ) : active ? (
                    <span className="w-3 h-3 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <span className="w-1.5 h-1.5 rounded-full" style={{ background: '#3a3a6a' }} />
                  )}
                </span>
                <span
                  className="text-lg"
                  style={{ color: done ? '#8080c0' : active ? '#e8e8ff' : '#4a4a78', fontWeight: active ? 600 : 400 }}
                >
                  {label}{active ? '…' : ''}
                </span>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function ErrorBanner({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 flex items-center gap-3 px-4 py-3 rounded-lg text-sm max-w-md shadow-xl"
         style={{ background: 'rgba(127,29,29,0.7)', border: '1px solid rgba(185,28,28,0.5)', color: '#fca5a5' }}>
      <span className="flex-1">{message}</span>
      <button onClick={onClose} className="hover:text-red-300 ml-2 flex-shrink-0 transition-colors" style={{ color: '#ef4444' }}>✕</button>
    </div>
  )
}

interface CompanyViewProps {
  history: ResearchResult[]
  notes: Record<string, string>
  loading: boolean
  sidebarCollapsed: boolean
  onToggleSidebar: () => void
  onResearch: (company: string) => void
  onUpdateNotes: (company: string, text: string) => void
}

// The /c/:slug route — sidebar + results for the company in the URL.
function CompanyView({
  history, notes, loading, sidebarCollapsed, onToggleSidebar, onResearch, onUpdateNotes,
}: CompanyViewProps) {
  const { slug: routeSlug } = useParams()
  const navigate = useNavigate()
  const [notesOpen, setNotesOpen] = useState(false)
  const [notesWidth, setNotesWidth] = useState(340)
  const [dragging, setDragging] = useState(false)

  // Drag-to-resize the notes drawer (drag its left edge).
  useEffect(() => {
    if (!dragging) return
    const onMove = (e: MouseEvent) => {
      setNotesWidth(Math.min(Math.max(window.innerWidth - e.clientX, 280), 640))
    }
    const onUp = () => setDragging(false)
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
    document.body.style.userSelect = 'none'
    document.body.style.cursor = 'ew-resize'
    return () => {
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
      document.body.style.userSelect = ''
      document.body.style.cursor = ''
    }
  }, [dragging])

  const result = history.find(h => slug(h.bundle.company_name) === routeSlug)

  // Company not in memory (e.g. a refresh / shared link — results aren't persisted).
  // Go back to Home, unless a fetch for it is currently in flight.
  if (!result) {
    return loading ? null : <Navigate to="/" replace />
  }

  const company = result.bundle.company_name
  const currentNotes = notes[company.toLowerCase()] || ''

  const handleExport = () => {
    const md = buildExportMarkdown(result.analysis, result.bundle, result.fitScore, currentNotes)
    const blob = new Blob([md], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${company.toLowerCase().replace(/\s+/g, '_')}_phenom_report.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex min-h-screen" style={{ background: '#08080f' }}>
      <Sidebar
        history={history}
        current={result}
        onSelect={r => navigate(`/c/${slug(r.bundle.company_name)}`)}
        collapsed={sidebarCollapsed}
        onToggle={onToggleSidebar}
        onResearch={onResearch}
      />

      <main
        className={`flex-1 min-h-screen ${sidebarCollapsed ? 'ml-12' : 'ml-60'}`}
        style={{ marginRight: notesOpen ? notesWidth : 0, transition: dragging ? 'none' : 'all 0.3s' }}
      >
        <ResultsPage key={company} result={result} />
      </main>

      {/* Top-right fixed toolbar */}
      <div className="fixed top-4 z-50 flex items-center gap-2"
           style={{ right: notesOpen ? notesWidth + 16 : 16, transition: dragging ? 'none' : 'right 0.3s' }}>
        {/* Export — prominent labeled button */}
        <button
          onClick={handleExport}
          className="flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
          style={{ background: '#7c3aed', color: '#fff' }}
          onMouseEnter={e => ((e.currentTarget as HTMLButtonElement).style.background = '#6d28d9')}
          onMouseLeave={e => ((e.currentTarget as HTMLButtonElement).style.background = '#7c3aed')}
        >
          <Download className="w-4 h-4" />
          Export
        </button>

        {/* Notes toggle */}
        <button
          onClick={() => setNotesOpen(v => !v)}
          title="Notes"
          className="w-9 h-9 flex items-center justify-center rounded-lg border transition-colors"
          style={{
            background: notesOpen ? '#7c3aed' : '#0f0f1a',
            border: notesOpen ? '1px solid #7c3aed' : '1px solid #2a2a50',
            color: notesOpen ? '#fff' : '#a0a0cc',
          }}
          onMouseEnter={e => { if (!notesOpen) { (e.currentTarget as HTMLButtonElement).style.borderColor = '#7c3aed'; (e.currentTarget as HTMLButtonElement).style.color = '#a78bfa' } }}
          onMouseLeave={e => { if (!notesOpen) { (e.currentTarget as HTMLButtonElement).style.borderColor = '#2a2a50'; (e.currentTarget as HTMLButtonElement).style.color = '#a0a0cc' } }}
        >
          <NotebookPen className="w-4 h-4" />
        </button>
      </div>

      {/* Notes — right side drawer (resizable) */}
      <div
        className="fixed top-0 right-0 h-screen z-40 flex flex-col"
        style={{
          width: notesOpen ? notesWidth : 0,
          overflow: 'hidden',
          background: '#0a0a14',
          borderLeft: notesOpen ? '1px solid #1e1e38' : 'none',
          transition: dragging ? 'none' : 'width 0.3s',
        }}
      >
        {/* Resize handle — drag the left edge */}
        {notesOpen && (
          <div
            onMouseDown={() => setDragging(true)}
            title="Drag to resize"
            className="absolute left-0 top-0 h-full w-1.5 cursor-ew-resize z-20 transition-colors"
            style={{ background: dragging ? '#7c3aed' : 'transparent' }}
            onMouseEnter={e => { if (!dragging) (e.currentTarget as HTMLDivElement).style.background = '#2a2a50' }}
            onMouseLeave={e => { if (!dragging) (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
          />
        )}
        {/* Inner wrapper keeps content width fixed while outer animates open/closed */}
        <div className="flex flex-col h-full" style={{ minWidth: notesWidth }}>
          <div className="flex items-center justify-between px-5 pt-5 pb-4 flex-shrink-0"
               style={{ borderBottom: '1px solid #1e1e38' }}>
            <div className="flex items-center gap-2.5 min-w-0">
              <span className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: 'rgba(124,58,237,0.15)', border: '1px solid #2a2a50' }}>
                <NotebookPen className="w-3.5 h-3.5" style={{ color: '#a78bfa' }} />
              </span>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-white leading-tight">Notes</h3>
                <p className="text-xs truncate" style={{ color: '#8585b8' }}>{company}</p>
              </div>
            </div>
            <button
              onClick={() => setNotesOpen(false)}
              title="Close notes"
              className="transition-colors flex-shrink-0"
              style={{ color: '#8585b8' }}
              onMouseEnter={e => ((e.currentTarget as HTMLButtonElement).style.color = '#a78bfa')}
              onMouseLeave={e => ((e.currentTarget as HTMLButtonElement).style.color = '#8585b8')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 px-4 py-4 overflow-hidden">
            <textarea
              value={currentNotes}
              onChange={e => onUpdateNotes(company, e.target.value)}
              placeholder="Add notes, talking points, or follow-up actions…"
              autoFocus={notesOpen}
              className="w-full h-full rounded-lg px-3.5 py-3 text-sm leading-relaxed outline-none resize-none transition-colors"
              style={{ background: '#0d0d16', border: '1px solid #1e1e38', color: '#c8c8f0', caretColor: '#a78bfa' }}
              onFocus={e => (e.currentTarget.style.borderColor = '#7c3aed')}
              onBlur={e => (e.currentTarget.style.borderColor = '#1e1e38')}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const [history, setHistory] = useState<ResearchResult[]>([])
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingCompany, setLoadingCompany] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(true)
  const navigate = useNavigate()

  const runResearch = useCallback(async (company: string) => {
    setLoading(true)
    setLoadingCompany(company)
    setError(null)
    try {
      const data = await researchCompany(company)
      const result: ResearchResult = {
        ...data,
        fitScore: calcFitScore(data.analysis),
        timestamp: new Date().toLocaleString('en-US', {
          month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
        }),
      }
      setHistory(prev => [
        result,
        ...prev.filter(h => h.bundle.company_name.toLowerCase() !== result.bundle.company_name.toLowerCase()),
      ])
      navigate(`/c/${slug(result.bundle.company_name)}`)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Research failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const updateNotes = useCallback((company: string, text: string) => {
    setNotes(prev => ({ ...prev, [company.toLowerCase()]: text }))
  }, [])

  return (
    <>
      {loading && <LoadingScreen company={loadingCompany} />}
      {error && <ErrorBanner message={error} onClose={() => setError(null)} />}

      <Routes>
        <Route
          path="/"
          element={
            <div style={{ background: '#08080f', minHeight: '100vh' }}>
              <Home onResearch={runResearch} />
            </div>
          }
        />
        <Route
          path="/c/:slug"
          element={
            <CompanyView
              history={history}
              notes={notes}
              loading={loading}
              sidebarCollapsed={sidebarCollapsed}
              onToggleSidebar={() => setSidebarCollapsed(v => !v)}
              onResearch={runResearch}
              onUpdateNotes={updateNotes}
            />
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}
