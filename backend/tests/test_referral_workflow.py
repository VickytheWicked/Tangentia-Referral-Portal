import io
import pytest
from app.models.referral import ReferralStatus


def test_duplicate_check_and_submission_workflow(client, seeded_job):
    emp_headers = {"Authorization": "Bearer dev-employee-token"}
    hr_headers = {"Authorization": "Bearer dev-hr-token"}

    # 1. Initial duplicate check - should find no matches
    dup_res = client.post(
        "/api/referrals/check-duplicate",
        headers=emp_headers,
        json={
            "candidate_email": "jane.doe@example.com",
            "candidate_phone": "+14165559999",
            "candidate_name": "Jane Doe",
            "position_id": seeded_job.id,
        },
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["is_duplicate"] is False

    # 2. Submit referral with valid PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Jane Doe CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    submit_data = {
        "candidate_name": "Jane Doe",
        "candidate_email": "jane.doe@example.com",
        "candidate_phone": "+14165559999",
        "linkedin_url": "https://linkedin.com/in/janedoe",
        "github_url": "https://github.com/janedoe",
        "years_of_experience": 5.0,
        "relationship": "Former Colleague",
        "referral_note": "Jane is an exceptional backend engineer who led core microservices.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }
    files = {
        "file": ("jane_doe_cv.pdf", io.BytesIO(pdf_content), "application/pdf"),
    }

    create_res = client.post(
        "/api/referrals",
        headers=emp_headers,
        data=submit_data,
        files=files,
    )
    assert create_res.status_code == 201
    created_ref = create_res.json()
    assert created_ref["candidate_name"] == "Jane Doe"
    assert created_ref["status"] == ReferralStatus.SUBMITTED.value
    assert created_ref["referral_number"].startswith("REF-")
    ref_id = created_ref["id"]

    # 3. Subsequent duplicate check with same email should flag duplicate
    dup_res_2 = client.post(
        "/api/referrals/check-duplicate",
        headers=emp_headers,
        json={
            "candidate_email": "jane.doe@example.com",
            "candidate_phone": "+19999999999",
            "candidate_name": "Jane Differ",
            "position_id": seeded_job.id,
        },
    )
    assert dup_res_2.status_code == 200
    assert dup_res_2.json()["is_duplicate"] is True
    assert len(dup_res_2.json()["matches"]) >= 1

    # 4. Employee can list their own referrals
    my_refs_res = client.get("/api/referrals", headers=emp_headers)
    assert my_refs_res.status_code == 200
    my_refs = my_refs_res.json()
    assert any(r["id"] == ref_id for r in my_refs)

    # 5. Detail view for employee should NOT expose internal HR notes
    detail_res = client.get(f"/api/referrals/{ref_id}", headers=emp_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["hr_notes"] == []

    # 6. HR can add internal notes
    note_res = client.post(
        f"/api/hr/referrals/{ref_id}/notes",
        headers=hr_headers,
        json={"note": "Initial background check passed. Technical assessment invited."},
    )
    assert note_res.status_code == 201

    # Employee still cannot see the note
    detail_res_again = client.get(f"/api/referrals/{ref_id}", headers=emp_headers)
    assert detail_res_again.json()["hr_notes"] == []

    # HR CAN see the note
    hr_detail_res = client.get(f"/api/referrals/{ref_id}", headers=hr_headers)
    assert len(hr_detail_res.json()["hr_notes"]) >= 1

    # 7. HR updates status to Interview with comment
    status_update_res = client.put(
        f"/api/hr/referrals/{ref_id}/status",
        headers=hr_headers,
        json={"status": ReferralStatus.INTERVIEW.value, "comment": "Passed screening."},
    )
    assert status_update_res.status_code == 200
    assert status_update_res.json()["status"] == ReferralStatus.INTERVIEW.value

    # 8. Check status history audit trail
    history_res = client.get(f"/api/referrals/{ref_id}/status-history", headers=emp_headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 2
    assert history[0]["new_status"] == ReferralStatus.INTERVIEW.value


def test_cv_download_authorization(client, seeded_job):
    emp_headers = {"Authorization": "Bearer dev-employee-token"}
    hr_headers = {"Authorization": "Bearer dev-hr-token"}

    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Test CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    submit_data = {
        "candidate_name": "Bob Smith",
        "candidate_email": "bob.smith@example.com",
        "candidate_phone": "+14165551234",
        "relationship": "Friend",
        "referral_note": "Great culture fit.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }
    files = {"file": ("bob_cv.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post("/api/referrals", headers=emp_headers, data=submit_data, files=files)
    assert res.status_code == 201
    ref_id = res.json()["id"]

    # Submitter can download
    cv_emp_res = client.get(f"/api/referrals/{ref_id}/cv", headers=emp_headers)
    assert cv_emp_res.status_code == 200
    assert cv_emp_res.content == pdf_content

    # HR Admin can download
    cv_hr_res = client.get(f"/api/referrals/{ref_id}/cv", headers=hr_headers)
    assert cv_hr_res.status_code == 200
    assert cv_hr_res.content == pdf_content


def test_hr_archive_and_delete_workflow(client, seeded_job):
    emp_headers = {"Authorization": "Bearer dev-employee-token"}
    hr_headers = {"Authorization": "Bearer dev-hr-token"}

    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Candidate CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    submit_data = {
        "candidate_name": "Archive Test Candidate",
        "candidate_email": "archive.test@example.com",
        "candidate_phone": "+14165558888",
        "relationship": "Colleague",
        "referral_note": "Solid developer candidate.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }
    files = {"file": ("archive_candidate_cv.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post("/api/referrals", headers=emp_headers, data=submit_data, files=files)
    assert res.status_code == 201
    ref_id = res.json()["id"]

    # 1. Update to Rejected first
    reject_res = client.put(
        f"/api/hr/referrals/{ref_id}/status",
        headers=hr_headers,
        json={"status": ReferralStatus.REJECTED.value, "comment": "Not a fit right now."},
    )
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == ReferralStatus.REJECTED.value

    # 2. Archive the referral even though it is Rejected
    archive_res = client.put(f"/api/hr/referrals/{ref_id}/archive?comment=Archived+rejected+record", headers=hr_headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == ReferralStatus.ARCHIVED.value

    # 3. Employee should NOT be able to delete referral (forbidden)
    emp_delete_res = client.delete(f"/api/hr/referrals/{ref_id}", headers=emp_headers)
    assert emp_delete_res.status_code == 403

    # 4. HR Admin permanently deletes the referral
    hr_delete_res = client.delete(f"/api/hr/referrals/{ref_id}", headers=hr_headers)
    assert hr_delete_res.status_code == 200
    assert "permanently deleted" in hr_delete_res.json()["message"]

    # 5. Verify referral is gone
    get_res = client.get(f"/api/referrals/{ref_id}", headers=hr_headers)
    assert get_res.status_code == 404
