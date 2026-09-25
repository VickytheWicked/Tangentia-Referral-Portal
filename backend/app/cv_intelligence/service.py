import re
import json
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

        # Snapshot prior stored details from cv_intelligence before processing
        prior_details = {
            "candidate_name": profile.candidate_name,
            "email": profile.email,
            "phone": profile.phone,
            "linkedin_url": profile.linkedin_url,
            "github_url": profile.github_url,
            "years_of_experience": profile.years_of_experience,
            "skills": list(profile.skills or []) if profile.skills else [],
            "education": list(profile.education or []) if profile.education else [],
            "experience": list(profile.experience or []) if profile.experience else [],
            "projects": list(profile.projects or []) if profile.projects else [],
            "certifications": list(profile.certifications or []) if profile.certifications else [],
            "extraction_status": profile.extraction_status,
            "extracted_at": profile.extracted_at,
        }

        prior_match = (
            cv_db.query(JobMatch)
            .filter(
                JobMatch.candidate_profile_id == profile.id,
                JobMatch.position_id == referral.position_id,
            )
            .first()
        )

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

            # 3. Rule-based heuristic fallback extraction from CV text
            from app.cv_intelligence.extractor import heuristic_cv_extract, is_valid_human_name
            from app.cv_intelligence.matcher import canonicalize_skill

            fallback_data = heuristic_cv_extract(cv_text)

            # 4. Attempt Gemini extraction
            gemini_data: Optional[CandidateProfileExtraction] = None
            gemini_available = False
            try:
                extractor = get_cv_extractor()
                gemini_data = extractor.extract(cv_text)
                gemini_available = True
            except Exception as ex:
                logger.warning(f"Live Gemini extraction unavailable for referral {referral_id} ({ex}).")
                gemini_data = None
                gemini_available = False

            # 5. Merge Candidate Profile Details
            # Priority:
            # - If Gemini is available: use Gemini details, fill any missing/empty details from fallback and prior.
            # - If Gemini is unavailable: use prior stored details in CV intelligence, fill missing from fallback and referral.

            # 5a. Candidate Name
            cand_name = None
            if gemini_data and gemini_data.candidate_name and is_valid_human_name(gemini_data.candidate_name):
                cand_name = gemini_data.candidate_name
            elif prior_details.get("candidate_name") and is_valid_human_name(prior_details["candidate_name"]):
                cand_name = prior_details["candidate_name"]
            elif fallback_data.candidate_name and is_valid_human_name(fallback_data.candidate_name):
                cand_name = fallback_data.candidate_name
            elif referral.candidate_name and is_valid_human_name(referral.candidate_name):
                cand_name = referral.candidate_name
            else:
                cand_name = referral.candidate_name or "Candidate"

            # 5b. Email
            final_email = None
            if gemini_data and gemini_data.email and "@" in gemini_data.email:
                final_email = gemini_data.email.strip()
            elif prior_details.get("email") and "@" in str(prior_details["email"]):
                final_email = str(prior_details["email"]).strip()
            elif fallback_data.email and "@" in fallback_data.email:
                final_email = fallback_data.email.strip()
            else:
                final_email = (referral.candidate_email or "").strip() or None

            # 5c. Phone
            final_phone = None
            if gemini_data and gemini_data.phone and len(re.sub(r"\D", "", gemini_data.phone)) >= 7:
                final_phone = gemini_data.phone.strip()
            elif prior_details.get("phone") and len(re.sub(r"\D", "", str(prior_details["phone"]))) >= 7:
                final_phone = str(prior_details["phone"]).strip()
            elif fallback_data.phone and len(re.sub(r"\D", "", fallback_data.phone)) >= 7:
                final_phone = fallback_data.phone.strip()
            else:
                final_phone = (referral.candidate_phone or "").strip() or None

            # 5d. URLs (LinkedIn, GitHub)
            final_linkedin = None
            if gemini_data and gemini_data.linkedin_url and "linkedin" in gemini_data.linkedin_url.lower():
                final_linkedin = gemini_data.linkedin_url.strip()
            elif prior_details.get("linkedin_url") and "linkedin" in str(prior_details["linkedin_url"]).lower():
                final_linkedin = str(prior_details["linkedin_url"]).strip()
            elif fallback_data.linkedin_url:
                final_linkedin = fallback_data.linkedin_url.strip()
            else:
                final_linkedin = (referral.linkedin_url or "").strip() or None

            final_github = None
            if gemini_data and gemini_data.github_url and "github" in gemini_data.github_url.lower():
                final_github = gemini_data.github_url.strip()
            elif prior_details.get("github_url") and "github" in str(prior_details["github_url"]).lower():
                final_github = str(prior_details["github_url"]).strip()
            elif fallback_data.github_url:
                final_github = fallback_data.github_url.strip()
            else:
                final_github = (referral.github_url or "").strip() or None

            # 5e. Years of Experience
            cand_years = 0.0
            if gemini_data and gemini_data.years_of_experience and float(gemini_data.years_of_experience) > 0:
                cand_years = float(gemini_data.years_of_experience)
            elif prior_details.get("years_of_experience") and float(prior_details["years_of_experience"]) > 0:
                cand_years = float(prior_details["years_of_experience"])
            elif fallback_data.years_of_experience and float(fallback_data.years_of_experience) > 0:
                cand_years = float(fallback_data.years_of_experience)
            elif referral.years_of_experience and float(referral.years_of_experience) > 0:
                cand_years = float(referral.years_of_experience)

            # 5f. Skills: Union Gemini skills (if available) with prior skills and fallback skills
            seen_skills = set()
            merged_skills = []

            def _append_skills(s_list):
                for s in (s_list or []):
                    if s and str(s).strip():
                        clean_s = canonicalize_skill(str(s).strip())
                        low = clean_s.lower()
                        if low not in seen_skills:
                            seen_skills.add(low)
                            merged_skills.append(clean_s)

            if gemini_data and gemini_data.skills:
                _append_skills(gemini_data.skills)
            if prior_details.get("skills"):
                _append_skills(prior_details["skills"])
            if fallback_data and fallback_data.skills:
                _append_skills(fallback_data.skills)

            # 5g. Education
            gemini_edu = [e.model_dump() if hasattr(e, "model_dump") else e for e in (gemini_data.education or [])] if gemini_data else []
            prior_edu = prior_details.get("education") or []
            fallback_edu = [e.model_dump() if hasattr(e, "model_dump") else e for e in (fallback_data.education or [])] if fallback_data else []

            if gemini_edu:
                final_edu = gemini_edu
                existing_degrees = {str(e.get("degree", "")).lower() for e in final_edu if isinstance(e, dict) and e.get("degree")}
                for f in fallback_edu:
                    if isinstance(f, dict) and f.get("degree") and str(f["degree"]).lower() not in existing_degrees:
                        final_edu.append(f)
                        existing_degrees.add(str(f["degree"]).lower())
            elif prior_edu:
                final_edu = prior_edu
                existing_degrees = {str(e.get("degree", "")).lower() for e in final_edu if isinstance(e, dict) and e.get("degree")}
                for f in fallback_edu:
                    if isinstance(f, dict) and f.get("degree") and str(f["degree"]).lower() not in existing_degrees:
                        final_edu.append(f)
                        existing_degrees.add(str(f["degree"]).lower())
            else:
                final_edu = fallback_edu

            # 5h. Experience
            gemini_exp = [exp.model_dump() if hasattr(exp, "model_dump") else exp for exp in (gemini_data.experience or [])] if gemini_data else []
            prior_exp = prior_details.get("experience") or []
            fallback_exp = [exp.model_dump() if hasattr(exp, "model_dump") else exp for exp in (fallback_data.experience or [])] if fallback_data else []

            if gemini_exp:
                final_exp = gemini_exp
            elif prior_exp:
                final_exp = prior_exp
            else:
                final_exp = fallback_exp

            # 5i. Projects
            gemini_proj = [p.model_dump() if hasattr(p, "model_dump") else p for p in (gemini_data.projects or [])] if gemini_data else []
            prior_proj = prior_details.get("projects") or []
            fallback_proj = [p.model_dump() if hasattr(p, "model_dump") else p for p in (fallback_data.projects or [])] if fallback_data else []

            if gemini_proj:
                final_proj = gemini_proj
            elif prior_proj:
                final_proj = prior_proj
            else:
                final_proj = fallback_proj

            # 5j. Certifications
            gemini_cert = [c.model_dump() if hasattr(c, "model_dump") else c for c in (gemini_data.certifications or [])] if gemini_data else []
            prior_cert = prior_details.get("certifications") or []
            fallback_cert = [c.model_dump() if hasattr(c, "model_dump") else c for c in (fallback_data.certifications or [])] if fallback_data else []

            if gemini_cert:
                final_cert = gemini_cert
            elif prior_cert:
                final_cert = prior_cert
            else:
                final_cert = fallback_cert

            profile.candidate_name = cand_name
            profile.email = final_email
            profile.phone = final_phone
            profile.linkedin_url = final_linkedin
            profile.github_url = final_github
            profile.years_of_experience = cand_years
            profile.skills = merged_skills
            profile.education = final_edu
            profile.experience = final_exp
            profile.projects = final_proj
            profile.certifications = final_cert
            profile.extraction_status = ExtractionStatus.COMPLETED.value
            profile.extracted_at = datetime.now(timezone.utc)
            profile.extraction_error = None

            # 6. Compute job matching against referral's target position
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

                # If Gemini was unavailable and we had prior match details in cv_db, preserve rich fit_summary:
                if not gemini_available and prior_match:
                    if prior_match.fit_summary and len(prior_match.fit_summary) > 15:
                        fit_summary = prior_match.fit_summary
                    if prior_match.explanation and len(prior_match.explanation) > len(explanation):
                        explanation = prior_match.explanation

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

                # Generate evidence-based requirement analysis (new — additive)
                try:
                    from app.cv_intelligence.requirement_analyzer import generate_requirement_analysis
                    req_analysis = generate_requirement_analysis(
                        position_id=position.id,
                        job_title=position.title,
                        department=position.department,
                        job_description=position.description or "",
                        candidate_name=profile.candidate_name or "",
                        candidate_years_exp=profile.years_of_experience,
                        candidate_skills=profile.skills or [],
                        candidate_experience=profile.experience or [],
                        cv_text=cv_text,
                        candidate_education=profile.education or [],
                    )
                    if req_analysis is not None:
                        job_match.requirement_analysis = req_analysis.model_dump_json()
                        logger.info(
                            f"Requirement analysis stored for referral {referral_id} "
                            f"({len(req_analysis.mandatory_requirements)} mandatory, "
                            f"{len(req_analysis.supported_requirements)} supported)"
                        )
                except Exception as ra_err:
                    logger.warning(
                        f"Requirement analysis failed for referral {referral_id}: {ra_err}. "
                        "Existing match data is preserved."
                    )

            cv_db.commit()
            cv_db.refresh(profile)
            logger.info(f"Successfully processed CV intelligence for referral {referral_id} (Gemini available={gemini_available})")

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
            # If we had prior completed details in cv_intelligence, restore them rather than breaking into FAILED!
            if prior_details.get("extraction_status") == ExtractionStatus.COMPLETED.value and (prior_details.get("skills") or prior_details.get("candidate_name")):
                logger.info(f"Restoring prior completed CV intelligence details for referral {referral_id}")
                profile.candidate_name = prior_details.get("candidate_name")
                profile.email = prior_details.get("email")
                profile.phone = prior_details.get("phone")
                profile.linkedin_url = prior_details.get("linkedin_url")
                profile.github_url = prior_details.get("github_url")
                profile.years_of_experience = prior_details.get("years_of_experience") or 0.0
                profile.skills = prior_details.get("skills") or []
                profile.education = prior_details.get("education") or []
                profile.experience = prior_details.get("experience") or []
                profile.projects = prior_details.get("projects") or []
                profile.certifications = prior_details.get("certifications") or []
                profile.extraction_status = ExtractionStatus.COMPLETED.value
                profile.extraction_error = None
            else:
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
            # Deserialise stored requirement_analysis JSON if present
            req_analysis_obj = None
            if match_record.requirement_analysis:
                try:
                    from app.cv_intelligence.schemas import OverallAnalysis
                    req_analysis_obj = OverallAnalysis.model_validate_json(
                        match_record.requirement_analysis
                    )
                except Exception as parse_err:
                    logger.warning(
                        f"Failed to parse requirement_analysis for match {match_record.id}: {parse_err}"
                    )

            match_item = JobMatchItem(
                id=match_record.id,
                position_id=match_record.position_id,
                match_level=match_record.match_level,
                matched_skills=match_record.matched_skills or [],
                missing_skills=match_record.missing_skills or [],
                experience_match=match_record.experience_match,
                explanation=match_record.explanation or [],
                fit_summary=match_record.fit_summary,
                requirement_analysis=req_analysis_obj,
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
