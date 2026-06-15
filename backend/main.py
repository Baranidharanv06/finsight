from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.fetcher.sec import get_cik, get_latest_10k_text
from backend.chunker.chunk import chunk_text
from backend.embedder.embed import embed_texts
from backend.retriever.store import init_collection, upsert_chunks, search, delete_ticker
from backend.retriever.rerank import rerank
from backend.retriever.generate import generate_answer, generate_comparison

app = FastAPI(title="FinSight API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_collection()


class IngestRequest(BaseModel):
    ticker: str


class QueryRequest(BaseModel):
    query: str
    ticker: str


class CompareRequest(BaseModel):
    query: str
    tickers: list[str]


def retrieve_and_rerank(query: str, ticker: str, top_k_retrieve: int = 10, top_k_rerank: int = 3):
    query_vector = embed_texts([query])[0]
    results = search(query_vector, top_k=top_k_retrieve, ticker=ticker)
    candidate_texts = [r.payload["text"] for r in results]
    if not candidate_texts:
        return []
    reranked = rerank(query, candidate_texts, top_k=top_k_rerank)
    return [text for text, score in reranked]


@app.post("/ingest")
def ingest(req: IngestRequest):
    ticker = req.ticker.upper()
    cik = get_cik(ticker)
    text = get_latest_10k_text(cik)
    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    delete_ticker(ticker)
    upsert_chunks(chunks, vectors, metadata={"ticker": ticker, "doc_type": "10-K"})

    return {"ticker": ticker, "chunks_stored": len(chunks)}


@app.post("/query")
def query(req: QueryRequest):
    top_chunks = retrieve_and_rerank(req.query, req.ticker.upper())
    if not top_chunks:
        return {"answer": "No indexed content found for this ticker. Try loading the filing first.", "sources": []}

    answer = generate_answer(req.query, top_chunks)
    return {"answer": answer, "sources": top_chunks}


@app.post("/compare")
def compare(req: CompareRequest):
    tickers = [t.upper() for t in req.tickers]
    per_company_chunks = {}

    for ticker in tickers:
        chunks = retrieve_and_rerank(req.query, ticker, top_k_rerank=2)
        per_company_chunks[ticker] = chunks

    answer = generate_comparison(req.query, per_company_chunks)
    return {"answer": answer, "sources": per_company_chunks}


@app.get("/health")
def health():
    return {"status": "ok"}