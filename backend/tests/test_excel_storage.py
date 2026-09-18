import os
import openpyxl
import pytest
from app.services.excel.local_excel_service import LocalExcelService


def test_excel_workbook_initialization(tmp_path):
    """Verify Excel workbook creates all 5 structured sheets with proper headers"""
    file_path = str(tmp_path / "test_referrals.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)

    excel_svc.initialize_workbook()
    assert os.path.exists(file_path)

    wb = openpyxl.load_workbook(file_path)
    expected_sheets = ["Referrals", "JobPositions", "StatusHistory", "HRNotes", "Users", "HiredHistory"]
    assert wb.sheetnames == expected_sheets

    # Verify Referrals headers
    ws_refs = wb["Referrals"]
    headers = [cell.value for cell in ws_refs[1]]
    assert "Referral Number" in headers
    assert "Candidate Name" in headers
    assert "Referred By" in headers
    assert "Status" in headers

    # Verify HiredHistory headers
    ws_hired = wb["HiredHistory"]
    hired_headers = [cell.value for cell in ws_hired[1]]
    assert "Referral Number" in hired_headers
    assert "Candidate Name" in hired_headers
    assert "Hired Date" in hired_headers
    assert "Position Title" in hired_headers
    wb.close()



def test_excel_append_and_status_update(tmp_path):
    """Verify referral append, status update, and history tracking in Excel"""
    file_path = str(tmp_path / "test_referrals.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)
    excel_svc.initialize_workbook()

    # Append referral
    ref_data = {
        "id": "ref-unit-001",
        "referral_number": "REF-2026-UNIT01",
        "candidate_name": "Test Candidate",
        "candidate_email": "candidate@test.com",
        "candidate_phone": "+14160001111",
        "referred_by_name": "Referring Employee",
        "years_of_experience": 4.5,
        "relationship": "Former Colleague",
        "position_title": "Senior Developer",
        "status": "Submitted",
    }
    excel_svc.append_referral(ref_data)

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 2
    assert ws.cell(row=2, column=1).value == "REF-2026-UNIT01"
    assert ws.cell(row=2, column=2).value == "Test Candidate"
    assert ws.cell(row=2, column=5).value == "Referring Employee"
    assert ws.cell(row=2, column=9).value == "Submitted"
    wb.close()

    # Update status
    excel_svc.update_referral_status(
        referral_id="ref-unit-001",
        referral_number="REF-2026-UNIT01",
        new_status="Shortlisted",
        comment="Candidate shortlisted for interview",
        changed_by="HR Lead",
    )

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.cell(row=2, column=9).value == "Shortlisted"

    # Verify history sheet
    ws_hist = wb["StatusHistory"]
    assert ws_hist.max_row >= 3  # Header + initial submitted + shortlisted update
    wb.close()


def test_excel_export_bytes(tmp_path):
    """Verify raw workbook bytes can be retrieved for download"""
    file_path = str(tmp_path / "test_referrals.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)
    excel_svc.initialize_workbook()

    raw_bytes = excel_svc.get_workbook_bytes()
    assert len(raw_bytes) > 0
    # Check standard zip/xlsx magic bytes (PK)
    assert raw_bytes[:2] == b"PK"


def test_hired_history_excel_storage_and_export(tmp_path):
    """Verify saving hired records to HiredHistory worksheet and generating standalone export"""
    from app.services.excel.local_excel_service import generate_hired_history_workbook_bytes

    file_path = str(tmp_path / "test_referrals.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)
    excel_svc.initialize_workbook()

    hired_record = {
        "id": "ref-hired-001",
        "referral_number": "REF-2026-HIRED01",
        "candidate_name": "Elena Rostova",
        "candidate_email": "elena@example.com",
        "position_id": "job-001",
        "position_title": "Senior Cloud Architect",
        "department": "Cloud & Infrastructure",
        "location": "Toronto, Canada",
        "employment_type": "Full-time",
        "referred_by_name": "Marcus Vance",
        "hired_at": "2026-09-15 14:30:00",
        "status": "Hired",
    }
    excel_svc.save_hired_record(hired_record)

    # Check worksheet
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws_hired = wb["HiredHistory"]
    assert ws_hired.max_row == 2
    assert ws_hired.cell(row=2, column=1).value == "REF-2026-HIRED01"
    assert ws_hired.cell(row=2, column=2).value == "Elena Rostova"
    assert ws_hired.cell(row=2, column=4).value == "Senior Cloud Architect"
    assert ws_hired.cell(row=2, column=10).value == "Hired"
    wb.close()

    # Test standalone workbook generator
    export_bytes = generate_hired_history_workbook_bytes([hired_record])
    assert len(export_bytes) > 0
    assert export_bytes[:2] == b"PK"

    # Verify content in standalone export
    import io
    standalone_wb = openpyxl.load_workbook(io.BytesIO(export_bytes), data_only=True)
    assert "HiredHistory" in standalone_wb.sheetnames
    standalone_ws = standalone_wb["HiredHistory"]
    assert standalone_ws.cell(row=2, column=2).value == "Elena Rostova"
    standalone_wb.close()


def test_excel_delete_first_middle_last_referrals(tmp_path):
    """
    Verify deletion of first, middle, and last referrals in Excel:
    - Row is physically removed and subsequent records shift upward
    - No blank rows left immediately below header or between records
    - Referral numbers and IDs are strictly preserved
    - Associated StatusHistory, HRNotes, and HiredHistory rows are cleaned up
    - Append, update, and hydration (load_all_data) continue to work seamlessly
    """
    file_path = str(tmp_path / "test_delete_sequence.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)
    excel_svc.initialize_workbook()

    refs = [
        {
            "id": "ref-001",
            "referral_number": "REF-2026-000001",
            "candidate_name": "Candidate One",
            "candidate_email": "one@example.com",
            "position_title": "Backend Dev",
            "status": "Submitted",
        },
        {
            "id": "ref-002",
            "referral_number": "REF-2026-000002",
            "candidate_name": "Candidate Two",
            "candidate_email": "two@example.com",
            "position_title": "Frontend Dev",
            "status": "Submitted",
        },
        {
            "id": "ref-003",
            "referral_number": "REF-2026-000003",
            "candidate_name": "Candidate Three",
            "candidate_email": "three@example.com",
            "position_title": "ML Engineer",
            "status": "Submitted",
        },
        {
            "id": "ref-004",
            "referral_number": "REF-2026-000004",
            "candidate_name": "Candidate Four",
            "candidate_email": "four@example.com",
            "position_title": "DevOps SRE",
            "status": "Submitted",
        },
    ]

    for r in refs:
        excel_svc.append_referral(r)
        excel_svc.append_hr_note(r["id"], r["referral_number"], f"Note for {r['candidate_name']}", "HR Admin")

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 5  # Row 1 header + 4 referrals
    assert ws.cell(row=2, column=1).value == "REF-2026-000001"
    assert ws.cell(row=3, column=1).value == "REF-2026-000002"
    assert ws.cell(row=4, column=1).value == "REF-2026-000003"
    assert ws.cell(row=5, column=1).value == "REF-2026-000004"
    wb.close()

    # --- 1. DELETE FIRST REFERRAL (ref-001 at Row 2) ---
    excel_svc.delete_referral("ref-001")

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 4, "Row count should decrement to 4 after deleting first referral"
    # Row 2 must now contain Candidate Two (shifted upward directly beneath header)
    assert ws.cell(row=2, column=1).value == "REF-2026-000002"
    assert ws.cell(row=2, column=2).value == "Candidate Two"
    assert ws.cell(row=2, column=10).value == "ref-002"
    # Row 3 is Candidate Three
    assert ws.cell(row=3, column=1).value == "REF-2026-000003"
    assert ws.cell(row=3, column=2).value == "Candidate Three"
    assert ws.cell(row=3, column=10).value == "ref-003"
    # Row 4 is Candidate Four
    assert ws.cell(row=4, column=1).value == "REF-2026-000004"
    assert ws.cell(row=4, column=2).value == "Candidate Four"
    assert ws.cell(row=4, column=10).value == "ref-004"

    # StatusHistory & HRNotes for ref-001 should be removed
    ws_notes = wb["HRNotes"]
    note_ref_ids = [ws_notes.cell(row=r, column=2).value for r in range(2, ws_notes.max_row + 1)]
    assert "ref-001" not in note_ref_ids
    assert "ref-002" in note_ref_ids
    wb.close()

    # --- 2. DELETE MIDDLE REFERRAL (ref-003, currently at Row 3) ---
    excel_svc.delete_referral("ref-003")

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 3, "Row count should decrement to 3 after deleting middle referral"
    # Row 2 remains Candidate Two
    assert ws.cell(row=2, column=1).value == "REF-2026-000002"
    assert ws.cell(row=2, column=10).value == "ref-002"
    # Row 3 must now contain Candidate Four (shifted upward into middle slot)
    assert ws.cell(row=3, column=1).value == "REF-2026-000004"
    assert ws.cell(row=3, column=2).value == "Candidate Four"
    assert ws.cell(row=3, column=10).value == "ref-004"
    wb.close()

    # --- 3. DELETE LAST REFERRAL (ref-004, currently at Row 3) ---
    excel_svc.delete_referral("ref-004")

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 2, "Row count should decrement to 2 after deleting last referral"
    # Only Candidate Two remains
    assert ws.cell(row=2, column=1).value == "REF-2026-000002"
    assert ws.cell(row=2, column=2).value == "Candidate Two"
    assert ws.cell(row=2, column=10).value == "ref-002"
    wb.close()

    # --- 4. VERIFY APPEND, UPDATE, AND LOAD AFTER DELETIONS ---
    # Append a new referral and verify it is placed directly at Row 3 with no gap
    ref5 = {
        "id": "ref-005",
        "referral_number": "REF-2026-000005",
        "candidate_name": "Candidate Five",
        "candidate_email": "five@example.com",
        "position_title": "Cloud Architect",
        "status": "Submitted",
    }
    excel_svc.append_referral(ref5)

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 3
    assert ws.cell(row=2, column=1).value == "REF-2026-000002"
    assert ws.cell(row=3, column=1).value == "REF-2026-000005"
    assert ws.cell(row=3, column=2).value == "Candidate Five"
    wb.close()

    # Update status of remaining referral (ref-002) at Row 2
    excel_svc.update_referral_status(
        referral_id="ref-002",
        referral_number="REF-2026-000002",
        new_status="Interview",
        comment="Proceeding to interview",
        changed_by="HR Lead",
    )
    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.cell(row=2, column=9).value == "Interview"
    wb.close()

    # Hydration / load_all_data test
    data = excel_svc.load_all_data()
    loaded_refs = data["Referrals"]
    assert len(loaded_refs) == 2
    assert loaded_refs[0]["Referral Number"] == "REF-2026-000002"
    assert loaded_refs[0]["Referral ID"] == "ref-002"
    assert loaded_refs[0]["Status"] == "Interview"
    assert loaded_refs[1]["Referral Number"] == "REF-2026-000005"
    assert loaded_refs[1]["Referral ID"] == "ref-005"


def test_excel_blank_rows_healed_on_init_and_delete(tmp_path):
    """
    Verify that existing blank rows below the header are normalized:
    subsequent records shift upward directly below header row 1,
    and referral numbers/IDs remain intact.
    """
    file_path = str(tmp_path / "test_legacy_blank_rows.xlsx")
    excel_svc = LocalExcelService(file_path=file_path)
    excel_svc.initialize_workbook()

    # Manually introduce blank rows 2 and 3 before inserting a referral at row 4
    wb = openpyxl.load_workbook(file_path)
    ws = wb["Referrals"]
    # Row 2 and Row 3 are left empty
    for r in (2, 3):
        for c in range(1, 15):
            ws.cell(row=r, column=c).value = None

    # Put a referral at row 4
    ws.cell(row=4, column=1).value = "REF-2026-000099"
    ws.cell(row=4, column=2).value = "Legacy Candidate"
    ws.cell(row=4, column=10).value = "ref-legacy-99"
    ws.cell(row=4, column=9).value = "Submitted"
    wb.save(file_path)
    wb.close()

    # Re-initialize or perform deletion operation to trigger cleanup
    excel_svc.initialize_workbook()

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb["Referrals"]
    assert ws.max_row == 2, "Blank rows should be removed, leaving only header + 1 record"
    assert ws.cell(row=2, column=1).value == "REF-2026-000099"
    assert ws.cell(row=2, column=2).value == "Legacy Candidate"
    assert ws.cell(row=2, column=10).value == "ref-legacy-99"
    wb.close()


