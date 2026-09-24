import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.database import Base, get_db
from app.cv_intelligence.database import CVBase, get_cv_db
from app.cv_intelligence.models import CandidateProfile, ExtractionStatus
from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus
from app.models.user import User, UserRole
from app.historical_suggestions.matcher import HistoricalMatcher
from app.historical_suggestions.rag_service import HistoricalRAGService

# Test database isolation
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

HR_HEADERS = {"X-Dev-Role": "hr_admin"}
EMPLOYEE_HEADERS = {"X-Dev-Role": "employee"}


@pytest.fixture
def rag_isolated_env(tmp_path):
    """Provide a temporary SQLite vector database for tests."""
    temp_rag_db = str(tmp_path / "test_historical_rag.db")
    with patch("app.config.settings.HISTORICAL_RAG_DB_PATH", temp_rag_db):
        with patch("app.config.settings.HISTORICAL_REFERRAL_SEARCH_ENABLED", True):
            yield temp_rag_db


def test_historical_archived_referral_retrieval(client, db_session, seeded_users, rag_isolated_env):
    """
    1. Test that archived referrals from closed/other positions are surfaced
       for an active position requiring similar skills.
    """
    cv_db = TestCVSessionLocal()
    try:
        # Active Position: Senior Python Developer
        active_job = JobPosition(
            id="job-active-py",
            title="Senior Python Developer",
            department="Engineering",
            description="Looking for an experienced backend developer skilled in Python, FastAPI, and PostgreSQL with 3+ years experience.",
            location="Toronto",
            employment_type="Full-time",
            is_active=True,
        )
        # Closed Previous Position: Software Engineer
        closed_job = JobPosition(
            id="job-closed-se",
            title="Software Engineer",
            department="Engineering",
            description="General software engineering position.",
            location="Toronto",
            employment_type="Full-time",
            is_active=False,
        )
        db_session.add_all([active_job, closed_job])
        db_session.commit()

        # Archived candidate originally submitted for the closed job
        cand_x = Referral(
            id="ref-cand-x",
            referral_number="REF-2025-000123",
            candidate_name="Candidate X",
            candidate_email="cand.x@example.com",
            candidate_phone="+14165551111",
            years_of_experience=4.0,
            relationship="Former Colleague",
            referral_note="Expert in Python, FastAPI, and PostgreSQL database optimizations.",
            position_id=closed_job.id,
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="cand_x_resume.pdf",
            stored_filename="cand_x_resume.pdf",
        )
        db_session.add(cand_x)
        db_session.commit()

        # Add structured profile in CV Intelligence
        profile_x = CandidateProfile(
            referral_id=cand_x.id,
            candidate_name="Candidate X",
            email="cand.x@example.com",
            years_of_experience=4.0,
            skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
            projects=[{"name": "API Gateway", "description": "FastAPI microservices", "technologies": ["Python", "FastAPI"]}],
            experience=[{"job_title": "Backend Dev", "company": "Tech Corp", "responsibilities": ["FastAPI services"]}],
            extraction_status=ExtractionStatus.COMPLETED.value,
        )
        cv_db.add(profile_x)
        cv_db.commit()

        # Query API for historical suggestions
        res = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()

        assert data["current_position_id"] == active_job.id
        assert data["total_relevant_found"] >= 1
        found = [s for s in data["suggestions"] if s["referral_id"] == cand_x.id]
        assert len(found) == 1
        item = found[0]

        # Verify provenance
        assert item["candidate_name"] == "Candidate X"
        assert item["original_position_id"] == closed_job.id
        assert item["original_position_title"] == "Software Engineer"
        assert item["referral_number"] == "REF-2025-000123"
        assert item["original_status"] == ReferralStatus.ARCHIVED.value
        assert "Python" in item["matched_skills"]
        assert any(s.lower() == "fastapi" for s in item["matched_skills"])
    finally:
        cv_db.close()


def test_current_vs_historical_classification(client, db_session, seeded_users, rag_isolated_env):
    """
    2. Test that candidates submitted for the current opening are NEVER returned as historical referrals.
    """
    cv_db = TestCVSessionLocal()
    try:
        active_job = JobPosition(
            id="job-active-react",
            title="Frontend React Lead",
            department="Engineering",
            description="React and TypeScript frontend lead with 5+ years experience.",
            is_active=True,
            location="Remote",
        )
        db_session.add(active_job)
        db_session.commit()

        # New applicant directly for this active job
        cand_current = Referral(
            id="ref-current-cand",
            referral_number="REF-2026-000777",
            candidate_name="Direct Applicant",
            candidate_email="direct@example.com",
            candidate_phone="+14165552222",
            years_of_experience=5.0,
            relationship="Friend",
            referral_note="React TypeScript developer",
            position_id=active_job.id,  # Same position
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.SUBMITTED.value,
            original_filename="direct.pdf",
            stored_filename="direct.pdf",
        )
        db_session.add(cand_current)
        db_session.commit()

        res = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()
        ids = [s["referral_id"] for s in data["suggestions"]]
        assert cand_current.id not in ids
    finally:
        cv_db.close()


def test_duplicate_prevention_same_candidate(client, db_session, seeded_users, rag_isolated_env):
    """
    3. Test that if a candidate is already submitted for the current job,
       their archived referral for a previous job is NOT surfaced again as an Old Referral.
    """
    cv_db = TestCVSessionLocal()
    try:
        active_job = JobPosition(
            id="job-active-devops",
            title="DevOps Engineer",
            department="Cloud",
            description="Kubernetes, Terraform, AWS, and Docker.",
            is_active=True,
            location="Toronto",
        )
        closed_job = JobPosition(
            id="job-closed-sysadmin",
            title="Systems Administrator",
            department="IT",
            description="Linux and server administration.",
            is_active=False,
            location="Toronto",
        )
        db_session.add_all([active_job, closed_job])
        db_session.commit()

        # Historical archived record from past
        cand_past = Referral(
            id="ref-past-duplicate",
            referral_number="REF-2024-000001",
            candidate_name="John Doe",
            candidate_email="john.doe@example.com",
            candidate_phone="+14165553333",
            years_of_experience=4.0,
            relationship="Colleague",
            referral_note="Linux, AWS, and Docker specialist",
            position_id=closed_job.id,
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="john_old.pdf",
            stored_filename="john_old.pdf",
        )

        # Candidate is ALSO submitted for the active DevOps opening today!
        cand_active = Referral(
            id="ref-active-duplicate",
            referral_number="REF-2026-000099",
            candidate_name="John Doe",
            candidate_email="john.doe@example.com",  # Same email!
            candidate_phone="+14165553333",
            years_of_experience=5.0,
            relationship="Colleague",
            referral_note="Submitted again for DevOps",
            position_id=active_job.id,
            referred_by_user_id=seeded_users["emp2"].id,
            status=ReferralStatus.UNDER_REVIEW.value,
            original_filename="john_new.pdf",
            stored_filename="john_new.pdf",
        )
        db_session.add_all([cand_past, cand_active])
        db_session.commit()

        res = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()

        # Neither the active referral nor the past referral should appear under historical suggestions
        suggested_emails = [s["candidate_email"].lower() for s in data["suggestions"]]
        assert "john.doe@example.com" not in suggested_emails
    finally:
        cv_db.close()


def test_relevance_threshold_filters_irrelevant(client, db_session, seeded_users, rag_isolated_env):
    """
    4. Test that completely irrelevant archived candidates (e.g. Sales for Cloud Architect)
       are filtered out and do not appear.
    """
    cv_db = TestCVSessionLocal()
    try:
        active_job = JobPosition(
            id="job-active-cloud",
            title="Senior Cloud Solutions Architect",
            department="Cloud",
            description="Deep expertise in Azure, Kubernetes, Terraform, and distributed cloud security.",
            is_active=True,
            location="Toronto",
        )
        closed_job = JobPosition(
            id="job-closed-sales",
            title="Retail Sales Associate",
            department="Sales",
            description="Store sales and cash register management.",
            is_active=False,
            location="Toronto",
        )
        db_session.add_all([active_job, closed_job])
        db_session.commit()

        sales_cand = Referral(
            id="ref-sales-cand",
            referral_number="REF-2024-000999",
            candidate_name="Sam Retail",
            candidate_email="sam.retail@example.com",
            candidate_phone="+14165554444",
            years_of_experience=1.0,
            relationship="Acquaintance",
            referral_note="Sales representative, retail customer service, cash handling.",
            position_id=closed_job.id,
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="sam_sales.pdf",
            stored_filename="sam_sales.pdf",
        )
        db_session.add(sales_cand)
        db_session.commit()

        res = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()

        suggested_ids = [s["referral_id"] for s in data["suggestions"]]
        assert sales_cand.id not in suggested_ids
    finally:
        cv_db.close()


def test_original_provenance_and_database_immutability(client, db_session, seeded_users, rag_isolated_env):
    """
    5. Test that:
       - No new referral record is created.
       - Candidate retains original position_id, referral_number, and status="Archived".
       - Total referral count in DB is untouched before and after search.
    """
    cv_db = TestCVSessionLocal()
    try:
        active_job = JobPosition(
            id="job-qa-lead",
            title="QA Automation Lead",
            department="QA",
            description="Lead QA automation using Selenium, Cypress, and Python.",
            is_active=True,
            location="Toronto",
        )
        closed_job = JobPosition(
            id="job-qa-junior",
            title="Junior QA Tester",
            department="QA",
            description="Manual testing and test cases.",
            is_active=False,
            location="Toronto",
        )
        db_session.add_all([active_job, closed_job])
        db_session.commit()

        archived_qa = Referral(
            id="ref-archived-qa",
            referral_number="REF-2025-000888",
            candidate_name="Alex Tester",
            candidate_email="alex.tester@example.com",
            candidate_phone="+14165555555",
            years_of_experience=4.0,
            relationship="Colleague",
            referral_note="Expert in Selenium, Cypress, Python, and test automation.",
            position_id=closed_job.id,
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="alex_qa.pdf",
            stored_filename="alex_qa.pdf",
        )
        db_session.add(archived_qa)
        db_session.commit()

        initial_count = db_session.query(Referral).count()

        # Perform historical suggestion query
        res = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res.status_code == 200
        data = res.json()

        # Verify no database mutations occurred
        final_count = db_session.query(Referral).count()
        assert final_count == initial_count

        # Check DB record directly to verify status and position_id were untouched
        ref_in_db = db_session.query(Referral).filter(Referral.id == archived_qa.id).first()
        assert ref_in_db.status == ReferralStatus.ARCHIVED.value
        assert ref_in_db.position_id == closed_job.id
        assert ref_in_db.referral_number == "REF-2025-000888"

        # Check returned suggestion structure
        found = [s for s in data["suggestions"] if s["referral_id"] == archived_qa.id]
        assert len(found) == 1
        item = found[0]
        assert item["original_position_title"] == "Junior QA Tester"
        assert item["original_position_id"] == closed_job.id
        assert item["relevance_category"] in ["Strong Relevance", "Good Relevance", "Potential Relevance"]
        assert any(r.startswith("✓") for r in item["relevance_reasons"])
    finally:
        cv_db.close()


def test_feature_disabled_behavior(client, db_session, seeded_users):
    """
    6. Test that when HISTORICAL_REFERRAL_SEARCH_ENABLED=False,
       the endpoint safely returns HTTP 404 / disabled.
    """
    with patch("app.config.settings.HISTORICAL_REFERRAL_SEARCH_ENABLED", False):
        res = client.get("/api/historical-suggestions/positions/any-id", headers=HR_HEADERS)
        assert res.status_code == 404
        assert "disabled" in res.json()["detail"].lower()

        status_res = client.get("/api/historical-suggestions/status")
        assert status_res.status_code == 200
        assert status_res.json()["enabled"] is False


def test_cv_download_route_accessible_for_historical_candidate(client, db_session, seeded_users, rag_isolated_env):
    """
    7. Test that HR can download the original CV of the historical candidate
       using the existing /api/referrals/{referral_id}/cv endpoint.
    """
    job = JobPosition(
        id="job-hist-dl",
        title="Position for Download Test",
        department="Engineering",
        description="Engineering role.",
        is_active=False,
        location="Toronto",
    )
    db_session.add(job)
    db_session.commit()

    ref = Referral(
        id="ref-download-target",
        referral_number="REF-2025-000777",
        candidate_name="Downloadable Candidate",
        candidate_email="dl.cand@example.com",
        candidate_phone="+14165557777",
        years_of_experience=3.0,
        relationship="Friend",
        referral_note="Archived test candidate",
        position_id=job.id,
        referred_by_user_id=seeded_users["emp1"].id,
        status=ReferralStatus.ARCHIVED.value,
        original_filename="sample_resume.pdf",
        stored_filename="sample_resume.pdf",
    )
    db_session.add(ref)
    db_session.commit()

    # Call existing CV download endpoint as HR
    res = client.get(f"/api/referrals/{ref.id}/cv", headers=HR_HEADERS)
    assert res.status_code == 200
    assert "attachment" in res.headers.get("Content-Disposition", "") or "inline" in res.headers.get("Content-Disposition", "")


def test_rag_semantic_caching_and_ranking(client, db_session, seeded_users, rag_isolated_env):
    """
    8. Test that RAG embeddings are cached in the isolated SQLite index,
       and candidates with higher semantic overlap are ranked above candidates with lower overlap.
    """
    cv_db = TestCVSessionLocal()
    try:
        active_job = JobPosition(
            id="job-active-ai",
            title="AI & Machine Learning Engineer",
            department="AI Innovations",
            description="Developing LLM evaluation pipelines, agentic workflows, and semantic vector search using Python, LangChain, and RAG.",
            is_active=True,
            location="Remote",
        )
        closed_job_1 = JobPosition(
            id="job-closed-ai",
            title="NLP Researcher",
            department="AI",
            description="NLP research.",
            is_active=False,
            location="Remote",
        )
        closed_job_2 = JobPosition(
            id="job-closed-web",
            title="Webmaster",
            department="IT",
            description="Webmaster role.",
            is_active=False,
            location="Remote",
        )
        db_session.add_all([active_job, closed_job_1, closed_job_2])
        db_session.commit()

        # Highly relevant AI candidate
        cand_ai = Referral(
            id="ref-ai-expert",
            referral_number="REF-2025-000555",
            candidate_name="Deepa AI",
            candidate_email="deepa.ai@example.com",
            candidate_phone="+14165558888",
            years_of_experience=4.0,
            relationship="Colleague",
            referral_note="Built agentic workflows, LLM fine-tuning, LangChain, RAG pipelines, and vector search systems.",
            position_id=closed_job_1.id,
            referred_by_user_id=seeded_users["emp1"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="deepa_ai.pdf",
            stored_filename="deepa_ai.pdf",
        )

        # Mildly relevant candidate
        cand_general = Referral(
            id="ref-general-dev",
            referral_number="REF-2025-000666",
            candidate_name="Gary General",
            candidate_email="gary.gen@example.com",
            candidate_phone="+14165559999",
            years_of_experience=2.0,
            relationship="Colleague",
            referral_note="Python scripting and basic HTML website maintenance.",
            position_id=closed_job_2.id,
            referred_by_user_id=seeded_users["emp2"].id,
            status=ReferralStatus.ARCHIVED.value,
            original_filename="gary_gen.pdf",
            stored_filename="gary_gen.pdf",
        )
        db_session.add_all([cand_ai, cand_general])
        db_session.commit()

        # First request computes and caches embeddings
        res1 = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res1.status_code == 200
        data1 = res1.json()

        # The AI expert must rank first ahead of the general dev
        assert len(data1["suggestions"]) >= 1
        assert data1["suggestions"][0]["referral_id"] == cand_ai.id

        # Second request should use cached embeddings seamlessly
        res2 = client.get(f"/api/historical-suggestions/positions/{active_job.id}", headers=HR_HEADERS)
        assert res2.status_code == 200
        data2 = res2.json()
        assert data2["suggestions"][0]["referral_id"] == cand_ai.id
    finally:
        cv_db.close()


def test_unauthorized_employee_access_blocked(client, db_session, seeded_users, rag_isolated_env):
    """
    9. Test that historical referral search is strictly HR-only.
       Regular employees cannot access this endpoint.
    """
    res = client.get("/api/historical-suggestions/positions/job-active-py", headers=EMPLOYEE_HEADERS)
    assert res.status_code == 403
