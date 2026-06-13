from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.fetcher.sec import get_cik, get_latest_10k_text
from backend.chunker.chunk import chunk_text
from backend.embedder.embed import embed_texts
from backend.retriever.store import init_collection, upsert_chunks, search
from backend.retriever.rerank import rerank
from backend.retriever.generate import generate_answer

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
    ticker: str = None


@app.post("/ingest")
def ingest(req: IngestRequest):
    cik = get_cik(req.ticker)
    text = get_latest_10k_text(cik)
    chunks = chunk_text(text)
    vectors = embed_texts(chunks)

    upsert_chunks(chunks, vectors, metadata={
        "ticker": req.ticker.upper(),
        "doc_type": "10-K"
    })

    return {
        "ticker": req.ticker.upper(),
        "chunks_stored": len(chunks)
    }


@app.post("/query")
def query(req: QueryRequest):
    query_vector = embed_texts([req.query])[0]
    results = search(query_vector, top_k=10)

    candidate_texts = [r.payload["text"] for r in results]
    reranked = rerank(req.query, candidate_texts, top_k=3)
    top_chunks = [text for text, score in reranked]

    answer = generate_answer(req.query, top_chunks)

    return {
        "answer": answer,
        "sources": top_chunks
    }


@app.get("/health")
def health():
    return {"status": "ok"}