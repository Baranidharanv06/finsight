from sentence_transformers import CrossEncoder

_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query: str, chunks: list[str], top_k: int = 3) -> list[tuple[str, float]]:
    """
    Re-score chunks against the query using a cross-encoder.
    Returns top_k (chunk, score) pairs sorted by relevance.
    """
    pairs = [[query, chunk] for chunk in chunks]
    scores = _reranker.predict(pairs)

    scored = list(zip(chunks, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[:top_k]