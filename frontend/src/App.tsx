import { useState, useCallback } from 'react'
import { Routes, Route, Navigate, useNavigate, useParams } from 'react-router-dom'
import { NotebookPen, X, Download } from 'lucide-react'
import { Home } from './components/Home'
import { Sidebar } from './components/Sidebar'
import { ResultsPage } from './components/ResultsPage'
import { researchCompany } from './api'
import { fitScore as calcFitScore, buildExportMarkdown, slug } from './utils'
import type { ResearchResult } from './types'

function LoadingScreen({ company }: { company: string }) {
  return (
    <div className="fixed inset-0 flex flex-col items-center justify-center z-50 fade-in" style={{ background: '#08080f' }}>
      <div className="w-5 h-5 border-2 border-violet-500 border-t-transparent rounded-full animate-spin mb-4" />
      <p className="text-sm" style={{ color: '#6060a0' }}>
        Researching <span className="text-white font-medium">{company}</span>
      </p>
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
        className={`flex-1 min-h-screen transition-all duration-300 ${sidebarCollapsed ? 'ml-12' : 'ml-60'}`}
        style={{ marginRight: notesOpen ? '288px' : '0' }}
      >
        <ResultsPage
          key={company}
          result={result}
          notes={currentNotes}
          onNotesChange={text => onUpdateNotes(company, text)}
          onResearch={onResearch}
        />
      </main>

      {/* Top-right fixed toolbar */}
      <div className="fixed top-4 z-50 flex items-center gap-2"
           style={{ right: notesOpen ? '304px' : '16px', transition: 'right 0.3s' }}>
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

      {/* Notes — right side drawer */}
      <div
        className="fixed top-0 right-0 h-screen z-40 flex flex-col transition-all duration-300"
        style={{
          width: notesOpen ? '288px' : '0',
          overflow: 'hidden',
          background: '#0a0a14',
          borderLeft: notesOpen ? '1px solid #1e1e38' : 'none',
        }}
      >
        {/* Inner wrapper keeps content at fixed width while outer animates */}
        <div className="flex flex-col h-full" style={{ minWidth: '288px' }}>
          <div className="flex items-center justify-between px-5 pt-5 pb-4 flex-shrink-0"
               style={{ borderBottom: '1px solid #1e1e38' }}>
            <div>
              <h3 className="text-sm font-semibold text-white">Notes</h3>
              <p className="text-xs mt-0.5" style={{ color: '#a0a0cc' }}>{company}</p>
            </div>
            <button
              onClick={() => setNotesOpen(false)}
              className="transition-colors"
              style={{ color: '#8585b8' }}
              onMouseEnter={e => ((e.currentTarget as HTMLButtonElement).style.color = '#a78bfa')}
              onMouseLeave={e => ((e.currentTarget as HTMLButtonElement).style.color = '#8585b8')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <textarea
            value={currentNotes}
            onChange={e => onUpdateNotes(company, e.target.value)}
            placeholder="Add notes, talking points, or follow-up actions."
            autoFocus={notesOpen}
            className="flex-1 w-full px-5 py-4 text-sm outline-none resize-none"
            style={{
              background: 'transparent',
              color: '#c8c8f0',
              caretColor: '#a78bfa',
            }}
          />
          <div className="px-5 py-3 text-xs flex-shrink-0" style={{ color: '#5858a0', borderTop: '1px solid #1e1e38' }}>
            Selected text → comment adds to notes
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
