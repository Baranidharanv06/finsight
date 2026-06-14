import { useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [ticker, setTicker] = useState('')
  const [ingesting, setIngesting] = useState(false)
  const [ingestStatus, setIngestStatus] = useState('')

  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])

  const handleIngest = async () => {
    if (!ticker) return
    setIngesting(true)
    setIngestStatus('')
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      })
      const data = await res.json()
      setIngestStatus(`Loaded ${data.chunks_stored} chunks for ${data.ticker}`)
    } catch (err) {
      setIngestStatus('Error: ' + err.message)
    } finally {
      setIngesting(false)
    }
  }

  const handleQuery = async () => {
    if (!query) return
    setLoading(true)
    setAnswer('')
    setSources([])
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources)
    } catch (err) {
      setAnswer('Error: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <h1>FinSight</h1>
      <p className="subtitle">RAG over SEC filings</p>

      <div className="card">
        <h2>1. Load a company filing</h2>
        <div className="row">
          <input
            placeholder="Ticker (e.g. AAPL)"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
          />
          <button onClick={handleIngest} disabled={ingesting}>
            {ingesting ? 'Loading...' : 'Load 10-K'}
          </button>
        </div>
        {ingestStatus && <p className="status">{ingestStatus}</p>}
      </div>

      <div className="card">
        <h2>2. Ask a question</h2>
        <div className="row">
          <input
            placeholder="e.g. What are the main risk factors?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          />
          <button onClick={handleQuery} disabled={loading}>
            {loading ? 'Thinking...' : 'Ask'}
          </button>
        </div>

        {answer && (
          <div className="answer">
            <h3>Answer</h3>
            <p>{answer}</p>
          </div>
        )}

        {sources.length > 0 && (
          <div className="sources">
            <h3>Sources</h3>
            {sources.map((s, i) => (
              <div key={i} className="source-chunk">
                {s.slice(0, 300)}...
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default App