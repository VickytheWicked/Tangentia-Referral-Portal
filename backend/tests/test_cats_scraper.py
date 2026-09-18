import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.cats_scraper import (
    clean_html,
    summarize_to_one_or_two_liner,
    infer_department,
    infer_employment_type,
    fetch_cats_job_listings,
    fetch_cats_job_detail,
    sync_cats_jobs_with_db,
)
from app.models.job_position import JobPosition


MOCK_MAIN_PAGE_HTML = """
<!DOCTYPE html>
<html>
<body>
<div class="jobs-table">
  <a class="table-row" href="/careers/9463/jobs/16850937-RPA-Developer-Power-Automate">
    <div class="data-cell title-cell">RPA Developer – Power Automate</div>
    <div class="data-cell" data-label="Category"></div>
    <div class="data-cell" data-label="Location">Goa/Trivandrum, India</div>
  </a>
  <a class="table-row" href="/careers/9463/jobs/16849421-Senior-Project-Manager-Finance-Transformation">
    <div class="data-cell title-cell">Senior Project Manager - Finance Transformation</div>
    <div class="data-cell" data-label="Category"></div>
    <div class="data-cell" data-label="Location">Dallas, TX, USA</div>
  </a>
  <a class="table-row" href="/careers/9463/jobs/16850595-Automation-Anywhere-SME">
    <div class="data-cell title-cell">Automation Anywhere SME</div>
    <div class="data-cell" data-label="Category"></div>
    <div class="data-cell" data-label="Location">Remote, India</div>
  </a>
</div>
</body>
</html>
"""

MOCK_JOB_DETAIL_HTML = """
<!DOCTYPE html>
<html>
<body>
<main id="job">
  <div class="container">
    <div class="job-description-container">
      <div class="job-header">
        <h1>RPA Developer – Power Automate</h1>
        <ul class="job-tags"><li>Goa/Trivandrum, India</li></ul>
      </div>
      <hr/>
      <div class="job-description">
        <h3><strong>Key Responsibilities:</strong></h3>
        &nbsp;
        <ul>
          <li><p>Develop and maintain RPA solutions using <strong>Microsoft Power Automate</strong>.</p></li>
          <li><p>Integrate with REST APIs &amp; databases.</p></li>
        </ul>
      </div>
    </div>
  </div>
  <aside><a class="btn" href="#">Apply Now</a></aside>
</main>
</body>
</html>
"""


def test_clean_html():
    raw = "<p>Hello <strong>World</strong>!</p><br/><ul><li>Item 1</li><li>Item 2 &amp; More</li></ul>"
    cleaned = clean_html(raw)
    assert "Hello World!" in cleaned
    assert "• Item 1" in cleaned
    assert "• Item 2 & More" in cleaned
    assert "<" not in cleaned


def test_summarize_to_one_or_two_liner():
    multi_paragraph = (
        "Key Responsibilities:\n"
        "• Develop and maintain enterprise cloud pipelines using Python and AWS.\n"
        "• Collaborate with cross-functional architecture and engineering teams.\n\n"
        "Required Qualifications:\n"
        "• 5+ years experience in distributed software systems."
    )
    one_liner = summarize_to_one_or_two_liner(multi_paragraph, "Senior Cloud Engineer", "Toronto, ON")
    assert len(one_liner.split("\n")) == 1
    assert "Develop and maintain enterprise cloud pipelines" in one_liner
    assert "Key Responsibilities" not in one_liner
    assert len(one_liner) <= 200



def test_infer_department():
    assert infer_department("RPA Developer – Power Automate") == "Intelligent Automation"
    assert infer_department("Senior Power BI Developer") == "Data & Analytics"
    assert infer_department("Senior SAP FICO Analyst") == "Finance & Enterprise"
    assert infer_department("Vice President, Global Sales") == "Global Sales"
    assert infer_department("Project Manager") == "Project & Product Management"
    assert infer_department("Senior Java Developer – Spring Boot") == "Engineering"
    assert infer_department("IT Engineer (AWS)") == "Cloud & Integration"


def test_infer_employment_type():
    assert infer_employment_type("Automation Anywhere", "Engagement: 3 months contract") == "Contract"
    assert infer_employment_type("Software Engineer Intern", "Summer internship") == "Internship"
    assert infer_employment_type("Senior Cloud Architect", "Full time permanent role") == "Full-time"


def test_fetch_cats_job_listings_mocked():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = MOCK_MAIN_PAGE_HTML
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response

    jobs = fetch_cats_job_listings(client=mock_client)
    assert len(jobs) == 3
    assert jobs[0]["cats_job_id"] == "16850937"
    assert jobs[0]["portal_id"] == "cats-16850937"
    assert jobs[0]["title"] == "RPA Developer – Power Automate"
    assert jobs[0]["location"] == "Goa/Trivandrum, India"


def test_fetch_cats_job_detail_mocked():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = MOCK_JOB_DETAIL_HTML
    mock_response.raise_for_status = MagicMock()
    mock_client.get.return_value = mock_response

    detail = fetch_cats_job_detail("/careers/9463/jobs/16850937-RPA-Developer-Power-Automate", client=mock_client)
    assert "Develop and maintain RPA solutions" in detail["description"]
    assert "REST APIs & databases" in detail["description"]


def test_sync_cats_jobs_with_db(db_session):
    mock_client = MagicMock()

    def mock_get(url):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        if "9463-General" in url:
            resp.text = MOCK_MAIN_PAGE_HTML
        else:
            resp.text = MOCK_JOB_DETAIL_HTML
        return resp

    mock_client.get.side_effect = mock_get

    with patch("app.services.excel.get_excel_service") as mock_excel:
        mock_excel_instance = MagicMock()
        mock_excel.return_value = mock_excel_instance

        result = sync_cats_jobs_with_db(db_session, deactivate_missing=False, client=mock_client)

        assert result["success"] is True
        assert result["total_scraped"] == 3
        assert result["created_count"] == 3

        # Verify records exist in DB
        db_job = db_session.query(JobPosition).filter(JobPosition.id == "cats-16850937").first()
        assert db_job is not None
        assert db_job.title == "RPA Developer – Power Automate"
        assert db_job.department == "Intelligent Automation"
        assert db_job.is_active is True

        # Re-running sync updates existing jobs idempotently
        result_re = sync_cats_jobs_with_db(db_session, deactivate_missing=False, client=mock_client)
        assert result_re["created_count"] == 0
        assert result_re["updated_count"] == 3


def test_api_sync_cats_unauthorized(client: TestClient):
    # Regular employee should be forbidden (403) from triggering ATS sync
    response = client.post(
        "/api/jobs/sync-cats",
        headers={"Authorization": "Bearer dev-employee-token"},
    )
    assert response.status_code == 403


def test_api_sync_cats_authorized(client: TestClient):
    with patch("app.services.cats_scraper.sync_cats_jobs_with_db") as mock_sync:
        mock_sync.return_value = {
            "success": True,
            "total_scraped": 2,
            "created_count": 2,
            "updated_count": 0,
            "deactivated_count": 0,
            "jobs": [],
            "message": "Successfully synchronized 2 job openings from Tangentia CATS Careers.",
        }

        response = client.post(
            "/api/jobs/sync-cats",
            headers={"Authorization": "Bearer dev-hr-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_scraped"] == 2


def test_cats_scheduler_status_endpoint(client: TestClient):
    response = client.get("/api/jobs/sync-cats/status")
    assert response.status_code == 200
    data = response.json()
    assert data["enabled"] is True
    assert data["interval_hours"] == 6
    assert data["deactivate_missing"] is True


def test_sync_cats_deactivates_closed_jobs(db_session):
    """
    Verify that when jobs disappear from CATS One (e.g. job closed/filled),
    syncing with deactivate_missing=True deactivates them (is_active=False).
    """
    # 1. Seed an active CATS position that was previously open
    open_cats_job = JobPosition(
        id="cats-99999",
        title="Previously Open Role",
        department="Engineering",
        location="Toronto, Canada",
        employment_type="Full-time",
        description="Legacy role",
        is_active=True,
    )
    db_session.add(open_cats_job)
    db_session.commit()
    assert open_cats_job.is_active is True

    # 2. Mock CATS scraper returning jobs that DO NOT include cats-99999
    mock_scraped = [
        {
            "portal_id": "cats-11111",
            "title": "Newly Opened Role",
            "department": "Engineering",
            "location": "Goa, India",
            "employment_type": "Full-time",
            "description": "New job description.",
        }
    ]

    with patch("app.services.cats_scraper.scrape_all_cats_jobs", return_value=mock_scraped):
        res = sync_cats_jobs_with_db(db_session, deactivate_missing=True)
        assert res["deactivated_count"] >= 1
        assert res["created_count"] == 1

        # Check in DB that the missing job was deactivated
        db_session.refresh(open_cats_job)
        assert open_cats_job.is_active is False


