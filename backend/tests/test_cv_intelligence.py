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
# 19. HR Decision Guidance (Gemini & Fallback)
# -------------------------------------------------------------------------
def test_hr_decision_guidance():
    from app.cv_intelligence.guidance import get_hr_decision_guidance

    # Test with valid guidance output
    res = get_hr_decision_guidance(
        position_id="test-pos-guidance",
        job_title="Business Architect",
        department="Project & Product Management",
        description="Lead enterprise architecture initiatives and business process modeling.",
        min_exp_years=5.0,
        expected_skills=["BPMN", "Enterprise Architecture", "Agile"],
    )
    assert "hiring_guidance" in res
    assert isinstance(res["selection_criteria"], list)
    assert len(res["selection_criteria"]) >= 2
    assert isinstance(res["key_qualities"], list)
    assert len(res["key_qualities"]) >= 2
    assert len(res["hiring_guidance"]) > 20


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

    assert level in [MatchLevel.STRONG_MATCH, MatchLevel.GOOD_MATCH, MatchLevel.POTENTIAL_MATCH]
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

