import { useState, useEffect, type FormEvent } from 'react'
import { fetchCompanies } from '../api'

interface HomeProps {
  onResearch: (company: string) => void
}

export function Home({ onResearch }: HomeProps) {
  const [input, setInput] = useState('')
  const [companies, setCompanies] = useState<string[]>([])

  useEffect(() => {
    fetchCompanies().then(setCompanies).catch(() => {})
  }, [])

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    if (input.trim()) onResearch(input.trim())
  }

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden fade-in">
      {/* Ambient glow — fills the empty canvas */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{ background: 'radial-gradient(circle at 50% 38%, rgba(124,58,237,0.16), transparent 60%)' }}
      />

      <div className="relative w-full max-w-2xl flex flex-col items-center text-center">
        <span className="text-xs font-semibold tracking-[0.25em] text-violet-400 uppercase mb-6">
          Phenom Intelligence
        </span>

        <h1 className="text-6xl sm:text-7xl font-extrabold text-white tracking-tight leading-[1.04] text-balance mb-6">
          PM <span className="text-violet-400">Research</span> Tool
        </h1>

        <p className="text-lg leading-relaxed mb-10 max-w-xl text-balance" style={{ color: '#8a8ac0' }}>
          Enter a company name. Get a full picture of their talent operations,
          gaps, and where Phenom fits.
        </p>

        <form onSubmit={handleSubmit} className="w-full max-w-xl flex gap-2.5 mb-7">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Company name…"
            autoFocus
            className="flex-1 bg-[#0f0f1a] border border-[#1e1e38] focus:border-violet-500 rounded-xl px-5 py-4 text-white placeholder:text-[#5a5a8a] text-base outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="bg-violet-600 hover:bg-violet-500 disabled:bg-[#1a1a30] disabled:text-[#5a5a8a] text-white text-base font-semibold px-7 py-4 rounded-xl transition-colors flex-shrink-0"
          >
            Research
          </button>
        </form>

        {companies.length > 0 && (
          <div className="flex items-center justify-center gap-2 flex-wrap">
            <span className="text-sm mr-1" style={{ color: '#5a5a8a' }}>Try</span>
            {companies.map(name => (
              <button
                key={name}
                onClick={() => onResearch(name)}
                className="text-sm px-3 py-1.5 rounded-full transition-colors"
                style={{ background: '#14142a', color: '#9090c8', border: '1px solid #20203a' }}
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#c4b5fd'; (e.currentTarget as HTMLButtonElement).style.borderColor = '#7c3aed' }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#9090c8'; (e.currentTarget as HTMLButtonElement).style.borderColor = '#20203a' }}
              >
                {name}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
