"""
Core data models for ACRE (Adaptive Clearance-Aware Retrieval Engine).

These are deliberately simple, ordered enums so that "higher" sensitivity
and "higher" clearance can be compared numerically — this is what lets the
scoring function in scorer.py treat them as continuous inputs instead of
hardcoding a lookup table per combination.
"""

from dataclasses import dataclass
from enum import IntEnum


class SensitivityTier(IntEnum):
    """How sensitive a chunk's content is, assigned at ingestion time."""
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    RESTRICTED = 3


class ClearanceLevel(IntEnum):
    """The requester's access level. Mirrors SensitivityTier on purpose —
    a requester can only fully see chunks at or below their own level."""
    GUEST = 0
    EMPLOYEE = 1
    MANAGER = 2
    EXECUTIVE = 3


class DisclosureDecision(IntEnum):
    """What ACRE decided to do with a given chunk for this query."""
    FULL = 0
    SUMMARY = 1
    REDACTED = 2


@dataclass
class Chunk:
    """A single retrieved chunk, as it would come back from Qdrant/the
    retriever, plus the sensitivity tag assigned when it was ingested."""
    id: str
    text: str
    relevance_score: float          # 0.0–1.0, from the retriever/reranker
    sensitivity: SensitivityTier
    summary: str = ""                # pre-generated short summary, optional


@dataclass
class ScoredChunk:
    """A chunk after ACRE has made a disclosure decision on it."""
    chunk: Chunk
    exposure_score: float
    decision: DisclosureDecision

    @property
    def content_for_llm(self) -> str:
        """What actually gets sent downstream to the LLM's context window."""
        if self.decision == DisclosureDecision.FULL:
            return self.chunk.text
        if self.decision == DisclosureDecision.SUMMARY:
            return self.chunk.summary or "[Restricted passage: related content exists, but its details are withheld at your clearance level.]"
        return "[REDACTED: insufficient clearance for this content]"