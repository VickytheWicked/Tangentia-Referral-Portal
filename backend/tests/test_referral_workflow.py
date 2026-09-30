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


def test_referrer_email_custom_submitted_details(client, seeded_job):
    """
    Verify that the referrer email and name submitted in the employee details
    are stored and returned properly (not defaulting to employee@tangentia.com).
    """
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (Referral CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    submit_data = {
        "candidate_name": "Devin Torres",
        "candidate_email": "devin.torres@example.com",
        "candidate_phone": "+14165553333",
        "referred_by_name": "Sarah Connor",
        "referred_by_email": "sarah.connor@tangentia.com",
        "relationship": "Former Colleague",
        "referral_note": "Exceptional team lead and systems architect.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }
    files = {"file": ("devin_torres_cv.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # Submit referral publicly as employee (no auth token required)
    res = client.post("/api/referrals", data=submit_data, files=files)
    assert res.status_code == 201
    created_ref = res.json()

    # The referrer name and email MUST match what was submitted, NOT employee@tangentia.com
    assert created_ref["referred_by_name"] == "Sarah Connor"
    assert created_ref["referred_by_email"] == "sarah.connor@tangentia.com"
    ref_id = created_ref["id"]

    # Detail view check
    detail_res = client.get(f"/api/referrals/{ref_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["referred_by_name"] == "Sarah Connor"
    assert detail_res.json()["referred_by_email"] == "sarah.connor@tangentia.com"

    # List view check
    list_res = client.get("/api/referrals")
    assert list_res.status_code == 200
    matched = [r for r in list_res.json() if r["id"] == ref_id]
    assert len(matched) == 1
    assert matched[0]["referred_by_name"] == "Sarah Connor"
    assert matched[0]["referred_by_email"] == "sarah.connor@tangentia.com"

    # CV Download check
    cv_res = client.get(f"/api/referrals/{ref_id}/cv")
    assert cv_res.status_code == 200
    assert cv_res.headers["content-type"] == "application/pdf"
    assert cv_res.content == pdf_content


def test_download_cv_fallback_when_item_id_none(client, db_session, seeded_job):
    from app.models.referral import Referral
    import uuid

    ref_id = str(uuid.uuid4())
    ref = Referral(
        id=ref_id,
        referral_number="REF-2026-999999",
        candidate_name="Fallback Test",
        candidate_email="fallback@tangentia.com",
        candidate_phone="+14160000000",
        referred_by_name="Test Referrer",
        referred_by_user_id="default-employee-id",
        years_of_experience=2.0,
        relationship="Former Colleague",
        referral_note="Great candidate.",
        position_id=seeded_job.id,
        status="Submitted",
        original_filename="devin_torres_cv.pdf",
        stored_filename="devin_torres_cv.pdf",
        storage_drive_id=None,
        storage_item_id=None,
        candidate_consent=True,
    )
    db_session.add(ref)
    db_session.commit()

    cv_res = client.get(f"/api/referrals/{ref_id}/cv")
    assert cv_res.status_code == 200
    assert len(cv_res.content) > 0


def test_strict_employee_email_tangentia_validation(client, seeded_job):
    """
    Verify that employee email MUST strictly end with @tangentia.com.
    Any other domain (e.g. gmail.com, yahoo.com) must be rejected with 400 Bad Request.
    """
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    base_data = {
        "candidate_name": "Email Domain Test Candidate",
        "candidate_email": "domain.test@example.com",
        "candidate_phone": "+1 416-555-0100",
        "referred_by_name": "Test Employee",
        "relationship": "Former Colleague",
        "referral_note": "Testing corporate email domain enforcement strictly.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }

    # 1. Non-tangentia email (e.g. @gmail.com) -> must be rejected with 400
    data_gmail = {**base_data, "referred_by_email": "john.doe@gmail.com"}
    files_gmail = {"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")}
    res_gmail = client.post("/api/referrals", data=data_gmail, files=files_gmail)
    assert res_gmail.status_code == 400
    assert "@tangentia.com" in res_gmail.json()["detail"]

    # 2. Another non-tangentia email (e.g. @outlook.com) -> must be rejected with 400
    data_outlook = {**base_data, "referred_by_email": "john.doe@outlook.com"}
    files_outlook = {"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")}
    res_outlook = client.post("/api/referrals", data=data_outlook, files=files_outlook)
    assert res_outlook.status_code == 400
    assert "@tangentia.com" in res_outlook.json()["detail"]

    # 3. Valid @tangentia.com email -> succeeds
    data_tangentia = {**base_data, "referred_by_email": "john.doe@tangentia.com"}
    files_tangentia = {"file": ("cv.pdf", io.BytesIO(pdf_content), "application/pdf")}
    res_tangentia = client.post("/api/referrals", data=data_tangentia, files=files_tangentia)
    assert res_tangentia.status_code == 201
    created = res_tangentia.json()
    assert created["referred_by_email"] == "john.doe@tangentia.com"


def test_referral_phone_stored_with_country_code_in_db_and_excel(client, seeded_job):
    """
    Verify that referral phone number with country code is properly stored
    in both the database and the Excel spreadsheet.
    """
    import openpyxl
    from app.services.excel import get_excel_service

    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Title (CV) >>\nendobj\ntrailer\n<<>>\n%%EOF"
    candidate_phone_with_cc = "+91 98200 12345"
    submit_data = {
        "candidate_name": "Aarav Sharma",
        "candidate_email": "aarav.sharma@example.com",
        "candidate_phone": candidate_phone_with_cc,
        "referred_by_name": "Rohan Mehra",
        "referred_by_email": "rohan.mehra@tangentia.com",
        "relationship": "Former Colleague",
        "referral_note": "Aarav is an outstanding senior engineer with deep cloud experience.",
        "position_id": seeded_job.id,
        "candidate_consent": True,
    }
    files = {"file": ("aarav_sharma_cv.pdf", io.BytesIO(pdf_content), "application/pdf")}

    res = client.post("/api/referrals", data=submit_data, files=files)
    assert res.status_code == 201
    created = res.json()
    assert created["candidate_phone"] == candidate_phone_with_cc
    ref_id = created["id"]
    ref_num = created["referral_number"]

    # Verify detail API returns candidate phone with country code
    detail_res = client.get(f"/api/referrals/{ref_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["candidate_phone"] == candidate_phone_with_cc

    # Verify in Excel workbook that candidate phone has the country code
    excel_svc = get_excel_service()
    wb = openpyxl.load_workbook(excel_svc.file_path, data_only=True)
    ws = wb["Referrals"]

    found_row = None
    for row in range(2, ws.max_row + 1):
        if ws.cell(row=row, column=10).value == ref_id or ws.cell(row=row, column=3).value == "aarav.sharma@example.com":
            found_row = row
            break

    assert found_row is not None, f"Referral {ref_id} not found in Excel Referrals sheet"
    excel_phone = ws.cell(row=found_row, column=4).value
    assert excel_phone == candidate_phone_with_cc
    wb.close()


def test_extract_cv_preview_endpoint(client):
    emp_headers = {"Authorization": "Bearer dev-employee-token"}

    # 1. Test unsupported file format
    txt_res = client.post(
        "/api/referrals/extract-cv",
        headers=emp_headers,
        files={"file": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")},
    )
    assert txt_res.status_code == 400
    assert "PDF" in txt_res.json()["detail"] and "docx" in txt_res.json()["detail"].lower()

    import zipfile

    def _create_docx(text: str) -> bytes:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            doc_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
                <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
            </w:document>"""
            z.writestr("word/document.xml", doc_xml.encode("utf-8"))
            z.writestr("[Content_Types].xml", b"<Types></Types>")
        return buf.getvalue()

    # 2. Test extraction from a sample document with contact details
    docx_bytes = _create_docx("Priya Sharma Email: priya.sharma@example.com Phone: +91 9876543210 Software Engineer with 6 years experience in Python and React")
    res = client.post(
        "/api/referrals/extract-cv",
        headers=emp_headers,
        files={"file": ("priya_cv.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "priya.sharma@example.com" in (data["candidate_email"] or "")
    assert "9876543210" in (data["candidate_phone"] or "")
    assert "email" in data["found_fields"]
    assert "phone" in data["found_fields"]

    # 3. Test extraction with missing email/phone
    docx_bytes2 = _create_docx("Project Summary Worked on enterprise data migration for 3 years.")
    res2 = client.post(
        "/api/referrals/extract-cv",
        headers=emp_headers,
        files={"file": ("project_summary.docx", io.BytesIO(docx_bytes2), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["success"] is True
    assert "email" in data2["not_found_fields"]
    assert "phone" in data2["not_found_fields"]


def test_duplicate_referral_after_six_months_is_treated_as_new(client, seeded_job, seeded_users, db_session):
    """
    Verify that if a referral was submitted more than 6 months ago (180+ days),
    it is considered an eligible new submission:
    - check-duplicate returns is_duplicate: False with no matches and no warning.
    - Subsequent new referral submission succeeds.
    - Candidates submitted within 6 months (<180 days) are flagged as duplicates.
    """
    from datetime import datetime, timezone, timedelta
    from app.models.referral import Referral

    emp = seeded_users["emp1"]
    now = datetime.now(timezone.utc)

    # 1. Seed a historical referral submitted 7 months ago (210 days ago)
    old_referral = Referral(
        referral_number="REF-2025-000088",
        candidate_name="Alex Mercer",
        candidate_email="alex.mercer@example.com",
        candidate_phone="+14165551234",
        years_of_experience=5.0,
        relationship="Former Colleague",
        referral_note="Great engineer from previous company.",
        position_id=seeded_job.id,
        referred_by_user_id=emp.id,
        referred_by_name=emp.name,
        referred_by_email=emp.email,
        status=ReferralStatus.SUBMITTED.value,
        original_filename="alex_old_cv.pdf",
        stored_filename="REF-2025-000088_Alex_Mercer.pdf",
        created_at=now - timedelta(days=210),
        updated_at=now - timedelta(days=210),
    )
    db_session.add(old_referral)

    # 2. Seed a recent referral submitted 1 month ago (30 days ago)
    recent_referral = Referral(
        referral_number="REF-2026-000099",
        candidate_name="Bob Recent",
        candidate_email="bob.recent@example.com",
        candidate_phone="+14165559876",
        years_of_experience=3.0,
        relationship="Friend",
        referral_note="Recent applicant.",
        position_id=seeded_job.id,
        referred_by_user_id=emp.id,
        referred_by_name=emp.name,
        referred_by_email=emp.email,
        status=ReferralStatus.SUBMITTED.value,
        original_filename="bob_cv.pdf",
        stored_filename="REF-2026-000099_Bob_Recent.pdf",
        created_at=now - timedelta(days=30),
        updated_at=now - timedelta(days=30),
    )
    db_session.add(recent_referral)
    db_session.commit()

    # 3. Check duplicate for Bob Recent (submitted 30 days ago) -> MUST be flagged as duplicate
    res_recent = client.post(
        "/api/referrals/check-duplicate",
        json={
            "candidate_email": "bob.recent@example.com",
            "candidate_phone": "+14165559876",
            "candidate_name": "Bob Recent",
            "position_id": seeded_job.id,
        },
    )
    assert res_recent.status_code == 200
    data_recent = res_recent.json()
    assert data_recent["is_duplicate"] is True
    assert len(data_recent["matches"]) == 1
    assert data_recent["matches"][0]["referral_number"] == "REF-2026-000099"

    # 4. Check duplicate for Alex Mercer (submitted 210 days ago > 6 months)
    # -> MUST NOT be flagged as duplicate (treated as new submission)
    res_old = client.post(
        "/api/referrals/check-duplicate",
        json={
            "candidate_email": "alex.mercer@example.com",
            "candidate_phone": "+14165551234",
            "candidate_name": "Alex Mercer",
            "position_id": seeded_job.id,
        },
    )
    assert res_old.status_code == 200
    data_old = res_old.json()
    assert data_old["is_duplicate"] is False
    assert len(data_old["matches"]) == 0

    # 5. Submit new referral for Alex Mercer -> succeeds as a fresh submission
    dummy_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n162\n%%EOF"
    submit_res = client.post(
        "/api/referrals",
        data={
            "candidate_name": "Alex Mercer",
            "candidate_email": "alex.mercer@example.com",
            "candidate_phone": "+14165551234",
            "years_of_experience": "6.0",
            "relationship": "Former Colleague",
            "referral_note": "Re-submitting Alex after 7 months for new opening.",
            "position_id": seeded_job.id,
            "candidate_consent": "true",
            "employee_name": "Sarah Jenkins",
            "employee_email": "sarah.jenkins@tangentia.com",
        },
        files={"file": ("alex_updated_cv.pdf", io.BytesIO(dummy_pdf), "application/pdf")},
    )
    assert submit_res.status_code == 201
    new_ref = submit_res.json()
    assert new_ref["candidate_email"] == "alex.mercer@example.com"
    # Overrides existing row rather than creating a new row
    assert new_ref["id"] == old_referral.id
    assert new_ref["referral_number"] == old_referral.referral_number
    assert float(new_ref["years_of_experience"]) == 6.0
    assert new_ref["status"] == ReferralStatus.SUBMITTED.value

    # Verify only 1 row exists in the database for Alex Mercer and fields were overwritten in place
    db_alex_refs = db_session.query(Referral).filter(Referral.candidate_email == "alex.mercer@example.com").all()
    assert len(db_alex_refs) == 1
    assert db_alex_refs[0].id == old_referral.id
    assert db_alex_refs[0].referral_note == "Re-submitting Alex after 7 months for new opening."
    assert float(db_alex_refs[0].years_of_experience) == 6.0




