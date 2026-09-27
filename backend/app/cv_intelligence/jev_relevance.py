"""
Jev Relevance Pre-Screen
========================
Uses TypeSafe AI's Jev (System One) model to run a fast, non-blocking relevance
check on a submitted CV against the target job position at submission time —
before the referral is saved to the database.

This is a non-blocking gate: on any Jev API failure, missing dependency, or timeout,
it returns a neutral result (score=0.5) and lets the referral proceed.
It must NEVER crash the submission flow.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("cv_intelligence.jev")


@dataclass
class RelevanceResult:
    score: float           # 0.0 (irrelevant) -> 1.0 (highly relevant)
    label: str             # "high" | "medium" | "low" | "unknown"
    jev_available: bool    # False if Jev API was unreachable or failed (score = 0.5 neutral)


def check_cv_relevance(
    cv_snippet: str,
    position_title: str,
    position_department: str = "",
    position_description: str = "",
    candidate_years_exp: float = 0.0,
    referral_note: str = "",
    api_key: str = "",
) -> RelevanceResult:
    """
    Ask Jev: "Is this CV relevant to this job position?"

    Returns a RelevanceResult with a score between 0.0 and 1.0.
    Always returns a safe neutral result (score=0.5) on any error.
    """
    if not api_key:
        logger.debug("Jev API key not configured — skipping relevance check.")
        return RelevanceResult(score=0.5, label="unknown", jev_available=False)

    try:
        from typesafe_sdk import TypeSafeClient, Noul

        client = TypeSafeClient(api_key=api_key)

        # Truncate inputs safely
        cv_text = (cv_snippet or "")[:1200].strip()
        job_desc = (position_description or "")[:600].strip()
        note = (referral_note or "")[:300].strip()

        state = {
            "cv_excerpt": cv_text,
            "job_title": position_title or "",
            "job_department": position_department or "",
            "job_description_excerpt": job_desc,
            "candidate_years_experience": str(candidate_years_exp),
            "referral_note": note,
        }

        response = client.system_one(
            state=state,
            questions={
                "is_relevant": Noul(
                    instructions=(
                        "Based on the candidate's CV excerpt and the job description, "
                        "is this candidate's background meaningfully relevant to the "
                        "target job position? Consider skills, domain, experience level, "
                        "and seniority. Ignore superficial keyword matches."
                    )
                ),
            },
        )

        # Extract score supporting typesafe-sdk 0.7+ (.nouls) with backward-compatible fallbacks
        if hasattr(response, "nouls") and "is_relevant" in response.nouls:
            score = float(response.nouls["is_relevant"].noul)
        elif hasattr(response, "answers") and "is_relevant" in response.answers:
            ans = response.answers["is_relevant"]
            score = float(getattr(ans, "noul", getattr(ans, "score", ans)))
        elif hasattr(response, "noulValue"):
            score = float(response.noulValue("is_relevant"))
        else:
            score = float(response["is_relevant"])

        if score >= 0.65:
            label = "high"
        elif score >= 0.40:
            label = "medium"
        else:
            label = "low"

        logger.info(
            f"Jev relevance check: position='{position_title}' "
            f"score={score:.2f} label={label}"
        )
        return RelevanceResult(score=score, label=label, jev_available=True)

    except Exception as e:
        logger.warning(f"Jev relevance check failed (non-blocking fallback used): {e}")
        return RelevanceResult(score=0.5, label="unknown", jev_available=False)
