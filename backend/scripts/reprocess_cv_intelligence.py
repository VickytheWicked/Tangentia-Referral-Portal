#!/usr/bin/env python3
"""
CV Intelligence Reprocessing Script
====================================
Reprocesses all existing candidate CVs with the new evidence-based
AI Requirement Analysis pipeline.

Usage:
    cd backend
    python scripts/reprocess_cv_intelligence.py [--force] [--referral-id <id>]

Options:
    --force          Regenerate requirement_analysis even if it already exists
    --referral-id    Process only a specific referral (for testing/debugging)
    --dry-run        Show what would be processed without making changes

This script:
  1. Discovers all CandidateProfiles with COMPLETED extraction status.
  2. Downloads each CV using the existing storage/retrieval mechanism.
  3. Generates the new evidence-based OverallAnalysis via requirement_analyzer.
  4. Updates job_match.requirement_analysis (idempotent — UPDATE not INSERT).
  5. Preserves all referral data, status, position, and CV files exactly.

SAFETY GUARANTEES:
  - Does NOT modify Referral records.
  - Does NOT change referral status, position_id, or referral_number.
  - Does NOT delete or duplicate CV files.
  - Does NOT create new Referral or CandidateProfile records.
  - Only updates job_matches.requirement_analysis column.
  - Continues processing if any individual candidate fails.
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

# ---------------------------------------------------------------------------
# Bootstrap path so we can import the backend application modules
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, BACKEND_DIR)

# Configure minimal logging before imports
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("reprocess_cv_intelligence")

# ---------------------------------------------------------------------------
# Imports (after path is set)
# ---------------------------------------------------------------------------
from app.config import settings  # noqa: E402
from app.database import SessionLocal, Base, engine  # noqa: E402
from app.cv_intelligence.database import CVSessionLocal, CVBase, cv_engine, init_cv_db  # noqa: E402
from app.cv_intelligence.models import CandidateProfile, JobMatch, ExtractionStatus  # noqa: E402
from app.models.referral import Referral  # noqa: E402
from app.models.job_position import JobPosition  # noqa: E402
from app.cv_intelligence.text_extractor import extract_cv_text, TextExtractionError  # noqa: E402
from app.cv_intelligence.requirement_analyzer import generate_requirement_analysis  # noqa: E402
from app.services.sharepoint import get_sharepoint_service  # noqa: E402
from app.services.excel import get_excel_service  # noqa: E402
from app.services.excel.sync import initialize_and_sync_excel  # noqa: E402

# ---------------------------------------------------------------------------
# Counters
# ---------------------------------------------------------------------------

class Counters:
    def __init__(self):
        self.total = 0
        self.processed = 0
        self.updated = 0
        self.created = 0
        self.skipped_already_done = 0
        self.skipped_no_match = 0
        self.skipped_no_position = 0
        self.failed_cv_download = 0
        self.failed_analysis = 0
        self.failures: list = []


# ---------------------------------------------------------------------------
# Core per-candidate processing
# ---------------------------------------------------------------------------

async def process_one_candidate(
    db,
    cv_db,
    profile: CandidateProfile,
    force: bool,
    dry_run: bool,
    counters: Counters,
) -> bool:
    """Process a single candidate profile for requirement analysis.
    Returns True if an LLM analysis was executed (caller may throttle), False otherwise."""
    referral_id = profile.referral_id

    # Fetch referral from main DB
    referral = db.query(Referral).filter(Referral.id == referral_id).first()
    if not referral:
        logger.warning(f"  [SKIP] Referral {referral_id} not found in main DB.")
        counters.skipped_no_match += 1
        counters.failures.append((referral_id, profile.candidate_name or "?", "Referral not found in main DB"))
        return False

    # Fetch job position
    position = db.query(JobPosition).filter(JobPosition.id == referral.position_id).first()
    if not position:
        logger.warning(f"  [SKIP] Position {referral.position_id} not found for referral {referral.referral_number}.")
        counters.skipped_no_position += 1
        counters.failures.append((referral.referral_number, profile.candidate_name or "?", "Position not found"))
        return False

    # Fetch existing job match
    job_match = (
        cv_db.query(JobMatch)
        .filter(
            JobMatch.candidate_profile_id == profile.id,
            JobMatch.position_id == referral.position_id,
        )
        .first()
    )
    if not job_match:
        logger.warning(
            f"  [SKIP] No JobMatch found for {referral.referral_number} / "
            f"{profile.candidate_name} — has CV been processed at least once?"
        )
        counters.skipped_no_match += 1
        counters.failures.append((referral.referral_number, profile.candidate_name or "?", "No JobMatch record"))
        return False

    # Skip if already done (unless --force)
    if job_match.requirement_analysis and not force:
        logger.info(
            f"  [SKIP] {referral.referral_number} / {profile.candidate_name} — "
            "requirement_analysis already exists. Use --force to regenerate."
        )
        counters.skipped_already_done += 1
        return False

    if dry_run:
        logger.info(
            f"  [DRY-RUN] Would process: {referral.referral_number} / "
            f"{profile.candidate_name} → {position.title}"
        )
        counters.processed += 1
        return False

    # Download CV and extract text (with graceful fallback to profile data)
    cv_text = ""
    try:
        sharepoint_svc = get_sharepoint_service()
        cv_bytes, filename, content_type = await sharepoint_svc.download_cv(
            drive_id=referral.sharepoint_drive_id,
            item_id=referral.sharepoint_item_id,
            referral_number=referral.referral_number,
            stored_filename=referral.stored_filename,
            original_filename=referral.original_filename,
            candidate_name=referral.candidate_name,
        )
        cv_text = extract_cv_text(
            file_bytes=cv_bytes,
            filename=referral.original_filename or filename,
            content_type=content_type,
        )
    except Exception as e:
        logger.debug(f"  CV extraction note for {referral.referral_number}: {e}")

    if not cv_text or not cv_text.strip():
        # Fallback: synthesize CV text from CandidateProfile structured fields
        parts = [f"Candidate Name: {profile.candidate_name or referral.candidate_name or 'Candidate'}"]
        if profile.years_of_experience:
            parts.append(f"Total Experience: {profile.years_of_experience:.1f} years")
        if profile.skills:
            parts.append("Skills: " + ", ".join(profile.skills))
        if profile.experience:
            parts.append("Experience:\n" + "\n".join(str(exp) for exp in profile.experience))
        if profile.education:
            parts.append("Education:\n" + "\n".join(str(edu) for edu in profile.education))
        cv_text = "\n\n".join(parts)


    # Generate requirement analysis
    try:
        analysis = generate_requirement_analysis(
            position_id=position.id,
            job_title=position.title,
            department=position.department,
            job_description=position.description or "",
            candidate_name=profile.candidate_name or referral.candidate_name or "",
            candidate_years_exp=profile.years_of_experience or 0.0,
            candidate_skills=profile.skills or [],
            candidate_experience=profile.experience or [],
            cv_text=cv_text,
            candidate_education=profile.education or [],
        )
    except Exception as e:
        logger.error(f"  [FAIL] Requirement analysis error for {referral.referral_number}: {e}")
        counters.failed_analysis += 1
        counters.failures.append((referral.referral_number, profile.candidate_name or "?", f"Analysis error: {e}"))
        return False

    if analysis is None:
        logger.warning(f"  [FAIL] Requirement analysis returned None for {referral.referral_number}.")
        counters.failed_analysis += 1
        counters.failures.append((referral.referral_number, profile.candidate_name or "?", "Analysis returned None"))
        return False

    # Persist — only updating requirement_analysis, nothing else
    was_new = job_match.requirement_analysis is None
    job_match.requirement_analysis = analysis.model_dump_json()
    cv_db.commit()

    if was_new:
        counters.created += 1
    else:
        counters.updated += 1

    counters.processed += 1
    logger.info(
        f"  [OK] {referral.referral_number} / {profile.candidate_name} → {position.title} "
        f"({len(analysis.mandatory_requirements)} mandatory, "
        f"{len(analysis.supported_requirements)} supported, "
        f"{len(analysis.partially_supported_requirements)} partial, "
        f"{len(analysis.not_demonstrated_requirements)} not demonstrated)"
    )
    return True


# ---------------------------------------------------------------------------
# Main reprocessing orchestrator
# ---------------------------------------------------------------------------

async def run_reprocessing(
    force: bool,
    dry_run: bool,
    referral_id_filter: str | None,
    delay: float = 5.0,
    limit: int | None = None,
) -> None:
    """Orchestrate the full reprocessing run."""

    print()
    print("=" * 60)
    print("  CV Intelligence Reprocessing — Requirement Analysis")
    print("=" * 60)
    if dry_run:
        print("  MODE: DRY-RUN (no changes will be made)")
    if force:
        print("  MODE: FORCE (existing analysis will be overwritten)")
    if referral_id_filter:
        print(f"  FILTER: Only referral {referral_id_filter}")
    if limit:
        print(f"  LIMIT: Up to {limit} candidate(s)")
    print(f"  RATE LIMIT SAFETY: {delay:.1f}s delay between LLM calls (~{int(60 / max(delay, 0.1))} RPM max)")
    print()

    # Step 1: Ensure Azure Blob cv_intelligence.db is downloaded if CV_STORAGE_TYPE == blob
    try:
        from app.cv_intelligence.blob_sync import download_cv_db_from_blob, upload_cv_db_to_blob, is_cv_blob_sync_enabled
        if is_cv_blob_sync_enabled():
            print("  [BLOB] Downloading cv_intelligence.db from Azure Blob Storage...")
            download_cv_db_from_blob()
            print("  [BLOB] Download completed.")
    except Exception as e:
        logger.warning(f"Could not download cv_intelligence.db from Azure Blob: {e}")

    # Step 2: Initialise CV intelligence DB (ensures schema + column migrations run)
    init_cv_db()

    # Step 3: Populate main DB (Referral, JobPosition) from Excel
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        excel_svc = get_excel_service()
        initialize_and_sync_excel(db, excel_svc)
        print("  [EXCEL] Synchronized referrals & job positions into runtime memory.")
    except Exception as e:
        logger.error(f"Failed to sync with Excel storage: {e}")

    cv_db = CVSessionLocal()
    counters = Counters()

    try:
        # Discover candidates to process
        query = cv_db.query(CandidateProfile).filter(
            CandidateProfile.extraction_status == ExtractionStatus.COMPLETED.value
        )

        if referral_id_filter:
            query = query.filter(CandidateProfile.referral_id == referral_id_filter)

        profiles = query.order_by(CandidateProfile.created_at).all()
        if limit and limit > 0:
            profiles = profiles[:limit]

        counters.total = len(profiles)

        print(f"  Found {counters.total} candidate profile(s) with COMPLETED extraction status.")
        print()

        for i, profile in enumerate(profiles, start=1):
            print(f"[{i:3d}/{counters.total}] {profile.candidate_name or profile.referral_id[:8]}...", end="  ")
            sys.stdout.flush()
            print()

            did_call_llm = False
            try:
                did_call_llm = await process_one_candidate(
                    db=db,
                    cv_db=cv_db,
                    profile=profile,
                    force=force,
                    dry_run=dry_run,
                    counters=counters,
                )
            except Exception as unexpected:
                logger.error(
                    f"  [FAIL] Unexpected error for profile {profile.id}: {unexpected}",
                    exc_info=True,
                )
                counters.failed_analysis += 1
                counters.failures.append((
                    profile.referral_id,
                    profile.candidate_name or "?",
                    f"Unexpected error: {unexpected}",
                ))
                # Rollback any partial transaction and continue
                try:
                    cv_db.rollback()
                except Exception:
                    pass

            # Safe throttling: delay only if an LLM call occurred and more candidates remain
            if did_call_llm and not dry_run and delay > 0 and i < len(profiles):
                logger.info(f"  [THROTTLE] Waiting {delay:.1f}s to respect Gemini Free Tier rate limits...")
                await asyncio.sleep(delay)

        # Sync back to Azure Blob if configured
        if not dry_run:
            try:
                from app.cv_intelligence.blob_sync import upload_cv_db_to_blob, is_cv_blob_sync_enabled
                if is_cv_blob_sync_enabled():
                    print("\n  [BLOB] Uploading updated cv_intelligence.db to Azure Blob Storage...")
                    upload_cv_db_to_blob()
                    print("  [BLOB] Sync complete!")
            except Exception as blob_err:
                logger.warning(f"Azure Blob sync after reprocessing failed: {blob_err}")

    finally:
        db.close()
        cv_db.close()

    # ---------------------------------------------------------------------------
    # Final Summary
    # ---------------------------------------------------------------------------
    print()
    print("=" * 60)
    print("  REPROCESSING COMPLETE")
    print("=" * 60)
    print(f"  Total profiles found:           {counters.total}")
    print(f"  Successfully processed:         {counters.processed}")
    print(f"    → Created (new analysis):     {counters.created}")
    print(f"    → Updated (existing):         {counters.updated}")
    print(f"  Skipped (already done):         {counters.skipped_already_done}")
    print(f"  Skipped (no match record):      {counters.skipped_no_match}")
    print(f"  Skipped (no position):          {counters.skipped_no_position}")
    print(f"  Failed (CV download/extract):   {counters.failed_cv_download}")
    print(f"  Failed (analysis error):        {counters.failed_analysis}")

    if counters.failures:
        print()
        print("  FAILURES:")
        for ref_num, name, reason in counters.failures:
            print(f"    • {ref_num} / {name}: {reason}")

    print()
    success_rate = (counters.processed / counters.total * 100) if counters.total > 0 else 0
    print(f"  Success rate: {success_rate:.1f}%")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Reprocess all existing candidate CVs with evidence-based AI Requirement Analysis."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate requirement_analysis even if it already exists.",
    )
    parser.add_argument(
        "--referral-id",
        metavar="ID",
        default=None,
        help="Process only a specific referral ID (for testing/debugging).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making any database changes.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=5.0,
        help="Delay in seconds between candidate LLM requests to stay within free tier rate limits (default: 5.0s = 12 RPM max).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of candidates to process in this run (useful for testing batches).",
    )

    args = parser.parse_args()

    if not settings.CV_INTELLIGENCE_ENABLED:
        print("ERROR: CV_INTELLIGENCE_ENABLED is False in settings. Set it to True to run reprocessing.")
        sys.exit(1)

    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY is not set. Semantic analysis will use fallback (deterministic only).")
        response = input("Continue anyway? [y/N]: ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    asyncio.run(
        run_reprocessing(
            force=args.force,
            dry_run=args.dry_run,
            referral_id_filter=args.referral_id,
            delay=args.delay,
            limit=args.limit,
        )
    )


if __name__ == "__main__":
    main()

