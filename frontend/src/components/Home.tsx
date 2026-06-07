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
    <div className="min-h-screen flex flex-col items-center justify-center px-4 fade-in">
      <div className="w-full max-w-md">

        <div className="mb-1">
          <span className="text-xs font-semibold tracking-widest text-violet-500 uppercase">Phenom Intelligence</span>
        </div>
        <h1 className="text-5xl font-bold text-white tracking-tight leading-none mb-4">
          PM<br />
          <span className="text-violet-400">Research</span> Tool
        </h1>
        <p className="text-[#6060a0] text-sm leading-relaxed mb-10 max-w-sm">
          Enter a company name. Get a full picture of their talent operations,
          gaps, and where Phenom fits.
        </p>

        <form onSubmit={handleSubmit} className="flex gap-2 mb-8">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Company name"
            autoFocus
            className="flex-1 bg-[#0f0f1a] border border-[#1e1e38] focus:border-violet-500 rounded-lg px-4 py-3 text-white placeholder:text-[#3a3a6a] text-sm outline-none transition-colors"
          />
          <button
            type="submit"
            disabled={!input.trim()}
            className="bg-violet-600 hover:bg-violet-500 disabled:bg-[#1a1a30] disabled:text-[#3a3a6a] text-white text-sm font-semibold px-6 py-3 rounded-lg transition-colors flex-shrink-0"
          >
            Research
          </button>
        </form>

        {companies.length > 0 && (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-[#3a3a6a] text-xs">Try</span>
            {companies.map(name => (
              <button
                key={name}
                onClick={() => onResearch(name)}
                className="text-[#6060a0] hover:text-violet-400 text-sm transition-colors"
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
