"""
Historical Referral Suggestions module.
Provides isolated, additive RAG-based semantic search over historical archived referrals.
"""

from app.historical_suggestions.schemas import (
    HistoricalCandidateItem,
    HistoricalSuggestionsResponse,
)

__all__ = [
    "HistoricalCandidateItem",
    "HistoricalSuggestionsResponse",
]
