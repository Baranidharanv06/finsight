from .models import Chunk, ScoredChunk, DisclosureDecision, ClearanceLevel

SUMMARY_FLOOR = 0.15
GAP_PENALTY_PER_LEVEL = 0.35
MAX_PARTIAL_EXPOSURE = 0.99


def compute_exposure_score(relevance: float, sensitivity: int, clearance: int) -> float:
    gap = max(0, int(sensitivity) - int(clearance))
    if gap == 0:
        return 1.0
    score = relevance - gap * GAP_PENALTY_PER_LEVEL
    return max(0.0, min(MAX_PARTIAL_EXPOSURE, score))


def decide(score: float) -> DisclosureDecision:
    if score >= 1.0:
        return DisclosureDecision.FULL
    if score >= SUMMARY_FLOOR:
        return DisclosureDecision.SUMMARY
    return DisclosureDecision.REDACTED


def score_chunk(chunk: Chunk, clearance: ClearanceLevel) -> ScoredChunk:
    score = compute_exposure_score(chunk.relevance_score, int(chunk.sensitivity), int(clearance))
    return ScoredChunk(chunk=chunk, exposure_score=score, decision=decide(score))


def score_chunks(chunks: list[Chunk], clearance: ClearanceLevel) -> list[ScoredChunk]:
    return [score_chunk(c, clearance) for c in chunks]
