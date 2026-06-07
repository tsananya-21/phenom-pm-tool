import { useState, type FormEvent } from 'react'
import { ChevronLeft, ChevronRight, Search } from 'lucide-react'
import type { ResearchResult } from '../types'
import { fitScoreColor, fitLabel } from '../utils'

interface SidebarProps {
  history: ResearchResult[]
  current: ResearchResult | null
  onSelect: (result: ResearchResult) => void
  collapsed: boolean
  onToggle: () => void
  onResearch: (company: string) => void
}

export function Sidebar({ history, current, onSelect, collapsed, onToggle, onResearch }: SidebarProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onResearch(input.trim())
      setInput('')
    }
  }

  return (
    <aside
      className={`fixed left-0 top-0 h-screen flex flex-col z-40 transition-all duration-200 ${
        collapsed ? 'w-12' : 'w-60'
      }`}
      style={{ background: '#0a0a14', borderRight: '1px solid #1a1a30' }}
    >
      {collapsed ? (
        <div className="flex flex-col items-center pt-3 gap-2 h-full overflow-hidden">
          <button
            onClick={onToggle}
            title="Expand sidebar"
            className="w-8 h-8 flex items-center justify-center text-[#5a5a8a] hover:text-violet-400 transition-colors flex-shrink-0"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <div className="w-6 h-px flex-shrink-0" style={{ background: '#1a1a30' }} />
          <button
            onClick={onToggle}
            title="Research a company"
            className="w-8 h-8 flex items-center justify-center text-[#5a5a8a] hover:text-violet-400 transition-colors flex-shrink-0"
          >
            <Search className="w-3.5 h-3.5" />
          </button>
          {history.length > 0 && <div className="w-6 h-px flex-shrink-0" style={{ background: '#1a1a30' }} />}
          {history.map(h => {
            const isActive = current?.bundle.company_name === h.bundle.company_name
            return (
              <button
                key={h.bundle.company_name}
                onClick={() => onSelect(h)}
                title={`${h.bundle.company_name} · ${h.fitScore}`}
                className={`w-8 h-8 rounded-md text-xs font-bold flex items-center justify-center transition-colors flex-shrink-0 ${
                  isActive
                    ? 'bg-violet-600 text-white'
                    : 'text-[#5050a0] hover:text-violet-400 hover:bg-violet-950/40'
                }`}
                style={!isActive ? { background: '#14142a' } : {}}
              >
                {h.bundle.company_name[0]}
              </button>
            )
          })}
        </div>
      ) : (
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="px-4 py-4 flex items-center justify-between flex-shrink-0" style={{ borderBottom: '1px solid #1a1a30' }}>
            <div className="flex items-center gap-2.5 min-w-0">
              <span className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 text-sm font-bold text-white"
                    style={{ background: 'linear-gradient(135deg,#7c3aed,#5b21b6)' }}>
                P
              </span>
              <div className="min-w-0">
                <div className="text-sm font-bold text-white tracking-tight leading-tight">Phenom PM</div>
                <div className="text-xs" style={{ color: '#5a5a8a' }}>Intelligence Tool</div>
              </div>
            </div>
            <button
              onClick={onToggle}
              title="Collapse sidebar"
              className="text-[#5a5a8a] hover:text-violet-400 transition-colors p-1 flex-shrink-0 ml-2"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
          </div>

          {/* Research input */}
          <div className="px-3 py-3 flex-shrink-0" style={{ borderBottom: '1px solid #1a1a30' }}>
            <form onSubmit={handleSubmit}>
              <div className="flex gap-1.5">
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  placeholder="Research a company…"
                  className="flex-1 rounded-lg px-3 py-2 text-xs text-white placeholder:text-[#5a5a8a] outline-none transition-colors"
                  style={{ background: '#14142a', border: '1px solid #1e1e38' }}
                  onFocus={e => (e.target.style.borderColor = '#7c3aed')}
                  onBlur={e => (e.target.style.borderColor = '#1e1e38')}
                />
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="bg-violet-600 hover:bg-violet-500 disabled:opacity-30 text-white text-sm font-semibold px-3 py-2 rounded-lg transition-colors flex-shrink-0"
                >
                  →
                </button>
              </div>
            </form>
          </div>

          {/* History */}
          <div className="flex-1 overflow-y-auto py-2 px-2">
            {history.length === 0 ? (
              <p className="px-3 py-6 text-xs leading-relaxed" style={{ color: '#5a5a8a' }}>
                Researched companies appear here.
              </p>
            ) : (
              <>
                <p className="px-3 pt-2 pb-1.5 text-xs font-semibold uppercase tracking-wider" style={{ color: '#5a5a8a' }}>Recent</p>
                {history.map(h => {
                  const isActive = current?.bundle.company_name === h.bundle.company_name
                  return (
                    <button
                      key={h.bundle.company_name}
                      onClick={() => onSelect(h)}
                      className="w-full text-left px-3 py-2.5 rounded-lg mb-0.5 transition-colors"
                      style={{ background: isActive ? 'rgba(124,58,237,0.14)' : 'transparent' }}
                      onMouseEnter={e => { if (!isActive) (e.currentTarget as HTMLButtonElement).style.background = '#12121f' }}
                      onMouseLeave={e => { if (!isActive) (e.currentTarget as HTMLButtonElement).style.background = 'transparent' }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className={`text-sm truncate font-medium ${isActive ? 'text-violet-200' : 'text-[#9090c8]'}`}>
                          {h.bundle.company_name}
                        </span>
                        <span className={`text-xs font-bold tabular-nums flex-shrink-0 px-1.5 py-0.5 rounded-md ${fitScoreColor(h.fitScore)}`}
                              style={{ background: '#14142a' }}>
                          {h.fitScore}
                        </span>
                      </div>
                      <div className="text-xs mt-1" style={{ color: '#5a5a8a' }}>{fitLabel(h.fitScore)} · {h.timestamp}</div>
                    </button>
                  )
                })}
              </>
            )}
          </div>
        </div>
      )}
    </aside>
  )
}
