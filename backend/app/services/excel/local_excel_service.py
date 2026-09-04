import os
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from app.config import settings
from app.services.excel.base import ExcelServiceInterface

logger = logging.getLogger(__name__)

# Standard Styling Constants
HEADER_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
HEADER_FONT = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
DATA_FONT = Font(name="Segoe UI", size=10)
BORDER_THIN = Border(
    left=Side(style="thin", color="E2E8F0"),
    right=Side(style="thin", color="E2E8F0"),
    top=Side(style="thin", color="E2E8F0"),
    bottom=Side(style="thin", color="E2E8F0"),
)

SHEET_SCHEMAS = {
    "Referrals": [
        "Referral Number",
        "Candidate Name",
        "Candidate Email",
        "Candidate Phone",
        "Referred By",
        "Years Experience",
        "Relationship",
        "Position Title",
        "Status",
        "Referral ID",
        "Position ID",
        "Referred By User ID",
        "LinkedIn URL",
        "GitHub URL",
        "Original CV Filename",
        "SharePoint CV URL",
        "Referral Note",
        "Created At",
        "Updated At",
    ],
    "JobPositions": [
        "Job ID",
        "Title",
        "Department",
        "Location",
        "Employment Type",
        "Is Active",
        "Description",
        "Created At",
        "Updated At",
    ],
    "StatusHistory": [
        "History ID",
        "Referral ID",
        "Referral Number",
        "Old Status",
        "New Status",
        "Changed By",
        "Comment",
        "Created At",
    ],
    "HRNotes": [
        "Note ID",
        "Referral ID",
        "Referral Number",
        "Created By",
        "Note",
        "Created At",
        "Updated At",
    ],
    "Users": [
        "User ID",
        "Name",
        "Email",
        "Role",
        "Department",
        "Entra User ID",
        "Created At",
    ],
}


class LocalExcelService(ExcelServiceInterface):
    """
    Local Microsoft Excel (.xlsx) implementation using openpyxl.
    Manages Tangentia_Referrals.xlsx with styled sheets, auto-widths, and atomic updates.
    """

    def __init__(self, file_path: Optional[str] = None):
        self.file_path = file_path or settings.EXCEL_FILE_PATH
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

    def _style_header_row(self, ws, headers: List[str]):
        """Apply Tangentia branding to header row with frozen panes"""
        ws.append(headers)
        ws.freeze_panes = "A2"
        for col_idx, _ in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = BORDER_THIN
        ws.row_dimensions[1].height = 26

    def _auto_adjust_column_widths(self, ws):
        """Auto-adjust column widths for optimal reading in Excel"""
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    def initialize_workbook(self) -> None:
        """Create structured Excel workbook if it doesn't exist"""
        with self._lock:
            if os.path.exists(self.file_path):
                return

            wb = openpyxl.Workbook()
            default_sheet = wb.active
            wb.remove(default_sheet)

            for sheet_name, headers in SHEET_SCHEMAS.items():
                ws = wb.create_sheet(title=sheet_name)
                self._style_header_row(ws, headers)
                self._auto_adjust_column_widths(ws)

            wb.save(self.file_path)
            logger.info(f"Initialized Microsoft Excel workbook at: {self.file_path}")

    def load_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Read all records from Excel sheets into memory"""
        with self._lock:
            if not os.path.exists(self.file_path):
                return {k: [] for k in SHEET_SCHEMAS}

            wb = openpyxl.load_workbook(self.file_path, data_only=True)
            result = {}

            for sheet_name, headers in SHEET_SCHEMAS.items():
                rows = []
                if sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    # Read rows after header
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        if not any(row):
                            continue
                        row_dict = {}
                        for idx, header in enumerate(headers):
                            val = row[idx] if idx < len(row) else None
                            row_dict[header] = val
                        rows.append(row_dict)
                result[sheet_name] = rows

            wb.close()
            return result

    def append_referral(self, ref: Dict[str, Any]) -> None:
        """Append a new referral row to Referrals sheet"""
        with self._lock:
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Referrals"]

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            row_values = [
                ref.get("referral_number", ""),
                ref.get("candidate_name", ""),
                ref.get("candidate_email", ""),
                ref.get("candidate_phone", ""),
                ref.get("referred_by_name", ""),
                ref.get("years_of_experience", 0.0),
                ref.get("relationship", ""),
                ref.get("position_title", ""),
                ref.get("status", "Submitted"),
                ref.get("id", ""),
                ref.get("position_id", ""),
                ref.get("referred_by_user_id", ""),
                ref.get("linkedin_url", "") or "",
                ref.get("github_url", "") or "",
                ref.get("original_filename", ""),
                ref.get("sharepoint_file_url", "") or "",
                ref.get("referral_note", ""),
                ref.get("created_at", now_str),
                ref.get("updated_at", now_str),
            ]
            ws.append(row_values)

            # Style appended row
            row_idx = ws.max_row
            for col_idx in range(1, len(row_values) + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = DATA_FONT
                cell.border = BORDER_THIN
                cell.alignment = Alignment(vertical="center")

            # Also log to StatusHistory sheet
            ws_hist = wb["StatusHistory"]
            import uuid
            hist_row = [
                str(uuid.uuid4()),
                ref.get("id", ""),
                ref.get("referral_number", ""),
                "",
                ref.get("status", "Submitted"),
                ref.get("referred_by_name", "Employee"),
                f"Referral submitted by {ref.get('referred_by_name', 'Employee')}.",
                now_str,
            ]
            ws_hist.append(hist_row)

            self._auto_adjust_column_widths(ws)
            wb.save(self.file_path)
            wb.close()

    def update_referral_status(
        self,
        referral_id: str,
        referral_number: str,
        new_status: str,
        comment: Optional[str],
        changed_by: str,
    ) -> None:
        """Update referral status and append audit history"""
        with self._lock:
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["Referrals"]

            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            old_status = ""

            # Locate referral row by referral_id (Column 10: Referral ID)
            for row in range(2, ws.max_row + 1):
                cell_id = ws.cell(row=row, column=10).value
                if cell_id == referral_id:
                    old_status = ws.cell(row=row, column=9).value or ""
                    ws.cell(row=row, column=9).value = new_status  # Column 9: Status
                    ws.cell(row=row, column=19).value = now_str   # Column 19: Updated At
                    break

            # Append to StatusHistory
            import uuid
            ws_hist = wb["StatusHistory"]
            ws_hist.append([
                str(uuid.uuid4()),
                referral_id,
                referral_number,
                old_status,
                new_status,
                changed_by,
                comment or f"Status transitioned to {new_status}",
                now_str,
            ])

            wb.save(self.file_path)
            wb.close()

    def append_hr_note(
        self,
        referral_id: str,
        referral_number: str,
        note: str,
        created_by: str,
    ) -> None:
        """Append a note to HRNotes sheet"""
        with self._lock:
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["HRNotes"]
            import uuid
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            ws.append([
                str(uuid.uuid4()),
                referral_id,
                referral_number,
                created_by,
                note,
                now_str,
                now_str,
            ])
            wb.save(self.file_path)
            wb.close()

    def save_job_position(self, job: Dict[str, Any]) -> None:
        """Insert or update a job opening in JobPositions sheet"""
        with self._lock:
            wb = openpyxl.load_workbook(self.file_path)
            ws = wb["JobPositions"]

            job_id = job.get("id")
            found_row = None
            now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

            for row in range(2, ws.max_row + 1):
                if ws.cell(row=row, column=1).value == job_id:
                    found_row = row
                    break

            row_data = [
                job_id,
                job.get("title", ""),
                job.get("department", ""),
                job.get("location", ""),
                job.get("employment_type", "Full-time"),
                "Yes" if job.get("is_active", True) else "No",
                job.get("description", ""),
                job.get("created_at", now_str),
                now_str,
            ]

            if found_row:
                for col_idx, val in enumerate(row_data, 1):
                    ws.cell(row=found_row, column=col_idx).value = val
            else:
                ws.append(row_data)

            self._auto_adjust_column_widths(ws)
            wb.save(self.file_path)
            wb.close()

    def get_workbook_bytes(self) -> bytes:
        """Return binary content of the Excel workbook"""
        with self._lock:
            if not os.path.exists(self.file_path):
                return b""
            with open(self.file_path, "rb") as fp:
                return fp.read()

    def delete_referral(self, referral_id: str) -> None:
        """Delete referral row from Referrals sheet and cleanup its history/notes in Excel"""
        with self._lock:
            if not os.path.exists(self.file_path):
                return
            wb = openpyxl.load_workbook(self.file_path)

            # 1. Delete from Referrals sheet
            if "Referrals" in wb.sheetnames:
                ws = wb["Referrals"]
                row_to_delete = None
                for r in range(2, ws.max_row + 1):
                    if str(ws.cell(row=r, column=10).value or "").strip() == str(referral_id).strip():
                        row_to_delete = r
                        break
                if row_to_delete:
                    ws.delete_rows(row_to_delete)

            # 2. Clean up StatusHistory sheet
            if "StatusHistory" in wb.sheetnames:
                ws_h = wb["StatusHistory"]
                rows_to_del = []
                for r in range(2, ws_h.max_row + 1):
                    if str(ws_h.cell(row=r, column=2).value or "").strip() == str(referral_id).strip():
                        rows_to_del.append(r)
                for r in reversed(rows_to_del):
                    ws_h.delete_rows(r)

            # 3. Clean up HRNotes sheet
            if "HRNotes" in wb.sheetnames:
                ws_n = wb["HRNotes"]
                rows_to_del = []
                for r in range(2, ws_n.max_row + 1):
                    if str(ws_n.cell(row=r, column=2).value or "").strip() == str(referral_id).strip():
                        rows_to_del.append(r)
                for r in reversed(rows_to_del):
                    ws_n.delete_rows(r)

            wb.save(self.file_path)
            wb.close()
            logger.info(f"Deleted referral {referral_id} from Microsoft Excel workbook.")
