import math

from sentence_transformers import CrossEncoder

_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")


def _sigmoid(x: float) -> float:
    x = max(-30.0, min(30.0, float(x)))
    return 1.0 / (1.0 + math.exp(-x))


def rerank(query: str, chunks: list[str], top_k: int = 3) -> list[tuple[str, float]]:
    """
    Re-score chunks against the query using a cross-encoder.
    Returns top_k (chunk, relevance) pairs sorted by relevance.

    The model outputs raw logits, which are often negative even for good
    matches on vague queries. So relevance is scaled to 0..1 across the
    candidate set (best candidate = 1.0, worst = 0.0). It is a relative
    ranking signal, not an absolute probability. If all candidates score the
    same (or there is only one), fall back to a sigmoid of the raw score.
    """
    if not chunks:
        return []

    pairs = [[query, chunk] for chunk in chunks]
    raw = [float(s) for s in _reranker.predict(pairs)]

    lo, hi = min(raw), max(raw)
    if hi - lo < 1e-6:
        relevance = [_sigmoid(s) for s in raw]
    else:
        relevance = [(s - lo) / (hi - lo) for s in raw]

    scored = list(zip(chunks, relevance))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]
