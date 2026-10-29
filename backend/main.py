import math

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.fetcher.sec import get_cik, get_latest_10k_text
from backend.chunker.chunk import chunk_text
from backend.embedder.embed import embed_texts
from backend.retriever.store import init_collection, upsert_chunks, search, delete_ticker
from backend.retriever.rerank import rerank
from backend.retriever.generate import generate_answer, generate_comparison

# ACRE: exposure scoring + identity
from backend.acre import Chunk, ClearanceLevel, score_chunks, tag_sensitivity
from backend.auth import get_clearance, get_caller
from backend.audit import log_disclosure
from backend.storage import save_filing

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


def _norm(score: float) -> float:
    """ACRE expects relevance in 0..1. If the reranker gives raw scores, squash them."""
    if 0.0 <= score <= 1.0:
        return float(score)
    score = max(-30.0, min(30.0, float(score)))
    return 1.0 / (1.0 + math.exp(-score))


def retrieve_and_rerank(query: str, ticker: str, top_k_retrieve: int = 10, top_k_rerank: int = 3):
    query_vector = embed_texts([query])[0]
    results = search(query_vector, top_k=top_k_retrieve, ticker=ticker)
    candidate_texts = [r.payload["text"] for r in results]
    if not candidate_texts:
        return []
    reranked = rerank(query, candidate_texts, top_k=top_k_rerank)

    sensitivity_by_text = {r.payload["text"]: r.payload.get("sensitivity", 0) for r in results}

    return [
        (text, _norm(score), sensitivity_by_text.get(text, 0))
        for text, score in reranked
    ]


@app.post("/ingest")
def ingest(req: IngestRequest, caller: dict = Depends(get_caller)):
    if caller["clearance"] < ClearanceLevel.MANAGER:
        raise HTTPException(status_code=403, detail="Ingest requires MANAGER clearance or higher")
    ticker = req.ticker.upper()
    cik = get_cik(ticker)
    text = get_latest_10k_text(cik)
    s3_key = save_filing(ticker, text)  # raw filing -> S3 (None if not configured)
    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    sensitivities = [int(tag_sensitivity(c)) for c in chunks]

    delete_ticker(ticker)
    upsert_chunks(
        chunks,
        vectors,
        metadata={"ticker": ticker, "doc_type": "10-K"},
        per_chunk_metadata=[{"sensitivity": s} for s in sensitivities],
    )

    return {"ticker": ticker, "chunks_stored": len(chunks), "s3_key": s3_key}


@app.post("/query")
def query(req: QueryRequest, caller: dict = Depends(get_caller)):
    clearance = caller["clearance"]
    top_chunks = retrieve_and_rerank(req.query, req.ticker.upper())
    if not top_chunks:
        return {"answer": "No indexed content found for this ticker. Try loading the filing first.", "sources": []}

    chunk_objs = [
        Chunk(id=str(i), text=text, relevance_score=score, sensitivity=sensitivity)
        for i, (text, score, sensitivity) in enumerate(top_chunks)
    ]
    scored = score_chunks(chunk_objs, clearance)
    context_texts = [s.content_for_llm for s in scored]

    disclosure_log = [
        {"id": s.chunk.id, "sensitivity": int(s.chunk.sensitivity), "relevance": round(s.chunk.relevance_score, 2),
         "score": round(s.exposure_score, 2), "decision": s.decision.name}
        for s in scored
    ]
    # Audit first: the decision is recorded before anything is sent to the LLM.
    request_id = log_disclosure(caller["sub"], clearance.name, req.ticker.upper(), req.query, disclosure_log)

    answer = generate_answer(req.query, context_texts)
    return {
        "answer": answer,
        "sources": context_texts,
        "clearance": clearance.name,
        "request_id": request_id,
        "disclosure_log": disclosure_log,
    }


@app.post("/compare")
def compare(req: CompareRequest, clearance: ClearanceLevel = Depends(get_clearance)):
    tickers = [t.upper() for t in req.tickers]
    per_company_chunks = {}

    for ticker in tickers:
        raw_chunks = retrieve_and_rerank(req.query, ticker, top_k_rerank=2)
        chunk_objs = [
            Chunk(id=f"{ticker}-{i}", text=text, relevance_score=score, sensitivity=sensitivity)
            for i, (text, score, sensitivity) in enumerate(raw_chunks)
        ]
        scored = score_chunks(chunk_objs, clearance)
        per_company_chunks[ticker] = [s.content_for_llm for s in scored]

    answer = generate_comparison(req.query, per_company_chunks)
    return {"answer": answer, "sources": per_company_chunks}


@app.get("/health")
def health():
    return {"status": "ok"}
