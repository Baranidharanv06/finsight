import { useState } from 'react'
import './App.css'

const API_BASE = 'http://127.0.0.1:8000'

function App() {
  const [ticker, setTicker] = useState('')
  const [ingesting, setIngesting] = useState(false)
  const [docs, setDocs] = useState([])
  const [activeDoc, setActiveDoc] = useState(null)
  const [ingestError, setIngestError] = useState(null)
  const [mode, setMode] = useState('chat') // 'chat' | 'compare'
  const [selectedForCompare, setSelectedForCompare] = useState([])

  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [messages, setMessages] = useState([])
  const [compareResult, setCompareResult] = useState(null)
  const [error, setError] = useState(null)

  const handleIngest = async () => {
    if (!ticker) return
    setIngesting(true)
    setIngestError(null)
    try {
      const res = await fetch(`${API_BASE}/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      const newDoc = { ticker: data.ticker, chunks: data.chunks_stored }
      setDocs((prev) => {
        const exists = prev.find((d) => d.ticker === newDoc.ticker)
        if (exists) return prev.map((d) => d.ticker === newDoc.ticker ? newDoc : d)
        return [...prev, newDoc]
      })
      setActiveDoc(newDoc.ticker)
      setMode('chat')
      setTicker('')
    } catch {
      setIngestError('Could not load ' + ticker)
    } finally {
      setIngesting(false)
    }
  }

  const handleQuery = async () => {
    if (!query || !activeDoc) return
    const userMessage = { role: 'user', text: query }
    setMessages((prev) => [...prev, userMessage])
    setQuery('')
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userMessage.text, ticker: activeDoc })
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', text: data.answer, sources: data.sources }])
    } catch {
      setError('Failed to get an answer. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = async () => {
    if (!query || selectedForCompare.length < 2) return
    setLoading(true)
    setCompareResult(null)
    setError(null)
    const q = query
    setQuery('')
    try {
      const res = await fetch(`${API_BASE}/compare`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, tickers: selectedForCompare })
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      setCompareResult({ query: q, answer: data.answer, sources: data.sources })
    } catch {
      setError('Comparison failed. Try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleCompareSelect = (ticker) => {
    setSelectedForCompare((prev) =>
      prev.includes(ticker) ? prev.filter((t) => t !== ticker) : [...prev, ticker]
    )
  }

  const exampleQueries = [
    'Summarize the main risk factors',
    'How did revenue change year over year?',
    'What are the biggest competitive threats?',
  ]

  const compareExamples = [
    'How does each company address AI regulation risk?',
    'Compare their supply chain risk disclosures',
    'How do they each describe their competitive position?',
  ]

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-name">FinSight</span>
          <span className="brand-sub">SEC filing analysis</span>
        </div>

        <div className="sidebar-section">
          <label className="sidebar-label">Add a filing</label>
          <div className="ticker-input-row">
            <input
              className="mono"
              placeholder="Ticker"
              value={ticker}
              maxLength={6}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === 'Enter' && handleIngest()}
            />
            <button onClick={handleIngest} disabled={ingesting || !ticker}>
              {ingesting ? '…' : '+'}
            </button>
          </div>
          {ingesting && <p className="sidebar-hint">Fetching 10-K from EDGAR...</p>}
          {ingestError && <p className="sidebar-error">{ingestError}</p>}
        </div>

        <div className="sidebar-section flex-grow">
          <div className="sidebar-label-row">
            <label className="sidebar-label">Loaded filings</label>
            {docs.length >= 2 && (
              <button
                className={`mode-toggle ${mode === 'compare' ? 'active' : ''}`}
                onClick={() => {
                  setMode(mode === 'compare' ? 'chat' : 'compare')
                  setSelectedForCompare([])
                  setCompareResult(null)
                }}
              >
                {mode === 'compare' ? 'Exit compare' : 'Compare'}
              </button>
            )}
          </div>

          {docs.length === 0 ? (
            <p className="sidebar-hint">No filings yet. Add a ticker above.</p>
          ) : (
            <div className="doc-list">
              {docs.map((doc) => (
                <button
                  key={doc.ticker}
                  className={`doc-item ${
                    mode === 'chat' && activeDoc === doc.ticker ? 'active' : ''
                  } ${mode === 'compare' && selectedForCompare.includes(doc.ticker) ? 'selected' : ''}`}
                  onClick={() => {
                    if (mode === 'compare') {
                      toggleCompareSelect(doc.ticker)
                    } else {
                      setActiveDoc(doc.ticker)
                      setMessages([])
                    }
                  }}
                >
                  {mode === 'compare' && (
                    <span className={`check ${selectedForCompare.includes(doc.ticker) ? 'checked' : ''}`}>
                      {selectedForCompare.includes(doc.ticker) ? '✓' : '○'}
                    </span>
                  )}
                  <span className="doc-ticker">{doc.ticker}</span>
                  <span className="doc-meta">{doc.chunks} chunks · 10-K</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="sidebar-footer">
          EDGAR → chunk → embed → Qdrant → rerank → Groq
        </div>
      </aside>

      <main className="main">
        {!activeDoc && mode === 'chat' ? (
          <div className="empty-state">
            <h1>FinSight</h1>
            <p>Load a company's 10-K filing on the left, then ask questions about it here.</p>
            <p className="empty-detail">Every answer is grounded in the actual filing text, with cited source chunks.</p>
          </div>
        ) : mode === 'compare' ? (
          <>
            <div className="chat-header">
              <div>
                <h2>Compare filings</h2>
                <p>
                  {selectedForCompare.length < 2
                    ? `Select ${2 - selectedForCompare.length} more filing${2 - selectedForCompare.length > 1 ? 's' : ''} from the sidebar`
                    : `Comparing ${selectedForCompare.join(' vs ')}`}
                </p>
              </div>
            </div>

            <div className="chat-thread">
              {!compareResult && !loading && selectedForCompare.length >= 2 && (
                <div className="examples">
                  <p className="examples-label">Try asking</p>
                  {compareExamples.map((q) => (
                    <button key={q} className="example-chip" onClick={() => setQuery(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {loading && (
                <div className="message assistant">
                  <div className="answer-block">
                    <div className="thinking">
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                    </div>
                  </div>
                </div>
              )}

              {compareResult && (
                <div className="compare-result fade-in">
                  <p className="compare-query">"{compareResult.query}"</p>
                  <p className="answer-text">{compareResult.answer}</p>
                  {compareResult.sources && (
                    <div className="sources">
                      {Object.entries(compareResult.sources).map(([ticker, chunks]) => (
                        chunks.length > 0 && (
                          <details key={ticker} className="source-chunk">
                            <summary>{ticker} sources</summary>
                            {chunks.map((c, i) => <p key={i}>{c}</p>)}
                          </details>
                        )
                      ))}
                    </div>
                  )}
                </div>
              )}

              {error && <div className="inline-error">{error}</div>}
            </div>

            <div className="composer">
              <input
                placeholder={
                  selectedForCompare.length < 2
                    ? 'Select 2 filings to compare...'
                    : `Compare ${selectedForCompare.join(' vs ')}...`
                }
                value={query}
                disabled={selectedForCompare.length < 2 || loading}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCompare()}
              />
              <button
                className="send"
                onClick={handleCompare}
                disabled={loading || !query || selectedForCompare.length < 2}
              >
                Compare
              </button>
            </div>
          </>
        ) : (
          <>
            <div className="chat-header">
              <div>
                <h2>{activeDoc}</h2>
                <p>Latest 10-K · {docs.find((d) => d.ticker === activeDoc)?.chunks} indexed chunks</p>
              </div>
            </div>

            <div className="chat-thread">
              {messages.length === 0 && (
                <div className="examples">
                  <p className="examples-label">Try asking</p>
                  {exampleQueries.map((q) => (
                    <button key={q} className="example-chip" onClick={() => setQuery(q)}>
                      {q}
                    </button>
                  ))}
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className={`message ${m.role}`}>
                  {m.role === 'user' ? (
                    <div className="message-bubble">{m.text}</div>
                  ) : (
                    <div className="answer-block">
                      <p className="answer-text">{m.text}</p>
                      {m.sources?.length > 0 && (
                        <div className="sources">
                          {m.sources.map((s, j) => (
                            <details key={j} className="source-chunk">
                              <summary>Source {j + 1}</summary>
                              <p>{s}</p>
                            </details>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}

              {loading && (
                <div className="message assistant">
                  <div className="answer-block">
                    <div className="thinking">
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                      <span className="thinking-dot" />
                    </div>
                  </div>
                </div>
              )}

              {error && <div className="inline-error">{error}</div>}
            </div>

            <div className="composer">
              <input
                placeholder={`Ask about ${activeDoc}'s 10-K...`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleQuery()}
              />
              <button className="send" onClick={handleQuery} disabled={loading || !query}>
                Send
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  )
}

export default App