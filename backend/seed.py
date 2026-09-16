import os
from datetime import datetime, timezone
from app.database import SessionLocal, Base, engine
from app.models.user import User, UserRole
from app.models.job_position import JobPosition
from app.models.referral import Referral, ReferralStatus
from app.models.status_history import ReferralStatusHistory
from app.models.hr_note import HRNote
from app.config import settings

# PDF header signature
SAMPLE_PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<<\n/Title (Sample Candidate Resume)\n/Author (Tangentia)\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Seed Users
        hr_user = db.query(User).filter(User.email == "hr.lead@tangentia.com").first()
        if not hr_user:
            hr_user = User(
                entra_user_id="user-dev-hr-001",
                name="Marcus Vance",
                email="hr.lead@tangentia.com",
                password="TangentiaHR@2026",
                role=UserRole.HR_ADMIN.value,
                department="Human Resources",
            )
            db.add(hr_user)

        employee_user = db.query(User).filter(User.email == "employee@tangentia.com").first()
        if not employee_user:
            employee_user = User(
                entra_user_id="entra-user-dev-employee-001",
                name="Sarah Jenkins",
                email="employee@tangentia.com",
                role=UserRole.EMPLOYEE.value,
                department="Cloud Engineering",
            )
            db.add(employee_user)

        db.commit()
        db.refresh(hr_user)
        db.refresh(employee_user)

        # 2. Seed Job Positions
        sample_jobs = [
            {
                "title": "Senior Backend Developer (Python / FastAPI)",
                "department": "Engineering",
                "description": "Looking for an experienced backend developer skilled in Python, FastAPI, PostgreSQL, and cloud distributed architectures.",
                "location": "Toronto, Canada (Hybrid)",
                "employment_type": "Full-time",
            },
            {
                "title": "AI & Machine Learning Engineer",
                "department": "AI Innovations",
                "description": "Responsible for designing and implementing LLM evaluation pipelines, agentic workflows, and semantic search systems.",
                "location": "Goa, India (Remote)",
                "employment_type": "Full-time",
            },
            {
                "title": "Senior Cloud Solutions Architect",
                "department": "Cloud & Infrastructure",
                "description": "Lead enterprise architecture initiatives across Microsoft Azure, AWS, and secure hybrid cloud deployments.",
                "location": "New York, USA",
                "employment_type": "Full-time",
            },
            {
                "title": "Frontend Lead (React + TypeScript)",
                "department": "Engineering",
                "description": "Build high-performance web applications, design systems, and responsive enterprise portals using React 18+ and modern CSS.",
                "location": "Toronto, Canada",
                "employment_type": "Full-time",
            },
            {
                "title": "DevOps & SRE Specialist",
                "department": "Operations",
                "description": "Maintain CI/CD pipelines, Kubernetes clusters, infrastructure-as-code with Terraform, and zero-downtime releases.",
                "location": "Goa, India",
                "employment_type": "Full-time",
            },
        ]

        created_jobs = {}
        for job_data in sample_jobs:
            existing = db.query(JobPosition).filter(JobPosition.title == job_data["title"]).first()
            if not existing:
                job = JobPosition(**job_data, is_active=True)
                db.add(job)
                db.flush()
                created_jobs[job.title] = job
            else:
                created_jobs[existing.title] = existing

        db.commit()

        # 3. Create mock CV files in storage
        year = str(datetime.now(timezone.utc).year)
        mock_dir = os.path.join(settings.LOCAL_STORAGE_DIR, year)
        os.makedirs(mock_dir, exist_ok=True)

        sample_referrals_data = [
            {
                "number": f"REF-{year}-000001",
                "cand_name": "Rahul Sharma",
                "cand_email": "rahul.sharma@example.com",
                "cand_phone": "+14165550192",
                "exp": 6.5,
                "rel": "Former Colleague",
                "note": "Worked with Rahul at FinTech Corp. Brilliant distributed systems knowledge and very proactive team player.",
                "job_title": "Senior Backend Developer (Python / FastAPI)",
                "status": ReferralStatus.INTERVIEW.value,
                "cv_filename": f"REF-{year}-000001_Rahul-Sharma_Senior-Backend-Developer.pdf",
            },
            {
                "number": f"REF-{year}-000002",
                "cand_name": "Ananya Patel",
                "cand_email": "ananya.patel@example.com",
                "cand_phone": "+919820011223",
                "exp": 4.0,
                "rel": "College Alumni",
                "note": "Ananya has published research papers in NLP and built agentic search engines using LangChain and FastAPI.",
                "job_title": "AI & Machine Learning Engineer",
                "status": ReferralStatus.SHORTLISTED.value,
                "cv_filename": f"REF-{year}-000002_Ananya-Patel_AI-Machine-Learning-Engineer.pdf",
            },
            {
                "number": f"REF-{year}-000003",
                "cand_name": "David Chen",
                "cand_email": "david.chen@example.com",
                "cand_phone": "+16475550144",
                "exp": 8.0,
                "rel": "Professional Network",
                "note": "David is a seasoned cloud architect who led multi-region Azure migrations at his previous enterprise employer.",
                "job_title": "Senior Cloud Solutions Architect",
                "status": ReferralStatus.UNDER_REVIEW.value,
                "cv_filename": f"REF-{year}-000003_David-Chen_Senior-Cloud-Solutions-Architect.pdf",
            },
        ]

        for ref_info in sample_referrals_data:
            existing_ref = db.query(Referral).filter(Referral.referral_number == ref_info["number"]).first()
            if not existing_ref and ref_info["job_title"] in created_jobs:
                job = created_jobs[ref_info["job_title"]]
                
                # Write sample PDF to mock sharepoint storage
                file_path = os.path.join(mock_dir, ref_info["cv_filename"])
                with open(file_path, "wb") as fp:
                    fp.write(SAMPLE_PDF_BYTES)

                referral = Referral(
                    referral_number=ref_info["number"],
                    candidate_name=ref_info["cand_name"],
                    candidate_email=ref_info["cand_email"],
                    candidate_phone=ref_info["cand_phone"],
                    years_of_experience=ref_info["exp"],
                    relationship=ref_info["rel"],
                    referral_note=ref_info["note"],
                    position_id=job.id,
                    referred_by_user_id=employee_user.id,
                    referred_by_name=employee_user.name,
                    status=ref_info["status"],
                    sharepoint_drive_id="mock-drive-tangentia-cvs",
                    sharepoint_item_id=f"item-{ref_info['number']}",
                    sharepoint_file_id=f"file-{ref_info['number']}",
                    sharepoint_file_url=f"https://tangentia.sharepoint.com/sites/hr/Referral-CVs/{year}/{ref_info['cv_filename']}",
                    original_filename=f"{ref_info['cand_name'].replace(' ', '_')}_CV.pdf",
                    stored_filename=ref_info["cv_filename"],
                    candidate_consent=True,
                )
                db.add(referral)
                db.flush()

                # Add status history
                h1 = ReferralStatusHistory(
                    referral_id=referral.id,
                    old_status=None,
                    new_status=ReferralStatus.SUBMITTED.value,
                    changed_by_user_id=employee_user.id,
                    comment="Initial referral submission",
                )
                db.add(h1)

                if ref_info["status"] != ReferralStatus.SUBMITTED.value:
                    h2 = ReferralStatusHistory(
                        referral_id=referral.id,
                        old_status=ReferralStatus.SUBMITTED.value,
                        new_status=ref_info["status"],
                        changed_by_user_id=hr_user.id,
                        comment=f"Candidate reviewed and transitioned to {ref_info['status']}",
                    )
                    db.add(h2)

                # Add sample HR note
                note = HRNote(
                    referral_id=referral.id,
                    created_by_user_id=hr_user.id,
                    note=f"Preliminary screening verified. Candidate has required technical background. Scheduled for hiring manager review.",
                )
                db.add(note)

        db.commit()
        print("Database successfully seeded with users, job openings, and sample referrals!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
