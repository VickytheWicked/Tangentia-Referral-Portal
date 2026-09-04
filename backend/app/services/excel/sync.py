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
            entra_user_id="entra-user-dev-hr-001",
            name="Marcus Vance",
            email="hr.lead@tangentia.com",
            role=UserRole.HR_ADMIN.value,
            department="Human Resources",
        )
        emp_user = User(
            id="user-emp-001",
            entra_user_id="entra-user-dev-employee-001",
            name="Vansh Rupesh (Employee)",
            email="employee@tangentia.com",
            role=UserRole.EMPLOYEE.value,
            department="Cloud Engineering",
        )
        db.merge(hr_user)
        db.merge(emp_user)
        db.commit()

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

        # 1. Ensure default users exist
        hr_user = User(
            id="user-hr-001",
            entra_user_id="entra-user-dev-hr-001",
            name="Marcus Vance",
            email="hr.lead@tangentia.com",
            role=UserRole.HR_ADMIN.value,
            department="Human Resources",
        )
        emp_user = User(
            id="user-emp-001",
            entra_user_id="entra-user-dev-employee-001",
            name="Vansh Rupesh (Employee)",
            email="employee@tangentia.com",
            role=UserRole.EMPLOYEE.value,
            department="Cloud Engineering",
        )
        db.merge(hr_user)
        db.merge(emp_user)

        # 2. Load Jobs
        for row in data.get("JobPositions", []):
            job_id = str(row.get("Job ID") or uuid.uuid4())
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

        # 3. Load Referrals
        for row in data.get("Referrals", []):
            ref_id = str(row.get("Referral ID") or uuid.uuid4())
            ref_num = str(row.get("Referral Number") or f"REF-{datetime.now().year}-{ref_id[:6]}")
            cand_name = str(row.get("Candidate Name") or "Candidate")
            cand_email = str(row.get("Candidate Email") or "candidate@example.com")
            cand_phone = str(row.get("Candidate Phone") or "+1000000000")
            pos_id = str(row.get("Position ID") or "job-001")
            referred_by = str(row.get("Referred By") or "Employee")
            ref_by_uid = str(row.get("Referred By User ID") or "user-emp-001")
            status_val = str(row.get("Status") or "Submitted")
            exp = float(row.get("Years Experience") or 0.0)
            rel = str(row.get("Relationship") or "Professional Network")
            note = str(row.get("Referral Note") or "Referred via portal.")
            orig_file = str(row.get("Original CV Filename") or "resume.pdf")
            sp_url = str(row.get("SharePoint CV URL") or "")

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
                stored_filename=orig_file,
                sharepoint_file_url=sp_url,
                referral_note=note,
                candidate_consent=True,
            )
            db.merge(ref)

        db.commit()
        logger.info(f"Loaded {len(data.get('Referrals', []))} referrals from Microsoft Excel into runtime engine.")
