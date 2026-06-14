import { useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [ticker, setTicker] = useState('')
  const [ingesting, setIngesting] = useState(false)
  const [ingestStatus, setIngestStatus] = useState(null)
  const [loadedTicker, setLoadedTicker] = useState(null)

  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [error, setError] = useState(null)

  const handleIngest = async () => {
    if (!ticker) return
    setIngesting(true)
    setIngestStatus(null)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      })
      if (!res.ok) throw new Error('Failed to load filing')
      const data = await res.json()
      setIngestStatus(data.chunks_stored)
      setLoadedTicker(data.ticker)
    } catch (err) {
      setError('Could not load filing for ' + ticker + '. Check the ticker and try again.')
    } finally {
      setIngesting(false)
    }
  }

  const handleQuery = async () => {
    if (!query || !loadedTicker) return
    setLoading(true)
    setAnswer('')
    setSources([])
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      if (!res.ok) throw new Error('Query failed')
      const data = await res.json()
      setAnswer(data.answer)
      setSources(data.sources)
    } catch (err) {
      setError('Something went wrong answering your question. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const exampleQueries = [
    'What are the main risk factors?',
    'How did revenue change year over year?',
    'What does the company say about AI investments?'
  ]

  return (
    <div className="app">
      <header className="header">
        <div className="logo">
          <div className="logo-mark">FS</div>
          <div>
            <h1>FinSight</h1>
            <p className="tagline">Retrieval-augmented Q&A over SEC filings</p>
          </div>
        </div>
        {loadedTicker && (
          <div className="active-doc">
            <span className="dot" />
            {loadedTicker} · 10-K loaded
          </div>
        )}
      </header>

      <section className="card">
        <div className="card-label">Step 1</div>
        <h2>Load a company filing</h2>
        <p className="card-desc">
          Enter a US stock ticker. We'll fetch the latest 10-K from SEC EDGAR,
          chunk it, and index it for retrieval.
        </p>
        <div className="row">
          <input
            className="mono"
            placeholder="AAPL"
            value={ticker}
            maxLength={6}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === 'Enter' && handleIngest()}
          />
          <button className="primary" onClick={handleIngest} disabled={ingesting || !ticker}>
            {ingesting ? <span className="spinner" /> : 'Load 10-K'}
          </button>
        </div>
        {ingesting && <p className="hint">Fetching filing, chunking, and embedding — this can take up to a minute...</p>}
        {ingestStatus !== null && (
          <p className="status success">
            Indexed {ingestStatus} chunks from {loadedTicker}'s 10-K
          </p>
        )}
      </section>

      <section className={`card ${!loadedTicker ? 'disabled' : ''}`}>
        <div className="card-label">Step 2</div>
        <h2>Ask a question</h2>
        <p className="card-desc">
          {loadedTicker
            ? `Ask anything about ${loadedTicker}'s latest annual report.`
            : 'Load a filing above to get started.'}
        </p>

        {!answer && !loading && loadedTicker && (
          <div className="examples">
            {exampleQueries.map((q) => (
              <button key={q} className="example-chip" onClick={() => { setQuery(q); }}>
                {q}
              </button>
            ))}
          </div>
        )}

        <div className="row">
          <input
            placeholder="What are the main risk factors?"
            value={query}
            disabled={!loadedTicker}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
          />
          <button className="primary" onClick={handleQuery} disabled={loading || !query || !loadedTicker}>
            {loading ? <span className="spinner" /> : 'Ask'}
          </button>
        </div>

        {loading && (
          <div className="loading-state">
            <div className="loading-step">Retrieving relevant sections...</div>
          </div>
        )}

        {answer && (
          <div className="answer fade-in">
            <h3>Answer</h3>
            <p>{answer}</p>
          </div>
        )}

        {sources.length > 0 && (
          <div className="sources fade-in">
            <h3>Sources <span className="source-count">{sources.length}</span></h3>
            {sources.map((s, i) => (
              <details key={i} className="source-chunk">
                <summary>Source {i + 1}</summary>
                <p>{s}</p>
              </details>
            ))}
          </div>
        )}
      </section>

      {error && <div className="error-toast">{error}</div>}

      <footer className="footer">
        Built with FastAPI, Qdrant, sentence-transformers, and Groq · Data from SEC EDGAR
      </footer>
    </div>
  )
}

export default App