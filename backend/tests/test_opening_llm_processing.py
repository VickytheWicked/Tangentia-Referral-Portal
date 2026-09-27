import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.cv_intelligence.database import get_cv_db
from app.models.job_position import JobPosition
from app.cv_intelligence.requirement_analyzer import (
    is_job_requirements_cached,
    process_opening_with_llm,
    extract_structured_job_requirements,
    ensure_all_openings_processed_by_llm,
    generate_requirement_analysis,
    _JOB_REQUIREMENTS_CACHE,
)
from app.services.cats_scraper import clean_html, sync_cats_jobs_with_db


@pytest.fixture(autouse=True)
def clean_test_cache():
    # Save cache snapshot and restore after each test
    saved_cache = dict(_JOB_REQUIREMENTS_CACHE)
    yield
    _JOB_REQUIREMENTS_CACHE.clear()
    _JOB_REQUIREMENTS_CACHE.update(saved_cache)


def test_clean_html_to_plain_text():
    """Verify that CATSOne job HTML is cleanly stripped of tags, scripts, and entities."""
    raw_html = """
    <div>
        <p>Seeking an experienced <strong>Cloud Architect</strong>.</p>
        <p>Responsibilities include:</p>
        <ul>
            <li>Design AWS and Azure enterprise cloud architectures</li>
            <li>Lead DevOps and CI/CD pipelines</li>
        </ul>
        <script>console.log('malicious');</script>
        <p>Requirements: 8+ years experience &amp; degree.</p>
    </div>
    """
    clean_text = clean_html(raw_html)
    assert "<p>" not in clean_text
    assert "<strong>" not in clean_text
    assert "<script>" not in clean_text
    assert "console.log" not in clean_text
    assert "&amp;" not in clean_text
    assert "&" in clean_text
    assert "• Design AWS and Azure" in clean_text
    assert "8+ years experience" in clean_text


def test_opening_llm_processing_runs_only_once():
    """
    Verify that an opening is processed by LLM strictly ONCE.
    Subsequent calls must hit cache and NOT invoke LLM.
    """
    opening_id = "test-cats-001"
    title = "Senior RPA Engineer"
    dept = "Intelligent Automation"
    clean_desc = "Seeking a Senior RPA Engineer with 5+ years of Automation Anywhere A360 and Python experience."

    _JOB_REQUIREMENTS_CACHE.pop(opening_id, None)
    _JOB_REQUIREMENTS_CACHE.pop(f"{opening_id}:{title.lower()}", None)

    assert not is_job_requirements_cached(opening_id, title)

    # First call - mock LLM extraction
    with patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements") as mock_gemini:
        mock_gemini.return_value = [
            {"requirement": "RPA & A360 Experience", "category": "REQUIRED_SKILLS", "required_value": "5+ years Automation Anywhere"}
        ]

        reqs1 = process_opening_with_llm(opening_id, title, dept, clean_desc, force_refresh=False)
        assert mock_gemini.call_count == 1
        assert len(reqs1) >= 2  # Baseline experience + education + extracted
        assert is_job_requirements_cached(opening_id, title)

    # Second call - must NOT call Gemini LLM again!
    with patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements") as mock_gemini:
        reqs2 = process_opening_with_llm(opening_id, title, dept, clean_desc, force_refresh=False)
        # Should not have called Gemini because it is already processed!
        assert mock_gemini.call_count == 0
        assert len(reqs2) == len(reqs1)


def test_candidate_processing_reuses_opening_requirements():
    """
    Verify that later on, when candidate processing runs, it reuses the pre-processed
    opening requirements and does NOT re-process the opening description with LLM.
    """
    opening_id = "test-cats-002"
    title = "Full Stack Python Architect"
    dept = "Engineering"
    clean_desc = "8+ years experience with FastAPI, React, PostgreSQL, Docker, and AWS."

    _JOB_REQUIREMENTS_CACHE.pop(opening_id, None)
    _JOB_REQUIREMENTS_CACHE.pop(f"{opening_id}:{title.lower()}", None)

    # Pre-process opening once
    with patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements") as mock_gemini:
        mock_gemini.return_value = [
            {"requirement": "Python & FastAPI", "category": "REQUIRED_SKILLS", "required_value": "FastAPI"}
        ]
        process_opening_with_llm(opening_id, title, dept, clean_desc)
        assert mock_gemini.call_count == 1

    # Now evaluate candidate - verify opening LLM is NOT called
    with patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements") as mock_gemini_opening:
        with patch("app.cv_intelligence.requirement_analyzer.run_semantic_analysis", return_value=None):
            analysis = generate_requirement_analysis(
                position_id=opening_id,
                job_title=title,
                department=dept,
                job_description=clean_desc,
                candidate_name="Jane Doe",
                candidate_years_exp=9.0,
                candidate_skills=["python", "fastapi", "react", "postgresql"],
                candidate_experience=[{"job_title": "Senior Engineer", "duration": "5 years", "responsibilities": ["FastAPI services"]}],
                cv_text="Jane Doe, Senior Engineer with 9 years of Python and FastAPI experience.",
                candidate_education=[{"degree": "B.Tech Computer Science"}],
            )

            # Opening LLM extraction must NOT have been called:
            assert mock_gemini_opening.call_count == 0
            assert analysis is not None
            assert len(analysis.mandatory_requirements) >= 1
            # REQ #1 is Total Professional Experience
            assert any(r.requirement == "Total Professional Experience" for r in analysis.mandatory_requirements + analysis.supported_requirements)


def test_cats_sync_triggers_opening_llm_once(db_session):
    """
    Verify that CATSOne sync triggers LLM processing for newly scraped openings,
    and skips openings that were already processed.
    """
    mock_jobs = [
        {
            "cats_job_id": "99901",
            "portal_id": "cats-99901",
            "title": "Data Scientist",
            "location": "Toronto, ON",
            "url_path": "/jobs/99901",
            "full_url": "https://tangentia.catsone.com/jobs/99901",
            "description": "Clean plain text description for Data Scientist requiring Python and Databricks.",
            "department": "Data & Analytics",
            "employment_type": "Full-time",
        }
    ]

    _JOB_REQUIREMENTS_CACHE.pop("cats-99901", None)
    _JOB_REQUIREMENTS_CACHE.pop("cats-99901:data scientist", None)

    with patch("app.services.cats_scraper.scrape_all_cats_jobs", return_value=mock_jobs):
        with patch("app.cv_intelligence.requirement_analyzer.process_opening_with_llm") as mock_process:
            mock_process.return_value = [
                {"requirement": "Python", "category": "REQUIRED_SKILLS", "required_value": "Python"}
            ]

            # First sync: opening is processed once
            res1 = sync_cats_jobs_with_db(db_session, deactivate_missing=False)
            assert res1["success"] is True
            assert mock_process.call_count == 1
            # Verify clean plain text was passed:
            args, kwargs = mock_process.call_args
            assert kwargs.get("position_id") == "cats-99901"
            assert "<" not in kwargs.get("description", "")


def test_opening_requirements_api_endpoints(client, db_session):
    """Verify the HR Admin endpoints for viewing and processing opening requirements."""
    job = JobPosition(
        id="cats-api-test-01",
        title="QA Automation Lead",
        department="Engineering",
        description="Lead QA Automation with Selenium, Python, and CI/CD pipelines.",
        location="Remote",
        employment_type="Full-time",
        is_active=True,
    )
    db_session.add(job)
    db_session.commit()

    headers = {"X-Dev-Role": "hr_admin"}

    # GET requirements
    resp = client.get(f"/api/cv-intelligence/openings/{job.id}/requirements", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["position_id"] == job.id
    assert data["title"] == job.title
    assert "requirements" in data
    assert data["requirements_count"] >= 2

    # POST process requirements
    resp_post = client.post(f"/api/cv-intelligence/openings/{job.id}/process-requirements", headers=headers)
    assert resp_post.status_code == 200
    data_post = resp_post.json()
    assert data_post["position_id"] == job.id
    assert data_post["already_cached"] is True
