import io
import pytest
from app.models.referral import Referral, ReferralStatus
from app.models.job_position import JobPosition
from app.services.cats_scraper import sync_cats_jobs_with_db


def test_hire_workflow_deactivates_position_and_archives_competitors(client, db_session, seeded_job):
    emp_headers = {"Authorization": "Bearer dev-employee-token"}
    hr_headers = {"Authorization": "Bearer dev-hr-token"}

    pdf_content = b"%PDF-1.4 mock cv bytes"

    # 1. Create referral A
    res_a = client.post(
        "/api/referrals",
        headers=emp_headers,
        data={
            "candidate_name": "Alice Candidate",
            "candidate_email": "alice@example.com",
            "candidate_phone": "+14161112222",
            "years_of_experience": 4.0,
            "relationship": "Colleague",
            "referral_note": "Great developer",
            "position_id": seeded_job.id,
            "candidate_consent": True,
        },
        files={"file": ("alice_cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert res_a.status_code == 201
    ref_a_id = res_a.json()["id"]

    # 2. Create referral B for the SAME position
    res_b = client.post(
        "/api/referrals",
        headers=emp_headers,
        data={
            "candidate_name": "Bob Candidate",
            "candidate_email": "bob@example.com",
            "candidate_phone": "+14163334444",
            "years_of_experience": 6.0,
            "relationship": "Former Teammate",
            "referral_note": "Senior engineer",
            "position_id": seeded_job.id,
            "candidate_consent": True,
        },
        files={"file": ("bob_cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert res_b.status_code == 201
    ref_b_id = res_b.json()["id"]

    # Verify both are initially submitted and job is active
    job_before = client.get(f"/api/jobs/{seeded_job.id}").json()
    assert job_before["is_active"] is True

    # 3. HR Hires Candidate A
    hire_res = client.put(
        f"/api/hr/referrals/{ref_a_id}/status",
        headers=hr_headers,
        json={"status": ReferralStatus.HIRED.value, "comment": "Excellent interview results. Offer accepted."},
    )
    assert hire_res.status_code == 200
    assert hire_res.json()["status"] == ReferralStatus.HIRED.value

    # 4. Verify Position is deactivated immediately
    job_after = client.get(f"/api/jobs/{seeded_job.id}", headers=hr_headers).json()
    assert job_after["is_active"] is False

    # 5. Verify Candidate B is automatically ARCHIVED with explanation
    ref_b_detail = client.get(f"/api/referrals/{ref_b_id}", headers=emp_headers).json()
    assert ref_b_detail["status"] == ReferralStatus.ARCHIVED.value
    history_comments = [h["comment"] for h in ref_b_detail["status_history"]]
    assert any("filled by candidate Alice Candidate" in (c or "") for c in history_comments)

    # 6. Verify Hired History endpoint includes Candidate A
    hired_history_res = client.get("/api/referrals/hired-history")
    assert hired_history_res.status_code == 200
    history = hired_history_res.json()
    assert len(history) >= 1
    found_a = next((item for item in history if item["id"] == ref_a_id), None)
    assert found_a is not None
    assert found_a["candidate_name"] == "Alice Candidate"
    assert found_a["position_id"] == seeded_job.id
    assert found_a["status"] == "Hired"

    # 7. Verify Hired History Excel export endpoint
    excel_res = client.get("/api/referrals/hired-history/excel-export")
    assert excel_res.status_code == 200
    assert excel_res.headers["content-disposition"] == 'attachment; filename="Tangentia_Hired_History.xlsx"'
    assert excel_res.content[:2] == b"PK"



def test_cats_sync_does_not_reactivate_hired_position(client, db_session):
    hr_headers = {"Authorization": "Bearer dev-hr-token"}
    emp_headers = {"Authorization": "Bearer dev-employee-token"}

    # Create a CATS job position
    cats_job_id = "cats-99999"
    cats_job = JobPosition(
        id=cats_job_id,
        title="Senior Automation Architect",
        department="Intelligent Automation",
        location="Toronto, Canada",
        employment_type="Full-time",
        description="Lead automation initiatives.",
        is_active=True,
    )
    db_session.add(cats_job)
    db_session.commit()

    # Submit a referral for this job
    pdf_content = b"%PDF-1.4 mock cv bytes"
    res_c = client.post(
        "/api/referrals",
        headers=emp_headers,
        data={
            "candidate_name": "Charlie Chaplin",
            "candidate_email": "charlie@example.com",
            "candidate_phone": "+14169998888",
            "years_of_experience": 8.0,
            "relationship": "Colleague",
            "referral_note": "Great architect",
            "position_id": cats_job_id,
            "candidate_consent": True,
        },
        files={"file": ("charlie_cv.pdf", io.BytesIO(pdf_content), "application/pdf")},
    )
    assert res_c.status_code == 201
    ref_c_id = res_c.json()["id"]

    # Hire Charlie
    client.put(
        f"/api/hr/referrals/{ref_c_id}/status",
        headers=hr_headers,
        json={"status": ReferralStatus.HIRED.value, "comment": "Hired for CATS role"},
    )

    # Job is now inactive
    db_session.refresh(cats_job)
    assert cats_job.is_active is False

    # Simulate CATS sync where the scraped jobs still include this position
    class MockClient:
        def get(self, url):
            class MockResponse:
                status_code = 200
                text = f"""
                <a class="table-row" href="/careers/9463/jobs/99999-Senior-Automation-Architect">
                    <div class="data-cell title-cell">Senior Automation Architect</div>
                    <div class="data-cell" data-label="Location">Toronto, Canada</div>
                </a>
                """
                def raise_for_status(self):
                    pass
            return MockResponse()

    # Run sync
    sync_cats_jobs_with_db(db_session, deactivate_missing=True, client=MockClient())

    # Verify that cats_job is STILL inactive!
    db_session.refresh(cats_job)
    assert cats_job.is_active is False
