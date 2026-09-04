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
    expected_sheets = ["Referrals", "JobPositions", "StatusHistory", "HRNotes", "Users"]
    assert wb.sheetnames == expected_sheets

    # Verify Referrals headers
    ws_refs = wb["Referrals"]
    headers = [cell.value for cell in ws_refs[1]]
    assert "Referral Number" in headers
    assert "Candidate Name" in headers
    assert "Referred By" in headers
    assert "Status" in headers
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
