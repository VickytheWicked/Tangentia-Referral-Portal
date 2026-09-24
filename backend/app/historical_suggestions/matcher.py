import re
import logging
from typing import List, Dict, Set, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.models.referral import Referral, ReferralStatus
from app.models.job_position import JobPosition
from app.historical_suggestions.schemas import HistoricalCandidateItem, HistoricalSuggestionsResponse
from app.historical_suggestions.rag_service import get_historical_rag_service

logger = logging.getLogger("historical_suggestions")


def normalize_phone(phone: Optional[str]) -> str:
    """Normalize phone to numeric digits only for collision checks."""
    if not phone:
        return ""
    return re.sub(r"\D", "", phone)


class HistoricalMatcher:
    """
    Evaluates and surfaces archived candidates for active job openings.
    Ensures strict separation between current and historical referrals,
    applies duplicate exclusion, computes hybrid RAG relevance, and formats explainable highlights.
    """

    @classmethod
    def find_historical_suggestions(
        cls,
        db: Session,
        cv_db: Optional[Session],
        position_id: str,
        threshold: Optional[float] = None,
    ) -> HistoricalSuggestionsResponse:
        """
        Main query pipeline:
        1. Retrieve target position.
        2. Retrieve current candidates for target position to prevent duplicate surfacing.
        3. Retrieve archived candidates from OTHER positions.
        4. Evaluate semantic similarity & structured skill alignment.
        5. Filter by threshold and rank by relevance.
        """
        active_threshold = threshold if threshold is not None else settings.HISTORICAL_MATCH_THRESHOLD

        target_position = db.query(JobPosition).filter(JobPosition.id == position_id).first()
        if not target_position:
            raise ValueError(f"Job position '{position_id}' not found.")

        # Step 1: Identify existing candidates for the CURRENT position to avoid duplicates
        current_candidates = db.query(Referral).filter(
            Referral.position_id == position_id
        ).all()

        current_candidate_emails = {
            (c.candidate_email or "").strip().lower() for c in current_candidates if c.candidate_email
        }
        current_candidate_phones = {
            normalize_phone(c.candidate_phone) for c in current_candidates if c.candidate_phone
        }

        # Step 2: Query ARCHIVED candidates from OTHER positions
        archived_candidates = (
            db.query(Referral)
            .filter(
                Referral.position_id != position_id,
                Referral.status == ReferralStatus.ARCHIVED.value,
            )
            .order_by(Referral.created_at.desc())
            .all()
        )

        rag_service = get_historical_rag_service()
        job_query_text = rag_service.build_job_searchable_text(
            job_title=target_position.title,
            department=target_position.department,
            description=target_position.description or "",
        )
        job_embedding = rag_service.compute_embedding(job_query_text)

        # Parse target job requirements for structured matching
        from app.cv_intelligence.matcher import extract_keywords_from_job, canonicalize_skill, SKILL_TAXONOMY_MAP
        expected_skills, min_exp_years = extract_keywords_from_job(
            target_position.title,
            target_position.department,
            target_position.description or "",
        )

        suggestions: List[HistoricalCandidateItem] = []

        for ref in archived_candidates:
            # Duplicate prevention: If candidate already exists in current opening, exclude!
            ref_email = (ref.candidate_email or "").strip().lower()
            ref_phone = normalize_phone(ref.candidate_phone)

            if ref_email and ref_email in current_candidate_emails:
                continue
            if ref_phone and ref_phone in current_candidate_phones:
                continue

            # Step 3: Hydrate candidate profile (from cv_intelligence.db if available, else referral)
            profile_data = cls._get_candidate_profile_data(cv_db, ref)

            # Step 4: Build searchable text & compute RAG similarity
            orig_pos_title = ref.position.title if ref.position else "Previous Position"
            candidate_text = rag_service.build_candidate_searchable_text(
                candidate_name=ref.candidate_name,
                skills=profile_data["skills"],
                years_of_experience=profile_data["years_of_experience"],
                projects=profile_data["projects"],
                experience=profile_data["experience"],
                referral_note=ref.referral_note,
                original_position_title=orig_pos_title,
            )

            cand_embedding = rag_service.get_or_create_candidate_embedding(ref.id, candidate_text)
            semantic_score = rag_service.cosine_similarity(job_embedding, cand_embedding)

            # Step 5: Structured skill & experience matching
            matched_skills, missing_skills, exp_ok, exp_summary = cls._evaluate_structured_fit(
                candidate_skills=profile_data["skills"],
                candidate_years_exp=profile_data["years_of_experience"],
                candidate_projects=profile_data["projects"],
                expected_skills=expected_skills,
                min_exp_years=min_exp_years,
            )

            # Step 6: Compute hybrid relevance score
            skill_coverage = len(matched_skills) / max(len(expected_skills), 1) if expected_skills else 0.5
            # Weighted hybrid: 50% semantic vector similarity + 35% skill coverage + 15% experience
            exp_factor = 1.0 if exp_ok else 0.6
            relevance_score = (semantic_score * 0.50) + (skill_coverage * 0.35) + (exp_factor * 0.15)
            relevance_score = round(min(1.0, max(0.0, relevance_score)), 3)

            # Apply configurable threshold filter
            if relevance_score < active_threshold and len(matched_skills) < 2:
                continue

            # Step 7: Classify into 3 distinct user-facing tiers
            if (relevance_score >= 0.70 or len(matched_skills) >= 3) and exp_ok:
                relevance_category = "Strong Relevance"
            elif relevance_score >= 0.50 or len(matched_skills) >= 1:
                relevance_category = "Good Relevance"
            else:
                relevance_category = "Potential Relevance"

            # Step 8: Build explainable reasons with ✓ and •
            relevance_reasons = []
            for s in matched_skills[:4]:
                relevance_reasons.append(f"✓ {s}")
            if profile_data["years_of_experience"] > 0:
                if exp_ok:
                    relevance_reasons.append(f"✓ {profile_data['years_of_experience']:.1f}+ yrs relevant experience")
                else:
                    relevance_reasons.append(f"• {profile_data['years_of_experience']:.1f} yrs experience (target: {min_exp_years:g}+ yrs)")
            for m in missing_skills[:2]:
                relevance_reasons.append(f"• {m} not explicitly detailed in historical CV")

            # Fit narrative
            fit_narrative = (
                f"{relevance_category}: Candidate originally referred for '{orig_pos_title}' brings "
                f"{profile_data['years_of_experience']:.1f} yrs experience with alignment in "
                f"{', '.join(matched_skills[:3]) if matched_skills else 'core domain requirements'}."
            )

            # Format original referral date
            orig_date_str = ref.created_at.strftime("%Y-%m-%d") if ref.created_at else None

            suggestions.append(
                HistoricalCandidateItem(
                    referral_id=ref.id,
                    referral_number=ref.referral_number,
                    candidate_name=ref.candidate_name,
                    candidate_email=ref.candidate_email,
                    candidate_phone=ref.candidate_phone,
                    original_position_id=ref.position_id,
                    original_position_title=orig_pos_title,
                    original_referral_date=orig_date_str,
                    referred_by_name=ref.referred_by_name or (ref.referred_by.name if ref.referred_by else "Employee"),
                    original_status=ref.status,
                    relevance_category=relevance_category,
                    relevance_score=relevance_score,
                    matched_skills=matched_skills,
                    missing_skills=missing_skills,
                    experience_summary=exp_summary,
                    relevance_reasons=relevance_reasons,
                    fit_narrative=fit_narrative,
                    years_of_experience=profile_data["years_of_experience"],
                    skills=profile_data["skills"],
                    experience=profile_data["experience"],
                    projects=profile_data["projects"],
                    education=profile_data["education"],
                    certifications=profile_data["certifications"],
                    original_filename=ref.original_filename,
                )
            )

        # Sort suggestions: highest relevance score first, then most matched skills
        suggestions.sort(key=lambda s: (s.relevance_score, len(s.matched_skills)), reverse=True)

        return HistoricalSuggestionsResponse(
            current_position_id=target_position.id,
            current_position_title=target_position.title,
            threshold_applied=active_threshold,
            total_archived_evaluated=len(archived_candidates),
            total_relevant_found=len(suggestions),
            suggestions=suggestions,
        )

    @classmethod
    def _get_candidate_profile_data(cls, cv_db: Optional[Session], ref: Referral) -> Dict:
        """Hydrate candidate structured profile from cv_intelligence or fallback to Referral record."""
        data = {
            "skills": [],
            "years_of_experience": float(ref.years_of_experience or 0.0),
            "projects": [],
            "experience": [],
            "education": [],
            "certifications": [],
        }

        if cv_db:
            try:
                from app.cv_intelligence.models import CandidateProfile
                profile = cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref.id).first()
                if profile:
                    data["skills"] = profile.skills or []
                    data["years_of_experience"] = float(profile.years_of_experience or ref.years_of_experience or 0.0)
                    data["projects"] = profile.projects or []
                    data["experience"] = profile.experience or []
                    data["education"] = profile.education or []
                    data["certifications"] = profile.certifications or []
            except Exception as e:
                logger.debug(f"Could not load cv_intelligence profile for {ref.id}: {e}")

        # If skills list is empty, heuristically extract from referral note and original position
        if not data["skills"]:
            from app.cv_intelligence.matcher import STANDARD_SKILL_KEYWORDS
            combined_txt = f"{ref.referral_note or ''} {ref.position.title if ref.position else ''}".lower()
            detected = []
            for kw in STANDARD_SKILL_KEYWORDS:
                if re.search(r"\b" + re.escape(kw) + r"\b", combined_txt):
                    detected.append(kw)
            data["skills"] = detected[:15]

        return data

    @classmethod
    def _evaluate_structured_fit(
        cls,
        candidate_skills: List[str],
        candidate_years_exp: float,
        candidate_projects: List[dict],
        expected_skills: Set[str],
        min_exp_years: float,
    ) -> Tuple[List[str], List[str], bool, str]:
        """
        Evaluate candidate skills against expected skills using domain synonym taxonomy.
        """
        from app.cv_intelligence.matcher import canonicalize_skill, SKILL_TAXONOMY_MAP

        cand_tokens = {s.lower().strip() for s in candidate_skills if isinstance(s, str)}
        for p in candidate_projects:
            for tech in p.get("technologies", []):
                if isinstance(tech, str):
                    cand_tokens.add(tech.lower().strip())

        matched = set()
        missing = set()

        for req in expected_skills:
            req_l = req.lower()
            found = False

            if req_l in cand_tokens or any(req_l in c or c in req_l for c in cand_tokens):
                matched.add(canonicalize_skill(req_l))
                found = True

            if not found and req_l in SKILL_TAXONOMY_MAP:
                aliases = SKILL_TAXONOMY_MAP[req_l]
                if any(a in cand_tokens or any(a in c for c in cand_tokens) for a in aliases):
                    matched.add(canonicalize_skill(req_l))
                    found = True

            if not found and req_l not in {"excel", "git", "rest", "sales"}:
                missing.add(canonicalize_skill(req_l))

        exp_ok = True
        if min_exp_years > 0:
            if candidate_years_exp >= min_exp_years:
                exp_text = f"{candidate_years_exp:.1f} yrs (Meets {min_exp_years:g}+ yrs target)"
                exp_ok = True
            else:
                diff = min_exp_years - candidate_years_exp
                exp_text = f"{candidate_years_exp:.1f} yrs ({diff:.1f} yrs below {min_exp_years:g}+ yrs requirement)"
                exp_ok = (candidate_years_exp >= min_exp_years * 0.75)
        else:
            exp_text = f"{candidate_years_exp:.1f} yrs experience"
            exp_ok = True

        return sorted(list(matched)), sorted(list(missing)), exp_ok, exp_text
