import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.referral import Referral
from app.models.job_position import JobPosition
from app.cv_intelligence.models import (
    CandidateProfile,
    JobMatch,
    ExtractionStatus,
    MatchLevel,
)
from app.cv_intelligence.text_extractor import extract_cv_text, TextExtractionError
from app.cv_intelligence.extractor import get_cv_extractor, ExtractionServiceError
from app.cv_intelligence.matcher import match_candidate_to_job, extract_keywords_from_job, llm_match_candidate_to_job
from app.cv_intelligence.schemas import (
    CandidateProfileExtraction,
    OpeningSuggestionsResponse,
    SuggestedCandidateSummary,
    CandidateProfileDetailResponse,
    JobMatchItem,
)
from app.services.sharepoint import get_sharepoint_service

logger = logging.getLogger("cv_intelligence")


class CVIntelligenceService:
    """
    Orchestration service coordinating CV retrieval from storage,
    text extraction, Gemini 3.5 Flash parsing, matching, and isolated persistence.
    """

    @staticmethod
    def get_or_create_profile(cv_db: Session, referral_id: str) -> CandidateProfile:
        """Fetch existing candidate profile or initialize a PENDING placeholder in cv_intelligence.db."""
        profile = cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == referral_id).first()
        if not profile:
            profile = CandidateProfile(
                referral_id=referral_id,
                extraction_status=ExtractionStatus.PENDING.value,
            )
            cv_db.add(profile)
            cv_db.commit()
            cv_db.refresh(profile)
        return profile

    @staticmethod
    async def process_referral_cv(
        db: Session,
        cv_db: Session,
        referral_id: str,
        force_reprocess: bool = False,
    ) -> CandidateProfile:
        """
        Process a single referral's CV:
        1. Locate existing referral in main DB.
        2. Retrieve original CV from existing storage.
        3. Extract text locally.
        4. Extract structured profile via Gemini 3.5 Flash.
        5. Persist to cv_intelligence.db.
        6. Compute and store match with candidate's job position.
        """
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise ValueError(f"Referral {referral_id} not found in portal database.")

        profile = CVIntelligenceService.get_or_create_profile(cv_db, referral_id)

        # Skip if already completed unless force_reprocess is True
        if profile.extraction_status == ExtractionStatus.COMPLETED.value and not force_reprocess:
            return profile

        # Update status to PROCESSING
        profile.extraction_status = ExtractionStatus.PROCESSING.value
        profile.extraction_error = None
        cv_db.commit()
        cv_db.refresh(profile)

        try:
            # 1. Download original CV bytes using existing storage service
            sharepoint_svc = get_sharepoint_service()
            cv_bytes, filename, content_type = await sharepoint_svc.download_cv(
                drive_id=referral.sharepoint_drive_id,
                item_id=referral.sharepoint_item_id,
                referral_number=referral.referral_number,
                stored_filename=referral.stored_filename,
                original_filename=referral.original_filename,
                candidate_name=referral.candidate_name,
            )

            # 2. Extract text locally
            cv_text = extract_cv_text(
                file_bytes=cv_bytes,
                filename=referral.original_filename or filename,
                content_type=content_type,
            )

            # 3. Extract structured profile via Gemini with heuristic fallback
            try:
                extractor = get_cv_extractor()
                extracted_data: CandidateProfileExtraction = extractor.extract(cv_text)
            except Exception as ex:
                logger.warning(f"Live Gemini extraction failed ({ex}), using heuristic parser.")
                from app.cv_intelligence.extractor import heuristic_cv_extract
                extracted_data = heuristic_cv_extract(cv_text)

            # 4. Save extracted profile into cv_intelligence.db
            from app.cv_intelligence.extractor import is_valid_human_name

            cand_name = extracted_data.candidate_name
            if not cand_name or not is_valid_human_name(cand_name):
                cand_name = referral.candidate_name

            cand_years = extracted_data.years_of_experience
            if (cand_years is None or cand_years <= 0) and referral.years_of_experience:
                cand_years = float(referral.years_of_experience)

            profile.candidate_name = cand_name
            profile.email = extracted_data.email or referral.candidate_email
            profile.phone = extracted_data.phone or referral.candidate_phone
            profile.linkedin_url = extracted_data.linkedin_url or referral.linkedin_url
            profile.github_url = extracted_data.github_url or referral.github_url
            profile.years_of_experience = cand_years or 0.0
            # Ensure education is populated if LLM returned empty list
            if not extracted_data.education:
                from app.cv_intelligence.extractor import extract_education_from_cv
                from app.cv_intelligence.schemas import EducationItem
                edu_items = extract_education_from_cv(cv_text)
                if edu_items:
                    extracted_data.education = [EducationItem.model_validate(e) for e in edu_items]

            profile.skills = extracted_data.skills
            profile.education = [e.model_dump() for e in extracted_data.education]
            profile.experience = [exp.model_dump() for exp in extracted_data.experience]
            profile.projects = [p.model_dump() for p in extracted_data.projects]
            profile.certifications = [c.model_dump() for c in extracted_data.certifications]
            profile.extraction_status = ExtractionStatus.COMPLETED.value
            profile.extracted_at = datetime.now(timezone.utc)
            profile.extraction_error = None

            # 5. Compute job matching against referral's target position
            position = db.query(JobPosition).filter(JobPosition.id == referral.position_id).first()
            if position:
                match_level, matched_skills, missing_skills, exp_match, explanation, fit_summary = llm_match_candidate_to_job(
                    candidate_skills=profile.skills,
                    candidate_years_exp=profile.years_of_experience,
                    candidate_projects=profile.projects,
                    candidate_experience=profile.experience,
                    job_title=position.title,
                    job_department=position.department,
                    job_description=position.description,
                )

                # Update or create JobMatch in cv_intelligence.db
                job_match = (
                    cv_db.query(JobMatch)
                    .filter(
                        JobMatch.candidate_profile_id == profile.id,
                        JobMatch.position_id == position.id,
                    )
                    .first()
                )
                if not job_match:
                    job_match = JobMatch(
                        candidate_profile_id=profile.id,
                        position_id=position.id,
                    )
                    cv_db.add(job_match)

                job_match.match_level = match_level.value
                job_match.matched_skills = matched_skills
                job_match.missing_skills = missing_skills
                job_match.experience_match = exp_match
                job_match.explanation = explanation
                job_match.fit_summary = fit_summary

            cv_db.commit()
            cv_db.refresh(profile)
            logger.info(f"Successfully processed CV intelligence for referral {referral_id}")

            # Persist to Azure Blob Storage if configured
            try:
                from app.cv_intelligence.blob_sync import upload_cv_db_to_blob, is_cv_blob_sync_enabled
                if is_cv_blob_sync_enabled():
                    upload_cv_db_to_blob()
            except Exception as blob_err:
                logger.warning(f"Failed to sync cv_intelligence.db to Azure Blob: {blob_err}")

            return profile

        except (TextExtractionError, ExtractionServiceError, Exception) as err:
            logger.error(f"CV Intelligence processing failed for referral {referral_id}: {str(err)}")
            profile.extraction_status = ExtractionStatus.FAILED.value
            profile.extraction_error = str(err)
            cv_db.commit()
            cv_db.refresh(profile)

            # Persist failure status to Azure Blob Storage if configured
            try:
                from app.cv_intelligence.blob_sync import upload_cv_db_to_blob, is_cv_blob_sync_enabled
                if is_cv_blob_sync_enabled():
                    upload_cv_db_to_blob()
            except Exception:
                pass

            return profile

    @staticmethod
    def get_suggestions_by_openings(db: Session, cv_db: Session) -> List[OpeningSuggestionsResponse]:
        """
        Organize HR suggestions around existing active job openings.
        Categorizes candidates into Strong Match, Good Match, Potential Match, and Pending/Failed.
        """
        positions = db.query(JobPosition).filter(JobPosition.is_active == True).order_by(JobPosition.title).all()
        results = []

        for pos in positions:
            referrals = db.query(Referral).filter(Referral.position_id == pos.id).order_by(Referral.created_at.desc()).all()

            strong_matches = []
            good_matches = []
            potential_matches = []
            pending_extraction = []
            failed_extraction = []

            for ref in referrals:
                profile = cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref.id).first()
                match = (
                    cv_db.query(JobMatch)
                    .filter(
                        JobMatch.candidate_profile_id == (profile.id if profile else None),
                        JobMatch.position_id == pos.id,
                    )
                    .first()
                    if profile
                    else None
                )

                # Calculate priority score for deterministic ranking
                priority_score = 0
                exp_val = (profile.years_of_experience if profile else ref.years_of_experience) or 0.0
                if match:
                    if match.match_level == MatchLevel.STRONG_MATCH.value:
                        priority_score += 300
                    elif match.match_level == MatchLevel.GOOD_MATCH.value:
                        priority_score += 200
                    else:
                        priority_score += 100
                    priority_score += len(match.matched_skills) * 15
                    priority_score += int(min(exp_val, 15.0) * 5)

                summary = SuggestedCandidateSummary(
                    referral_id=ref.id,
                    candidate_name=ref.candidate_name,
                    candidate_email=ref.candidate_email,
                    original_filename=ref.original_filename,
                    extraction_status=profile.extraction_status if profile else ExtractionStatus.PENDING.value,
                    match_level=match.match_level if match else None,
                    years_of_experience=exp_val,
                    matched_skills=match.matched_skills if match else [],
                    missing_skills=match.missing_skills if match else [],
                    explanation=match.explanation if match else [],
                    fit_summary=match.fit_summary if match else None,
                    referral_status=ref.status,
                    referred_at=ref.created_at,
                    priority_score=priority_score,
                )

                if not profile or profile.extraction_status == ExtractionStatus.PENDING.value:
                    pending_extraction.append(summary)
                elif profile.extraction_status == ExtractionStatus.FAILED.value:
                    failed_extraction.append(summary)
                elif match:
                    if match.match_level == MatchLevel.STRONG_MATCH.value:
                        strong_matches.append(summary)
                    elif match.match_level == MatchLevel.GOOD_MATCH.value:
                        good_matches.append(summary)
                    else:
                        potential_matches.append(summary)
                else:
                    potential_matches.append(summary)

            # Sort candidate groups strictly by priority score descending
            strong_matches.sort(key=lambda s: s.priority_score, reverse=True)
            good_matches.sort(key=lambda s: s.priority_score, reverse=True)
            potential_matches.sort(key=lambda s: s.priority_score, reverse=True)

            from app.cv_intelligence.guidance import get_hr_decision_guidance

            expected_skills_raw, min_exp = extract_keywords_from_job(pos.title, pos.department, pos.description or "")
            formatted_skills = sorted([s.capitalize() if len(s) > 3 else s.upper() for s in expected_skills_raw])[:6]

            guidance = get_hr_decision_guidance(
                position_id=pos.id,
                job_title=pos.title,
                department=pos.department,
                description=pos.description or "",
                min_exp_years=min_exp,
                expected_skills=formatted_skills,
            )

            results.append(
                OpeningSuggestionsResponse(
                    position_id=pos.id,
                    title=pos.title,
                    department=pos.department,
                    location=pos.location,
                    employment_type=pos.employment_type,
                    description=pos.description,
                    expected_skills=formatted_skills,
                    min_experience_years=min_exp,
                    selection_criteria=guidance.get("selection_criteria", []),
                    key_qualities=guidance.get("key_qualities", []),
                    hiring_guidance=guidance.get("hiring_guidance"),
                    strong_matches=strong_matches,
                    good_matches=good_matches,
                    potential_matches=potential_matches,
                    pending_extraction=pending_extraction,
                    failed_extraction=failed_extraction,
                    total_candidates=len(referrals),
                )
            )

        # Sort openings: highest number of referrals first, tiebreak alphabetically by title
        results.sort(key=lambda o: (-o.total_candidates, o.title))
        return results

    @staticmethod
    def get_candidate_profile_detail(
        db: Session,
        cv_db: Session,
        referral_id: str,
    ) -> CandidateProfileDetailResponse:
        """
        Retrieve structured candidate profile, match explanation, and original CV reference.
        """
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise ValueError(f"Referral {referral_id} not found.")

        profile = cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == referral_id).first()
        position = db.query(JobPosition).filter(JobPosition.id == referral.position_id).first()

        match_record = None
        if profile:
            match_record = (
                cv_db.query(JobMatch)
                .filter(
                    JobMatch.candidate_profile_id == profile.id,
                    JobMatch.position_id == referral.position_id,
                )
                .first()
            )

        match_item = None
        if match_record:
            match_item = JobMatchItem(
                id=match_record.id,
                position_id=match_record.position_id,
                match_level=match_record.match_level,
                matched_skills=match_record.matched_skills or [],
                missing_skills=match_record.missing_skills or [],
                experience_match=match_record.experience_match,
                explanation=match_record.explanation or [],
                fit_summary=match_record.fit_summary,
            )

        return CandidateProfileDetailResponse(
            id=profile.id if profile else None,
            referral_id=referral.id,
            referral_number=referral.referral_number,
            candidate_name=(profile.candidate_name if profile and profile.candidate_name else referral.candidate_name),
            email=(profile.email if profile and profile.email else referral.candidate_email),
            phone=(profile.phone if profile and profile.phone else referral.candidate_phone),
            linkedin_url=(profile.linkedin_url if profile and profile.linkedin_url else referral.linkedin_url),
            github_url=(profile.github_url if profile and profile.github_url else referral.github_url),
            years_of_experience=(profile.years_of_experience if profile else referral.years_of_experience) or 0.0,
            skills=profile.skills if profile else [],
            education=profile.education if profile else [],
            experience=profile.experience if profile else [],
            projects=profile.projects if profile else [],
            certifications=profile.certifications if profile else [],
            extraction_status=profile.extraction_status if profile else ExtractionStatus.PENDING.value,
            extraction_error=profile.extraction_error if profile else None,
            extracted_at=profile.extracted_at if profile else None,
            match=match_item,
            original_filename=referral.original_filename,
            position_title=position.title if position else "General Position",
            position_id=referral.position_id,
            referral_status=referral.status,
            referred_by_name=referral.referred_by_name,
            referred_by_email=referral.referred_by_email,
            relationship=referral.relationship,
            referral_note=referral.referral_note,
            created_at=referral.created_at,
        )
