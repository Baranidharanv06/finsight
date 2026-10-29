"""
Sensitivity tagging for FinSight chunks at ingestion time.

FinSight indexes public SEC 10-K filings, so nothing here is "secret" in
the real-world sense -- the tiers below are a simulated sensitivity
labeling, standing in for what would, in a real deployment, be actual
internal/confidential/restricted document classification. This lets the
ACRE mechanism itself be demonstrated honestly on this dataset without
pretending public filings are regulated secrets.

Simple keyword-rule tagger: good enough to demo the pipeline end-to-end.
A production version would use a classifier instead of keyword matching.
"""

from .models import SensitivityTier

RESTRICTED_KEYWORDS = [
    "material weakness", "restatement", "going concern",
    "sec investigation", "subpoena", "securities fraud",
]

CONFIDENTIAL_KEYWORDS = [
    "litigation", "lawsuit", "regulatory inquiry", "settlement",
    "impairment", "undisclosed", "breach of contract",
]

INTERNAL_KEYWORDS = [
    "risk factor", "internal control", "related party",
]


def tag_sensitivity(text: str) -> SensitivityTier:
    lowered = text.lower()

    if any(kw in lowered for kw in RESTRICTED_KEYWORDS):
        return SensitivityTier.RESTRICTED
    if any(kw in lowered for kw in CONFIDENTIAL_KEYWORDS):
        return SensitivityTier.CONFIDENTIAL
    if any(kw in lowered for kw in INTERNAL_KEYWORDS):
        return SensitivityTier.INTERNAL
    return SensitivityTier.PUBLIC


def tag_chunks(chunks: list[str]) -> list[SensitivityTier]:
    return [tag_sensitivity(c) for c in chunks]