import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus
from app.models.status_history import ReferralStatusHistory
from app.models.hr_note import HRNote
from app.services.excel.base import ExcelServiceInterface

logger = logging.getLogger(__name__)


SAMPLE_JOBS = [
    {
        "id": "job-001",
        "title": "Senior Backend Developer (Python / FastAPI)",
        "department": "Engineering",
        "description": "Looking for an experienced backend developer skilled in Python, FastAPI, and cloud distributed architectures.",
        "location": "Toronto, Canada (Hybrid)",
        "employment_type": "Full-time",
        "is_active": True,
    },
    {
        "id": "job-002",
        "title": "AI & Machine Learning Engineer",
        "department": "AI Innovations",
        "description": "Responsible for designing and implementing LLM evaluation pipelines, agentic workflows, and semantic search systems.",
        "location": "Goa, India (Remote)",
        "employment_type": "Full-time",
        "is_active": True,
    },
    {
        "id": "job-003",
        "title": "Senior Cloud Solutions Architect",
        "department": "Cloud & Infrastructure",
        "description": "Lead enterprise architecture initiatives across Microsoft Azure, AWS, and secure hybrid cloud deployments.",
        "location": "New York, USA",
        "employment_type": "Full-time",
        "is_active": True,
    },
    {
        "id": "job-004",
        "title": "Frontend Lead (React + TypeScript)",
        "department": "Engineering",
        "description": "Build high-performance web applications, design systems, and responsive enterprise portals using React 18+ and modern CSS.",
        "location": "Toronto, Canada",
        "employment_type": "Full-time",
        "is_active": True,
    },
    {
        "id": "job-005",
        "title": "DevOps & SRE Specialist",
        "department": "Operations",
        "description": "Maintain CI/CD pipelines, Kubernetes clusters, infrastructure-as-code with Terraform, and zero-downtime releases.",
        "location": "Goa, India",
        "employment_type": "Full-time",
        "is_active": True,
    },
]


def initialize_and_sync_excel(db: Session, excel_svc: ExcelServiceInterface) -> None:
    """
    On application startup:
    1. Ensure the Microsoft Excel workbook exists with structured sheets.
    2. If the workbook is empty, seed it with default users, jobs, and sample referrals.
    3. Load data from the Excel workbook into the in-memory database engine.
    """
    excel_svc.initialize_workbook()
    data = excel_svc.load_all_data()

    # Check if Excel workbook already has job positions or referrals
    has_jobs = len(data.get("JobPositions", [])) > 0
    has_referrals = len(data.get("Referrals", [])) > 0

    if not has_jobs:
        logger.info("Excel workbook is new or empty. Seeding default data...")
        # 1. Seed Users in DB and Excel
        hr_user = User(
            id="user-hr-001",
            entra_user_id="user-dev-hr-001",
            name="Marcus Vance",
            email="hr.lead@tangentia.com",
            password="TangentiaHR@2026",
            role=UserRole.HR_ADMIN.value,
            department="Human Resources",
        )
        emp_user = User(
            id="user-emp-001",
            entra_user_id="user-dev-employee-001",
            name="Vansh Rupesh (Employee)",
            email="employee@tangentia.com",
            password="",
            role=UserRole.EMPLOYEE.value,
            department="Cloud Engineering",
        )
        db.merge(hr_user)
        db.merge(emp_user)
        db.commit()

        excel_svc.save_user({
            "id": "user-hr-001",
            "name": "Marcus Vance",
            "email": "hr.lead@tangentia.com",
            "password": "TangentiaHR@2026",
            "role": UserRole.HR_ADMIN.value,
            "department": "Human Resources",
        })
        excel_svc.save_user({
            "id": "user-emp-001",
            "name": "Vansh Rupesh (Employee)",
            "email": "employee@tangentia.com",
            "password": "",
            "role": UserRole.EMPLOYEE.value,
            "department": "Cloud Engineering",
        })

        # 2. Seed Jobs in DB and Excel
        for j_data in SAMPLE_JOBS:
            job = JobPosition(
                id=j_data["id"],
                title=j_data["title"],
                department=j_data["department"],
                description=j_data["description"],
                location=j_data["location"],
                employment_type=j_data["employment_type"],
                is_active=j_data["is_active"],
            )
            db.merge(job)
            excel_svc.save_job_position(j_data)
        db.commit()

        # 3. Seed Sample Referrals in DB and Excel
        sample_refs = [
            {
                "id": "ref-001",
                "referral_number": "REF-2026-000001",
                "candidate_name": "Rahul Sharma",
                "candidate_email": "rahul.sharma@example.com",
                "candidate_phone": "+14165550192",
                "referred_by_name": "Vansh Rupesh (Employee)",
                "years_of_experience": 6.5,
                "relationship": "Former Colleague",
                "position_id": "job-001",
                "position_title": "Senior Backend Developer (Python / FastAPI)",
                "status": ReferralStatus.INTERVIEW.value,
                "referred_by_user_id": "user-emp-001",
                "original_filename": "Rahul_Sharma_CV.pdf",
                "sharepoint_file_url": "https://tangentia.sharepoint.com/sites/hr/Referral-CVs/Rahul_Sharma_CV.pdf",
                "referral_note": "Worked with Rahul at FinTech Corp. Brilliant distributed systems knowledge and very proactive team player.",
            },
            {
                "id": "ref-002",
                "referral_number": "REF-2026-000002",
                "candidate_name": "Ananya Patel",
                "candidate_email": "ananya.patel@example.com",
                "candidate_phone": "+919820011223",
                "referred_by_name": "Vansh Rupesh (Employee)",
                "years_of_experience": 4.0,
                "relationship": "College Alumni",
                "position_id": "job-002",
                "position_title": "AI & Machine Learning Engineer",
                "status": ReferralStatus.SHORTLISTED.value,
                "referred_by_user_id": "user-emp-001",
                "original_filename": "Ananya_Patel_CV.pdf",
                "sharepoint_file_url": "https://tangentia.sharepoint.com/sites/hr/Referral-CVs/Ananya_Patel_CV.pdf",
                "referral_note": "Ananya has published research papers in NLP and built agentic search engines using LangChain and FastAPI.",
            },
            {
                "id": "ref-003",
                "referral_number": "REF-2026-000003",
                "candidate_name": "David Chen",
                "candidate_email": "david.chen@example.com",
                "candidate_phone": "+16475550144",
                "referred_by_name": "Vansh Rupesh (Employee)",
                "years_of_experience": 8.0,
                "relationship": "Professional Network",
                "position_id": "job-003",
                "position_title": "Senior Cloud Solutions Architect",
                "status": ReferralStatus.UNDER_REVIEW.value,
                "referred_by_user_id": "user-emp-001",
                "original_filename": "David_Chen_CV.pdf",
                "sharepoint_file_url": "https://tangentia.sharepoint.com/sites/hr/Referral-CVs/David_Chen_CV.pdf",
                "referral_note": "David is a seasoned cloud architect who led multi-region Azure migrations at his previous enterprise employer.",
            },
        ]

        for r_info in sample_refs:
            ref_model = Referral(
                id=r_info["id"],
                referral_number=r_info["referral_number"],
                candidate_name=r_info["candidate_name"],
                candidate_email=r_info["candidate_email"],
                candidate_phone=r_info["candidate_phone"],
                referred_by_name=r_info["referred_by_name"],
                years_of_experience=r_info["years_of_experience"],
                relationship=r_info["relationship"],
                position_id=r_info["position_id"],
                referred_by_user_id=r_info["referred_by_user_id"],
                status=r_info["status"],
                original_filename=r_info["original_filename"],
                stored_filename=r_info["original_filename"],
                sharepoint_file_url=r_info["sharepoint_file_url"],
                referral_note=r_info["referral_note"],
                candidate_consent=True,
            )
            db.merge(ref_model)
            excel_svc.append_referral(r_info)
        db.commit()
        logger.info("Default seed data written to Microsoft Excel workbook and in-memory engine.")

    else:
        # Load records from Excel into in-memory DB
        logger.info("Hydrating in-memory engine from Microsoft Excel workbook...")

        # 1. Ensure default users exist — commit them first to populate the identity map
        db.merge(User(
            id="user-hr-001",
            entra_user_id="user-dev-hr-001",
            name="Marcus Vance",
            email="hr.lead@tangentia.com",
            password="TangentiaHR@2026",
            role=UserRole.HR_ADMIN.value,
            department="Human Resources",
        ))
        db.merge(User(
            id="user-emp-001",
            entra_user_id="user-dev-employee-001",
            name="Vansh Rupesh (Employee)",
            email="employee@tangentia.com",
            password="",
            role=UserRole.EMPLOYEE.value,
            department="Cloud Engineering",
        ))
        db.commit()  # Commit defaults first so email UNIQUE index is populated

        # Collect emails already in DB to avoid UNIQUE constraint on email
        existing_emails = {u.email.lower() for u in db.query(User).all()}
        existing_ids = {u.id for u in db.query(User).all()}

        # Check if Excel Users sheet is empty, seed default HR user
        if len(data.get("Users", [])) == 0:
            excel_svc.save_user({
                "id": "user-hr-001",
                "name": "Marcus Vance",
                "email": "hr.lead@tangentia.com",
                "password": "TangentiaHR@2026",
                "role": UserRole.HR_ADMIN.value,
                "department": "Human Resources",
            })
            data = excel_svc.load_all_data()

        # Merge users from Excel Users sheet, skipping any already loaded by ID or email
        for u_row in data.get("Users", []):
            u_id = str(u_row.get("User ID") or "").strip()
            u_email = str(u_row.get("Email") or "").strip().lower()
            if not u_id:
                continue
            # Use merge (upsert by PK) — it safely updates existing rows without duplicate inserts
            u_role = str(u_row.get("Role") or UserRole.EMPLOYEE.value)
            u_pass = str(u_row.get("Password") or "").strip()
            # Preserve a stable entra_user_id if user already exists
            entra_id = str(u_row.get("Entra User ID") or "").strip()
            if not entra_id:
                if u_id in existing_ids:
                    existing_user = db.query(User).filter(User.id == u_id).first()
                    entra_id = existing_user.entra_user_id or f"user-{u_id[:8]}"
                else:
                    entra_id = f"user-{u_id[:8]}"
            u_obj = User(
                id=u_id,
                name=str(u_row.get("Name") or "Employee"),
                email=u_email or f"{u_id[:8]}@tangentia.com",
                password=u_pass,
                role=u_role,
                department=str(u_row.get("Department") or "Engineering"),
                entra_user_id=entra_id,
            )
            try:
                db.merge(u_obj)
                db.flush()
                existing_emails.add(u_email)
                existing_ids.add(u_id)
            except Exception as ue:
                db.rollback()
                logger.warning(f"Skipping duplicate user {u_id} ({u_email}): {ue}")
        db.commit()

        # 2. Load Jobs
        existing_job_ids = set()
        for row in data.get("JobPositions", []):
            job_id = str(row.get("Job ID") or uuid.uuid4()).strip()
            is_act = str(row.get("Is Active") or "Yes").strip().lower() in ["yes", "true", "1"]
            job = JobPosition(
                id=job_id,
                title=str(row.get("Title") or "Job Title"),
                department=str(row.get("Department") or "Engineering"),
                description=str(row.get("Description") or ""),
                location=str(row.get("Location") or "Remote"),
                employment_type=str(row.get("Employment Type") or "Full-time"),
                is_active=is_act,
            )
            db.merge(job)
            existing_job_ids.add(job_id)

        # Merge any sample jobs that aren't yet in the database
        for s_job in SAMPLE_JOBS:
            if s_job["id"] not in existing_job_ids:
                job = JobPosition(
                    id=s_job["id"],
                    title=s_job["title"],
                    department=s_job["department"],
                    description=s_job["description"],
                    location=s_job["location"],
                    employment_type=s_job["employment_type"],
                    is_active=s_job["is_active"],
                )
                db.merge(job)
                existing_job_ids.add(s_job["id"])
        db.commit()

        # 3. Load Referrals with collision resolution and foreign key safety
        valid_job_ids = {j.id for j in db.query(JobPosition.id).all()}
        valid_user_ids = {u.id for u in db.query(User.id).all()}
        seen_ref_numbers = set()
        seen_ids = set()

        current_year = datetime.now(timezone.utc).year
        max_seq = 0
        for r_row in data.get("Referrals", []):
            raw_num = str(r_row.get("Referral Number") or "").strip()
            if raw_num.startswith(f"REF-{current_year}-"):
                try:
                    num_val = int(raw_num.split("-")[-1])
                    if num_val > max_seq:
                        max_seq = num_val
                except (ValueError, IndexError):
                    pass

        loaded_count = 0
        for row in data.get("Referrals", []):
            try:
                raw_id = str(row.get("Referral ID") or "").strip()
                if not raw_id or raw_id in seen_ids:
                    ref_id = str(uuid.uuid4())
                else:
                    ref_id = raw_id
                seen_ids.add(ref_id)

                raw_num = str(row.get("Referral Number") or "").strip()
                if not raw_num or raw_num in seen_ref_numbers:
                    max_seq += 1
                    ref_num = f"REF-{current_year}-{max_seq:06d}"
                else:
                    ref_num = raw_num
                seen_ref_numbers.add(ref_num)

                cand_name = str(row.get("Candidate Name") or "Candidate").strip()
                cand_email = str(row.get("Candidate Email") or f"candidate_{ref_id[:6]}@example.com").strip()
                cand_phone = str(row.get("Candidate Phone") or "+1000000000").strip()
                referred_by = str(row.get("Referred By") or "Vansh Rupesh").strip()

                pos_id = str(row.get("Position ID") or "").strip()
                pos_title = str(row.get("Position Title") or "General Position").strip()
                if not pos_id or pos_id not in valid_job_ids:
                    if pos_id:
                        new_job = JobPosition(
                            id=pos_id,
                            title=pos_title,
                            department="Engineering",
                            description=f"Role: {pos_title}",
                            location="Toronto, Canada (Hybrid)",
                            employment_type="Full-time",
                            is_active=True,
                        )
                        db.merge(new_job)
                        db.commit()
                        valid_job_ids.add(pos_id)
                    else:
                        pos_id = "job-001"

                ref_by_uid = str(row.get("Referred By User ID") or "").strip()
                if not ref_by_uid or ref_by_uid not in valid_user_ids:
                    if ref_by_uid:
                        new_user = User(
                            id=ref_by_uid,
                            name=referred_by or "Tangentia Employee",
                            email=f"{ref_by_uid[:8]}@tangentia.com",
                            role=UserRole.EMPLOYEE.value,
                            department="Engineering",
                            entra_user_id=f"entra-{ref_by_uid}",
                        )
                        db.merge(new_user)
                        db.commit()
                        valid_user_ids.add(ref_by_uid)
                    else:
                        ref_by_uid = "user-emp-001"

                status_val = str(row.get("Status") or "Submitted").strip()
                try:
                    exp = float(row.get("Years Experience") or 0.0)
                except (ValueError, TypeError):
                    exp = 0.0
                rel = str(row.get("Relationship") or "Former Colleague").strip()
                note = str(row.get("Referral Note") or "Referred candidate.").strip()
                orig_file = str(row.get("Original CV Filename") or "resume.pdf").strip()
                sp_url = str(row.get("SharePoint CV URL") or "").strip()
                li_url = str(row.get("LinkedIn URL") or "").strip() or None
                gh_url = str(row.get("GitHub URL") or "").strip() or None

                created_at_dt = datetime.now(timezone.utc)
                created_at_raw = row.get("Created At")
                if created_at_raw:
                    try:
                        created_at_dt = datetime.fromisoformat(str(created_at_raw))
                    except Exception:
                        try:
                            created_at_dt = datetime.strptime(str(created_at_raw), "%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass

                sp_drive_id = None
                sp_item_id = None
                stored_file = orig_file
                if sp_url:
                    if "/referral-cvs/" in sp_url:
                        blob_path = sp_url.split("/referral-cvs/")[-1]
                        sp_item_id = f"blob:{blob_path}"
                        sp_drive_id = "blob:referral-cvs"
                        stored_file = blob_path.split("/")[-1]
                    elif "sharepoint.com" in sp_url:
                        parts = sp_url.rstrip("/").split("/")
                        if parts:
                            stored_file = parts[-1]

                ref = Referral(
                    id=ref_id,
                    referral_number=ref_num,
                    candidate_name=cand_name,
                    candidate_email=cand_email,
                    candidate_phone=cand_phone,
                    referred_by_name=referred_by,
                    years_of_experience=exp,
                    relationship=rel,
                    position_id=pos_id,
                    referred_by_user_id=ref_by_uid,
                    status=status_val,
                    original_filename=orig_file,
                    stored_filename=stored_file,
                    sharepoint_drive_id=sp_drive_id,
                    sharepoint_item_id=sp_item_id,
                    sharepoint_file_url=sp_url,
                    linkedin_url=li_url,
                    github_url=gh_url,
                    referral_note=note,
                    candidate_consent=True,
                    created_at=created_at_dt,
                    updated_at=created_at_dt,
                )
                db.merge(ref)
                db.commit()
                loaded_count += 1
            except Exception as row_err:
                db.rollback()
                logger.warning(f"Error loading referral row: {row_err}")

        # 4. Load Status History if present
        for h_row in data.get("StatusHistory", []):
            h_id = str(h_row.get("History ID") or "").strip()
            r_id = str(h_row.get("Referral ID") or "").strip()
            if h_id and r_id and r_id in seen_ids:
                try:
                    c_by = str(h_row.get("Changed By") or "user-hr-001")
                    history = ReferralStatusHistory(
                        id=h_id,
                        referral_id=r_id,
                        old_status=str(h_row.get("Old Status") or ""),
                        new_status=str(h_row.get("New Status") or "Submitted"),
                        changed_by_user_id=c_by if c_by in valid_user_ids else "user-hr-001",
                        comment=str(h_row.get("Comment") or ""),
                    )
                    db.merge(history)
                except Exception:
                    pass
        db.commit()

        # 5. Load HR Notes if present
        for n_row in data.get("HRNotes", []):
            n_id = str(n_row.get("Note ID") or "").strip()
            r_id = str(n_row.get("Referral ID") or "").strip()
            if n_id and r_id and r_id in seen_ids:
                try:
                    c_by = str(n_row.get("Created By") or "user-hr-001")
                    note_obj = HRNote(
                        id=n_id,
                        referral_id=r_id,
                        created_by_user_id=c_by if c_by in valid_user_ids else "user-hr-001",
                        note=str(n_row.get("Note") or ""),
                    )
                    db.merge(note_obj)
                except Exception:
                    pass
        logger.info(f"Loaded {loaded_count} referrals from Microsoft Excel into runtime engine.")

    # Ensure all Hired referrals in DB are synchronized to HiredHistory worksheet in Excel
    try:
        hired_refs = db.query(Referral).outerjoin(Referral.position).filter(
            Referral.status == ReferralStatus.HIRED.value
        ).all()
        for hr in hired_refs:
            pos = hr.position
            excel_svc.save_hired_record({
                "id": hr.id,
                "referral_number": hr.referral_number,
                "candidate_name": hr.candidate_name,
                "candidate_email": hr.candidate_email,
                "position_id": hr.position_id,
                "position_title": pos.title if pos else "Unknown Position",
                "department": pos.department if pos else "General",
                "location": pos.location if pos else "Tangentia Office",
                "employment_type": pos.employment_type if pos else "Full-time",
                "referred_by_name": hr.referred_by_name or (hr.referred_by.name if hr.referred_by else "Employee"),
                "hired_at": hr.updated_at or hr.created_at,
                "status": "Hired",
            })
    except Exception as sync_hired_err:
        logger.warning(f"Error synchronizing HiredHistory sheet in Excel: {sync_hired_err}")

