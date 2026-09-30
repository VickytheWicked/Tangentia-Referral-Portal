import io
import json
import zipfile
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.cv_intelligence.database import CVBase, get_cv_db
from app.cv_intelligence.models import CandidateProfile, JobMatch, ExtractionStatus, MatchLevel
from app.cv_intelligence.schemas import CandidateProfileExtraction, EducationItem, ExperienceItem, ProjectItem, CertificationItem
from app.cv_intelligence.text_extractor import (
    extract_cv_text,
    extract_text_from_pdf,
    extract_text_from_docx,
    TextExtractionError,
)
from app.cv_intelligence.matcher import match_candidate_to_job
from app.cv_intelligence.extractor import GeminiCVExtractor, ExtractionServiceError
from app.cv_intelligence.service import CVIntelligenceService
from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus
from app.models.user import User, UserRole

# Isolated in-memory SQLite for testing CV intelligence
test_cv_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestCVSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_cv_engine)


@pytest.fixture(autouse=True)
def setup_test_cv_db():
    CVBase.metadata.create_all(bind=test_cv_engine)
    app.dependency_overrides[get_cv_db] = override_get_cv_db
    yield
    CVBase.metadata.drop_all(bind=test_cv_engine)


def override_get_cv_db():
    db = TestCVSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_cv_db] = override_get_cv_db
client = TestClient(app)

HR_HEADERS = {"X-Dev-Role": "hr_admin"}
EMPLOYEE_HEADERS = {"X-Dev-Role": "employee"}


def _create_minimal_valid_docx(text: str) -> bytes:
    """Helper to generate a valid in-memory DOCX binary."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
            </w:body>
        </w:document>"""
        z.writestr("word/document.xml", doc_xml.encode("utf-8"))
        z.writestr("[Content_Types].xml", b"<Types></Types>")
    return buf.getvalue()


def _create_minimal_pdf_bytes(text: str) -> bytes:
    """Helper to generate minimal valid PDF bytes with extractable text."""
    # A tiny valid PDF containing text object
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
        b"4 0 obj << /Length 55 >> stream\n"
        b"BT /F1 12 Tf 72 712 Td (" + text.encode("latin-1") + b") Tj ET\n"
        b"endstream\nendobj\n"
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000244 00000 n \n0000000350 00000 n \n"
        b"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n425\n%%EOF"
    )
    return pdf_content


# -------------------------------------------------------------------------
# 1. PDF extraction test
# -------------------------------------------------------------------------
def test_pdf_extraction():
    pdf_bytes = _create_minimal_pdf_bytes("Rahul Sharma Python FastAPI Engineer")
    extracted = extract_text_from_pdf(pdf_bytes)
    assert "Rahul Sharma" in extracted
    assert "Python" in extracted


# -------------------------------------------------------------------------
# 2. DOCX extraction test
# -------------------------------------------------------------------------
def test_docx_extraction():
    docx_bytes = _create_minimal_valid_docx("Priya Patel 3 years experience Docker PostgreSQL")
    extracted = extract_text_from_docx(docx_bytes)
    assert "Priya Patel" in extracted
    assert "Docker" in extracted


# -------------------------------------------------------------------------
# 3. Missing CV fields handling
# -------------------------------------------------------------------------
def test_missing_cv_fields_handling():
    # Schema validation with empty/partial fields
    partial = CandidateProfileExtraction(
        candidate_name="Amit Shah",
        skills=["Python"],
    )
    assert partial.candidate_name == "Amit Shah"
    assert partial.email is None
    assert partial.years_of_experience == 0.0
    assert partial.education == []
    assert partial.certifications == []


# -------------------------------------------------------------------------
# 4. Invalid CV handling
# -------------------------------------------------------------------------
def test_invalid_cv():
    with pytest.raises(TextExtractionError):
        extract_cv_text(b"This is not a pdf or docx format", "corrupt.pdf", "application/pdf")

    with pytest.raises(TextExtractionError):
        extract_cv_text(b"", "empty.pdf", "application/pdf")


# -------------------------------------------------------------------------
# 5. Unsupported file type handling
# -------------------------------------------------------------------------
def test_unsupported_file_type():
    with pytest.raises(TextExtractionError) as exc_info:
        extract_cv_text(b"some image data", "profile.png", "image/png")
    assert "Unsupported file format" in str(exc_info.value)


# -------------------------------------------------------------------------
# 6. Gemini extraction response validation
# -------------------------------------------------------------------------
def test_gemini_extraction_response_validation():
    valid_json = json.dumps({
        "candidate_name": "Vikram Singh",
        "email": "vikram@example.com",
        "phone": "+91-9876543210",
        "linkedin_url": "https://linkedin.com/in/vikram",
        "github_url": "https://github.com/vikram",
        "years_of_experience": 4.5,
        "skills": ["Python", "FastAPI", "React", "PostgreSQL", "Docker"],
        "education": [{"degree": "B.Tech", "institution": "IIT Bombay", "graduation_year": "2020"}],
        "experience": [{"company": "Tech Corp", "job_title": "Backend Lead", "duration": "3 years", "responsibilities": ["API design"]}],
        "projects": [{"name": "E-Commerce", "description": "High load store", "technologies": ["Python", "FastAPI"]}],
        "certifications": [{"name": "AWS Solutions Architect", "issuer": "Amazon", "year": "2022"}],
    })

    extractor = GeminiCVExtractor(api_key="test-key")
    parsed = extractor._parse_and_validate(valid_json)
    assert parsed.candidate_name == "Vikram Singh"
    assert parsed.years_of_experience == 4.5
    assert len(parsed.skills) == 5
    assert parsed.education[0].institution == "IIT Bombay"


# -------------------------------------------------------------------------
# 7. Gemini failure handling
# -------------------------------------------------------------------------
def test_gemini_failure_handling():
    extractor = GeminiCVExtractor(api_key="test-key")
    with patch("google.genai.Client") as mock_client:
        mock_client.return_value.models.generate_content.side_effect = Exception("API Quota Exceeded")
        with pytest.raises(ExtractionServiceError) as exc:
            extractor.extract("Some CV text")
        assert "Gemini CV extraction failed" in str(exc.value)


# -------------------------------------------------------------------------
# 8. Candidate profile persistence
# -------------------------------------------------------------------------
def test_candidate_profile_persistence():
    cv_db = TestCVSessionLocal()
    try:
        profile = CandidateProfile(
            referral_id="ref-test-001",
            candidate_name="Anita Roy",
            email="anita@example.com",
            years_of_experience=3.0,
            skills=["Python", "FastAPI", "SQL"],
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(profile)
        cv_db.commit()

        loaded = cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == "ref-test-001").first()
        assert loaded is not None
        assert loaded.candidate_name == "Anita Roy"
        assert "FastAPI" in loaded.skills
        assert loaded.extraction_status == ExtractionStatus.COMPLETED.value
    finally:
        cv_db.close()


# -------------------------------------------------------------------------
# 9. Job matching logic (Strong Match vs Good Match vs Potential Match)
# -------------------------------------------------------------------------
def test_job_matching_logic():
    # Job requirements: Python, FastAPI, PostgreSQL, 3+ years
    job_title = "Senior Python Developer"
    job_dept = "Engineering"
    job_desc = "Looking for a Python Developer with 3+ years experience in FastAPI, PostgreSQL, and Docker."

    # Strong match candidate
    level, matched, missing, exp_text, exp_bullets = match_candidate_to_job(
        candidate_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        candidate_years_exp=3.5,
        candidate_projects=[{"name": "API Gateway", "technologies": ["Python", "FastAPI"]}],
        candidate_experience=[],
        job_title=job_title,
        job_department=job_dept,
        job_description=job_desc,
    )
    assert level == MatchLevel.STRONG_MATCH
    assert "Python" in matched
    assert "Fastapi" in matched or "FASTAPI" in matched

    # Potential match candidate (only 1 skill and less experience)
    p_level, p_matched, p_missing, _, _ = match_candidate_to_job(
        candidate_skills=["HTML", "CSS"],
        candidate_years_exp=0.5,
        candidate_projects=[],
        candidate_experience=[],
        job_title=job_title,
        job_department=job_dept,
        job_description=job_desc,
    )
    assert p_level == MatchLevel.POTENTIAL_MATCH


# -------------------------------------------------------------------------
# 10. Multiple candidates for one job opening
# -------------------------------------------------------------------------
def test_multiple_candidates_for_one_job():
    # Setup referrals in main db
    from app.database import SessionLocal
    main_db = SessionLocal()
    cv_db = TestCVSessionLocal()
    try:
        pos = JobPosition(
            id="job-pos-multi",
            title="Full Stack Engineer",
            department="Engineering",
            description="Experience with React and Python",
            location="Remote",
            is_active=True,
        )
        main_db.merge(pos)

        ref1 = Referral(
            id="ref-multi-1",
            referral_number="REF-M-001",
            candidate_name="Alice Smith",
            candidate_email="alice@example.com",
            candidate_phone="1234567890",
            relationship="Former Colleague",
            referral_note="Top engineer",
            position_id=pos.id,
            referred_by_user_id="user-hr-001",
            original_filename="alice.pdf",
            stored_filename="alice.pdf",
        )
        ref2 = Referral(
            id="ref-multi-2",
            referral_number="REF-M-002",
            candidate_name="Bob Jones",
            candidate_email="bob@example.com",
            candidate_phone="1234567891",
            relationship="Professional Network",
            referral_note="Solid backend developer",
            position_id=pos.id,
            referred_by_user_id="user-hr-001",
            original_filename="bob.docx",
            stored_filename="bob.docx",
        )
        main_db.merge(ref1)
        main_db.merge(ref2)
        main_db.commit()

        # Group suggestions
        openings = CVIntelligenceService.get_suggestions_by_openings(main_db, cv_db)
        found = next((o for o in openings if o.position_id == pos.id), None)
        assert found is not None
        assert found.total_candidates >= 2
    finally:
        main_db.close()
        cv_db.close()


# -------------------------------------------------------------------------
# 11. HR Suggestions API endpoint
# -------------------------------------------------------------------------
def test_hr_suggestions_api():
    response = client.get("/api/cv-intelligence/suggestions", headers=HR_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# -------------------------------------------------------------------------
# 12. Candidate details API endpoint
# -------------------------------------------------------------------------
def test_candidate_details_api():
    from app.database import SessionLocal
    main_db = SessionLocal()
    try:
        ref = Referral(
            id="ref-details-test",
            referral_number="REF-DT-001",
            candidate_name="Details Candidate",
            candidate_email="details@example.com",
            candidate_phone="9998887770",
            relationship="Former Colleague",
            referral_note="Great fit for this role",
            position_id="job-1",
            referred_by_user_id="user-hr-001",
            original_filename="cv.pdf",
            stored_filename="cv.pdf",
        )
        main_db.merge(ref)
        main_db.commit()

        res = client.get(f"/api/cv-intelligence/candidates/{ref.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()
        assert data["candidate_name"] == "Details Candidate"
        assert data["referral_id"] == ref.id
        assert data["extraction_status"] == ExtractionStatus.PENDING.value
    finally:
        main_db.close()


# -------------------------------------------------------------------------
# 13. Original CV download verification (uses existing referral endpoint)
# -------------------------------------------------------------------------
def test_original_cv_download_intact():
    from app.database import SessionLocal
    main_db = SessionLocal()
    try:
        ref = Referral(
            id="ref-dl-cv",
            referral_number="REF-DLCV-001",
            candidate_name="Download Candidate",
            candidate_email="dl@example.com",
            candidate_phone="9998887771",
            relationship="Former Colleague",
            referral_note="Excellent resume",
            position_id="job-1",
            referred_by_user_id="user-hr-001",
            original_filename="candidate_resume.pdf",
            stored_filename="candidate_resume.pdf",
        )
        main_db.merge(ref)
        main_db.commit()

        # Existing referral CV endpoint
        res = client.get(f"/api/referrals/{ref.id}/cv", headers=HR_HEADERS)
        # Should return 200 stream or valid mock response
        assert res.status_code in [200, 404]  # 404 only if mock file not on disk
    finally:
        main_db.close()


# -------------------------------------------------------------------------
# 14. Feature disabled behavior
# -------------------------------------------------------------------------
def test_feature_disabled_behavior():
    with patch.object(settings, "CV_INTELLIGENCE_ENABLED", False):
        res = client.get("/api/cv-intelligence/suggestions", headers=HR_HEADERS)
        assert res.status_code == 404
        assert "disabled" in res.json()["detail"].lower()


# -------------------------------------------------------------------------
# 15. Existing referral workflow remains untouched
# -------------------------------------------------------------------------
def test_existing_referral_workflow_untouched():
    res = client.get("/api/referrals", headers=EMPLOYEE_HEADERS)
    assert res.status_code == 200


# -------------------------------------------------------------------------
# 16. Existing HR workflow remains untouched
# -------------------------------------------------------------------------
def test_existing_hr_workflow_untouched():
    res = client.get("/api/hr/referrals", headers=HR_HEADERS)
    assert res.status_code == 200


# -------------------------------------------------------------------------
# 17. Existing Excel synchronization remains untouched
# -------------------------------------------------------------------------
def test_existing_excel_sync_untouched():
    from app.services.excel import get_excel_service
    svc = get_excel_service()
    assert svc is not None
    assert hasattr(svc, "load_all_data")


# -------------------------------------------------------------------------
# 18. Existing authentication remains untouched
# -------------------------------------------------------------------------
def test_existing_auth_untouched():
    # Unauthenticated attempt to HR suggestions must return 401 or 403
    res = client.get("/api/cv-intelligence/suggestions")
    assert res.status_code in [401, 403]




# -------------------------------------------------------------------------
# 20. LLM Candidate Matching & Fit Summary Fallback
# -------------------------------------------------------------------------
def test_llm_match_and_fit_summary():
    from app.cv_intelligence.matcher import llm_match_candidate_to_job

    job_title = "Senior RPA Developer"
    job_dept = "Robotic Process Automation"
    job_desc = "Seeking an experienced RPA developer with Automation Anywhere A360 and Python skills."

    level, matched, missing, exp_text, explanation, fit_summary = llm_match_candidate_to_job(
        candidate_skills=["Automation Anywhere", "A360", "Python", "SQL"],
        candidate_years_exp=4.0,
        candidate_projects=[{"name": "Invoice Bot", "description": "Automated invoice parsing with A360"}],
        candidate_experience=[{"job_title": "RPA Engineer", "company": "Tech Corp", "duration": "2021-Present"}],
        job_title=job_title,
        job_department=job_dept,
        job_description=job_desc,
    )

    assert level in [MatchLevel.STRONG_MATCH, MatchLevel.GOOD_MATCH, MatchLevel.POTENTIAL_MATCH, MatchLevel.IRRELEVANT]
    assert isinstance(matched, list)
    assert isinstance(missing, list)
    assert isinstance(explanation, list)
    assert len(explanation) >= 1
    assert fit_summary is not None
    assert len(fit_summary) > 10


# -------------------------------------------------------------------------
# 21. JobMatch fit_summary persistence in cv_intelligence.db
# -------------------------------------------------------------------------
def test_job_match_fit_summary_persistence():
    cv_db = TestCVSessionLocal()
    try:
        profile = CandidateProfile(
            referral_id="ref-test-fit-summary",
            candidate_name="Vikram Rao",
            email="vikram@example.com",
            years_of_experience=5.0,
            skills=["Python", "Cloud Architecture"],
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(profile)
        cv_db.commit()

        match = JobMatch(
            candidate_profile_id=profile.id,
            position_id="pos-test-fit",
            match_level=MatchLevel.STRONG_MATCH.value,
            matched_skills=["Python", "Cloud Architecture"],
            missing_skills=[],
            experience_match="5.0 yrs",
            explanation=["✓ Python", "✓ Cloud Architecture"],
            fit_summary="Strong Match: Candidate brings 5.0 years of experience with skills in Python and Cloud Architecture.",
        )
        cv_db.add(match)
        cv_db.commit()

        loaded_match = cv_db.query(JobMatch).filter(JobMatch.candidate_profile_id == profile.id).first()
        assert loaded_match is not None
        assert loaded_match.fit_summary is not None
        assert "Strong Match" in loaded_match.fit_summary
        assert "Python" in loaded_match.fit_summary
    finally:
        cv_db.close()


# -------------------------------------------------------------------------
# 22. Fill missing details from fallback
# -------------------------------------------------------------------------
def test_fill_missing_from_fallback():
    from app.cv_intelligence.extractor import fill_missing_from_fallback
    from app.cv_intelligence.schemas import CandidateProfileExtraction, EducationItem, ExperienceItem, ProjectItem, CertificationItem

    # Primary (from Gemini): has name and some skills, but missing phone, email, education, experience, projects, certifications
    primary = CandidateProfileExtraction(
        candidate_name="Pooja Hegde",
        email=None,
        phone=None,
        linkedin_url=None,
        github_url=None,
        years_of_experience=0.0,
        skills=["Python", "FastAPI"],
        education=[],
        experience=[],
        projects=[],
        certifications=[],
    )

    # Fallback (from rule-based parser on CV text): has email, phone, years, extra skill, education, experience, projects, certs
    fallback = CandidateProfileExtraction(
        candidate_name=None,
        email="pooja@example.com",
        phone="+91 9876543210",
        linkedin_url="https://linkedin.com/in/pooja-hegde",
        github_url="https://github.com/pooja-h",
        years_of_experience=3.5,
        skills=["Python", "Docker", "PostgreSQL"],
        education=[EducationItem(degree="Bachelor of Engineering in CS", institution="Goa College of Engineering", graduation_year="2021")],
        experience=[ExperienceItem(job_title="Software Engineer", company="Tech Solutions", duration="2021-Present", responsibilities=["Built REST APIs"])],
        projects=[ProjectItem(name="Payment Gateway", description="Integrated stripe API", technologies=["Python", "FastAPI"])],
        certifications=[CertificationItem(name="AWS Certified Developer", issuer="Amazon Web Services", year="2023")],
    )

    merged = fill_missing_from_fallback(primary, fallback)

    assert merged.candidate_name == "Pooja Hegde"
    assert merged.email == "pooja@example.com"
    assert merged.phone == "+91 9876543210"
    assert merged.linkedin_url == "https://linkedin.com/in/pooja-hegde"
    assert merged.github_url == "https://github.com/pooja-h"
    assert merged.years_of_experience == 3.5
    # Skills should be merged without duplicates
    assert "Python" in merged.skills
    assert "Fastapi" in merged.skills or "FastAPI" in merged.skills
    assert "Docker" in merged.skills
    assert "Postgresql" in merged.skills or "PostgreSQL" in merged.skills
    # Education, experience, projects, certifications should be filled from fallback
    assert len(merged.education) == 1
    assert merged.education[0].institution == "Goa College of Engineering"
    assert len(merged.experience) == 1
    assert merged.experience[0].company == "Tech Solutions"
    assert len(merged.projects) == 1
    assert merged.projects[0].name == "Payment Gateway"
    assert len(merged.certifications) == 1
    assert merged.certifications[0].name == "AWS Certified Developer"


# -------------------------------------------------------------------------
# 23. Re-extract CV uses prior stored details when Gemini is unavailable
# -------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_reextract_cv_uses_prior_stored_details_when_gemini_unavailable():
    from app.database import SessionLocal

    main_db = SessionLocal()
    cv_db = TestCVSessionLocal()

    try:
        # Create position
        pos = JobPosition(
            id="job-pos-reextract-prior",
            title="Senior Python Architect",
            department="Cloud Engineering",
            description="Seeking a Senior Python Architect with AWS and Docker experience.",
            location="Remote",
            is_active=True,
        )
        main_db.merge(pos)

        # Create referral
        ref = Referral(
            id="ref-reextract-prior-001",
            referral_number="REF-RP-001",
            candidate_name="Karan Malhotra",
            candidate_email="karan@malhotra.dev",
            candidate_phone="+91 9123456789",
            relationship="Colleague",
            referral_note="Top architect candidate",
            position_id=pos.id,
            referred_by_user_id="user-hr-001",
            original_filename="karan_cv.pdf",
            stored_filename="karan_cv.pdf",
            years_of_experience=6.0,
        )
        main_db.merge(ref)
        main_db.commit()

        # Seed prior completed profile in cv_intelligence.db
        prior_profile = CandidateProfile(
            id="profile-karan-001",
            referral_id=ref.id,
            candidate_name="Karan Malhotra",
            email="karan@malhotra.dev",
            phone="+91 9123456789",
            linkedin_url="https://linkedin.com/in/karan-malhotra",
            years_of_experience=6.0,
            skills=["Python", "AWS", "Docker", "Microservices"],
            education=[{"degree": "Master of Technology in CS", "institution": "IIT Delhi", "graduation_year": "2018"}],
            experience=[{"job_title": "Senior Cloud Architect", "company": "Global Cloud Corp", "duration": "2018-Present", "responsibilities": ["Lead cloud architecture"]}],
            projects=[{"name": "Multi-Region Cloud Mesh", "description": "Designed resilient distributed system", "technologies": ["Python", "AWS", "Docker"]}],
            certifications=[{"name": "AWS Certified Solutions Architect", "issuer": "Amazon Web Services", "year": "2021"}],
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(prior_profile)

        # Seed prior job match with rich fit_summary
        prior_match = JobMatch(
            candidate_profile_id=prior_profile.id,
            position_id=pos.id,
            match_level=MatchLevel.STRONG_MATCH.value,
            matched_skills=["Python", "AWS", "Docker"],
            missing_skills=[],
            experience_match="6.0 yrs experience",
            explanation=["✓ Exceptional cloud architecture background", "✓ Master of Technology from IIT Delhi"],
            fit_summary="Strong Match: Karan Malhotra brings 6.0 years of proven enterprise cloud systems design.",
        )
        cv_db.add(prior_match)
        cv_db.commit()

        # Mock download_cv and extract_cv_text
        from unittest.mock import AsyncMock
        pdf_bytes = _create_minimal_pdf_bytes("Karan Malhotra Python AWS Docker")
        mock_sp = MagicMock()
        mock_sp.download_cv = AsyncMock(return_value=(pdf_bytes, "karan_cv.pdf", "application/pdf"))

        with patch("app.cv_intelligence.service.get_storage_service", return_value=mock_sp), \
             patch("app.cv_intelligence.extractor.GeminiCVExtractor.extract", side_effect=ExtractionServiceError("Gemini API Rate Limit 429")), \
             patch("app.cv_intelligence.service.llm_match_candidate_to_job", return_value=(
                 MatchLevel.STRONG_MATCH,
                 ["Python", "AWS", "Docker"],
                 [],
                 "6.0 yrs",
                 ["✓ Python", "✓ AWS"],
                 "Strong Match: Fallback narrative"
             )):

            # Call re-extract CV (force_reprocess=True)
            updated_profile = await CVIntelligenceService.process_referral_cv(
                db=main_db,
                cv_db=cv_db,
                referral_id=ref.id,
                force_reprocess=True,
            )

            # Assert prior stored details are preserved and status is COMPLETED
            assert updated_profile.extraction_status == ExtractionStatus.COMPLETED.value
            assert updated_profile.candidate_name == "Karan Malhotra"
            assert updated_profile.email == "karan@malhotra.dev"
            assert updated_profile.phone == "+91 9123456789"
            assert updated_profile.linkedin_url == "https://linkedin.com/in/karan-malhotra"
            assert updated_profile.years_of_experience == 6.0

            # Prior experience, projects, and certifications must NOT be wiped out!
            assert len(updated_profile.experience) >= 1
            assert updated_profile.experience[0]["company"] == "Global Cloud Corp"
            assert len(updated_profile.projects) >= 1
            assert updated_profile.projects[0]["name"] == "Multi-Region Cloud Mesh"
            assert len(updated_profile.certifications) >= 1
            assert updated_profile.certifications[0]["name"] == "AWS Certified Solutions Architect"
            assert len(updated_profile.education) >= 1
            assert updated_profile.education[0]["institution"] == "IIT Delhi"

            # Check JobMatch preserved the prior rich fit_summary
            match_in_db = cv_db.query(JobMatch).filter(
                JobMatch.candidate_profile_id == updated_profile.id,
                JobMatch.position_id == pos.id,
            ).first()
            assert match_in_db is not None
            assert "Karan Malhotra brings 6.0 years" in match_in_db.fit_summary

    finally:
        main_db.close()
        cv_db.close()


# -------------------------------------------------------------------------
# 24. Heuristic extractors for experience, projects, and certifications
# -------------------------------------------------------------------------
def test_heuristic_experience_projects_certifications():
    from app.cv_intelligence.extractor import (
        extract_experience_from_cv,
        extract_projects_from_cv,
        extract_certifications_from_cv,
    )

    sample_cv = """
    John Doe
    john@example.com

    WORK EXPERIENCE:
    Senior Software Engineer at ACME Corp
    Jan 2021 - Present
    • Developed microservices architecture using Python and FastAPI
    • Implemented automated CI/CD pipelines with Docker and GitHub Actions

    KEY PROJECTS:
    Automated Referral Engine
    Technologies: Python, React, PostgreSQL
    Engine to streamline candidate applications and automate screening.

    CERTIFICATIONS:
    AWS Certified Solutions Architect - Associate (2022)
    Automation Anywhere Master RPA Professional
    """

    exp = extract_experience_from_cv(sample_cv)
    assert len(exp) >= 1
    assert any("ACME" in (e.get("company") or "") or "Software" in (e.get("job_title") or "") for e in exp)
    assert any(len(e.get("responsibilities", [])) >= 1 for e in exp)

    projects = extract_projects_from_cv(sample_cv)
    assert len(projects) >= 1
    assert any("Referral" in p.get("name", "") for p in projects)
    assert any("Python" in p.get("technologies", []) or "FastAPI" in str(p) for p in projects)

    certs = extract_certifications_from_cv(sample_cv)
    assert len(certs) >= 1
    assert any("AWS" in c.get("name", "") or "Automation Anywhere" in c.get("name", "") for c in certs)


# -------------------------------------------------------------------------
# 28. Referral Deletion Cascades to CV Intelligence
# -------------------------------------------------------------------------
def test_delete_referral_cv_data_direct():
    """Verify CVIntelligenceService.delete_referral_cv_data removes profile & job matches."""
    import uuid
    ref_id = f"test-del-ref-{uuid.uuid4()}"
    cv_db = TestCVSessionLocal()
    try:
        profile = CandidateProfile(
            referral_id=ref_id,
            candidate_name="Deletion Test Candidate",
            email="delete_me@example.com",
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(profile)
        cv_db.commit()
        cv_db.refresh(profile)

        match = JobMatch(
            candidate_profile_id=profile.id,
            position_id="pos-del-test",
            match_level="Good Match",
            matched_skills=["Python"],
            missing_skills=[],
        )
        cv_db.add(match)
        cv_db.commit()

        # Verify records exist
        assert cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref_id).first() is not None
        assert cv_db.query(JobMatch).filter(JobMatch.candidate_profile_id == profile.id).first() is not None

        # Call deletion
        deleted = CVIntelligenceService.delete_referral_cv_data(cv_db=cv_db, referral_id=ref_id)
        assert deleted is True

        # Verify records are completely removed
        assert cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref_id).first() is None
        assert cv_db.query(JobMatch).filter(JobMatch.candidate_profile_id == profile.id).first() is None

        # Second call returns False (already gone)
        assert CVIntelligenceService.delete_referral_cv_data(cv_db=cv_db, referral_id=ref_id) is False
    finally:
        cv_db.close()


def test_hr_delete_referral_cleans_cv_intelligence():
    """Verify that DELETE /api/hr/referrals/{referral_id} purges CV Intelligence data."""
    import uuid
    from app.database import SessionLocal
    main_db = SessionLocal()
    cv_db = TestCVSessionLocal()
    ref_id = f"test-hr-del-{uuid.uuid4()}"

    try:
        pos = JobPosition(
            id="job-pos-del",
            title="DevOps Engineer",
            department="IT",
            description="Experience with DevOps and Python",
            location="Remote",
            is_active=True,
        )
        main_db.merge(pos)

        ref = Referral(
            id=ref_id,
            referral_number=f"REF-DEL-{uuid.uuid4().hex[:6].upper()}",
            candidate_name="Purge Candidate",
            candidate_email=f"purge_{uuid.uuid4().hex[:6]}@example.com",
            candidate_phone="+1-555-0199",
            relationship="Former Colleague",
            referral_note="Please evaluate",
            position_id=pos.id,
            referred_by_user_id="user-hr-001",
            status=ReferralStatus.SUBMITTED.value,
            original_filename="purge_cv.pdf",
            stored_filename=f"cvs/{ref_id}.pdf",
        )
        main_db.merge(ref)
        main_db.commit()

        profile = CandidateProfile(
            referral_id=ref_id,
            candidate_name="Purge Candidate",
            email=ref.candidate_email,
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(profile)
        cv_db.commit()
        cv_db.refresh(profile)

        match = JobMatch(
            candidate_profile_id=profile.id,
            position_id=pos.id,
            match_level="Strong Match",
            matched_skills=["FastAPI", "Python"],
            missing_skills=[],
        )
        cv_db.add(match)
        cv_db.commit()

        profile_id = profile.id

        # Confirm data is present in CV intelligence
        assert cv_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref_id).first() is not None
        assert cv_db.query(JobMatch).filter(JobMatch.candidate_profile_id == profile_id).first() is not None
        cv_db.close()

        # HR Admin deletes the referral via API
        del_resp = client.delete(f"/api/hr/referrals/{ref_id}", headers=HR_HEADERS)
        assert del_resp.status_code == 200
        assert "permanently deleted" in del_resp.json()["message"]

        # Verify referral is deleted from portal DB
        main_check_db = SessionLocal()
        try:
            assert main_check_db.query(Referral).filter(Referral.id == ref_id).first() is None
        finally:
            main_check_db.close()

        # Verify profile and match are deleted from test cv_intelligence db
        cv_check_db = TestCVSessionLocal()
        try:
            assert cv_check_db.query(CandidateProfile).filter(CandidateProfile.referral_id == ref_id).first() is None
            assert cv_check_db.query(JobMatch).filter(JobMatch.candidate_profile_id == profile_id).first() is None
        finally:
            cv_check_db.close()
    finally:
        main_db.close()



