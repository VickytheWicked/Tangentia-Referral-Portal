#!/usr/bin/env python3
"""
Populate and test CV Intelligence & HR Suggestions using ALL CVs from resumes/ folder.
1. Purges all existing referrals from Main DB, Excel, Mock SharePoint, and CV Intelligence DB.
2. Ingests all 29 CVs from resumes/ into Mock SharePoint, SQLite, and Excel.
3. Executes CV Intelligence extraction (profile, education, skills, criteria).
4. Generates match evaluations and HR suggestion rankings.
5. Persists cv_intelligence.db to Azure Blob Storage if enabled.
6. Exports a detailed report.
"""

import os
import sys
import uuid
import shutil
import asyncio
from datetime import datetime, timezone
import openpyxl

# Add backend directory to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.models.referral import Referral, ReferralStatus
from app.models.status_history import ReferralStatusHistory
from app.models.hr_note import HRNote
from app.models.job_position import JobPosition
from app.models.user import User, UserRole
from app.services.excel.local_excel_service import LocalExcelService
from app.services.sharepoint.mock_service import MockSharePointService
from app.cv_intelligence.database import cv_engine, CVBase, CVSessionLocal
from app.cv_intelligence.models import CandidateProfile, JobMatch
from app.cv_intelligence.service import CVIntelligenceService
from app.cv_intelligence.text_extractor import extract_cv_text
from app.cv_intelligence.extractor import get_cv_extractor, heuristic_cv_extract, is_valid_human_name
from app.cv_intelligence.blob_sync import upload_cv_db_to_blob, is_cv_blob_sync_enabled

CV_DIR = os.path.join(WORKSPACE_ROOT, "resumes")

# 29 CV metadata mapping corresponding to all files in resumes/
RESUMES_METADATA = [
    {
        "file": "APA Developer.docx",
        "candidate_name": "Jassim Shaji",
        "candidate_email": "jassim.shaji@example.com",
        "candidate_phone": "+91 98471 23456",
        "position_id": "cats-16855743",
        "years": 3.0,
        "relationship": "Former Colleague",
        "note": "Experienced RPA & Automation Anywhere developer with strong hands-on APA and bot deployment track record.",
    },
    {
        "file": "APA Developer.pdf",
        "candidate_name": "Keerthi K",
        "candidate_email": "keerthikrishnan3778@gmail.com",
        "candidate_phone": "+91 75109 63778",
        "position_id": "cats-16855744",
        "years": 4.0,
        "relationship": "Industry Peer",
        "note": "Expert in Automation Anywhere A360, UiPath, and Intelligent Document Processing.",
    },
    {
        "file": "Business Analyst -2.pdf",
        "candidate_name": "Vinayak Chari",
        "candidate_email": "vinayakrchari@gmail.com",
        "candidate_phone": "+91 82088 53944",
        "position_id": "cats-16699887",
        "years": 11.0,
        "relationship": "Former Colleague",
        "note": "Senior Business Analyst with extensive experience in requirements elicitation, BRDs, and agile delivery.",
    },
    {
        "file": "Business Analyst.pdf",
        "candidate_name": "Ruchita Elekar",
        "candidate_email": "ruchitaelekar05@gmail.com",
        "candidate_phone": "+91 99231 19494",
        "position_id": "cats-16699887",
        "years": 8.0,
        "relationship": "College Alumni",
        "note": "Proven track record in business process analysis, functional specifications, and stakeholder management.",
    },
    {
        "file": "Change Management - 1.docx",
        "candidate_name": "Owen Farmer",
        "candidate_email": "44owenfarmer@gmail.com",
        "candidate_phone": "416-806-5930",
        "position_id": "cats-16699887",
        "years": 11.0,
        "relationship": "Professional Network",
        "note": "Seasoned Change Management and Organizational Transformation specialist with enterprise delivery experience.",
    },
    {
        "file": "Cybersecurity Engineer - 1.pdf",
        "candidate_name": "Navaneeth P",
        "candidate_email": "navaneethpra865@gmail.com",
        "candidate_phone": "+91 96568 49601",
        "position_id": "job-005",
        "years": 3.0,
        "relationship": "Former Colleague",
        "note": "Certified IT Infrastructure & Cyber SOC Analyst with hands-on network defense and vulnerability assessment experience.",
    },
    {
        "file": "Cybersecurity Engineer - 2.pdf",
        "candidate_name": "Dev Manishkumar Shah",
        "candidate_email": "devshah.d54@gmail.com",
        "candidate_phone": "437-971-6240",
        "position_id": "job-005",
        "years": 5.0,
        "relationship": "Industry Peer",
        "note": "Cloud Security & DevSecOps Engineer skilled in AWS, Azure security center, and container protection.",
    },
    {
        "file": "Dashboard BI Developer - 1.pdf",
        "candidate_name": "Ashna K",
        "candidate_email": "ashnakottakal@gmail.com",
        "candidate_phone": "+91 62383 00663",
        "position_id": "cats-16856097",
        "years": 2.0,
        "relationship": "College Alumni",
        "note": "Power BI & Tableau developer with strong SQL and ETL pipeline background.",
    },
    {
        "file": "Dashboard BI Developer - 2.pdf",
        "candidate_name": "Akshay Khobragade",
        "candidate_email": "akshay.khobragade102@gmail.com",
        "candidate_phone": "+91 90282 22344",
        "position_id": "cats-16856097",
        "years": 13.0,
        "relationship": "Industry Peer",
        "note": "Senior BI Lead with 13+ years architecting enterprise analytics dashboards and data warehouses.",
    },
    {
        "file": "Data Engineer - 1.pdf",
        "candidate_name": "Roystan Prajwal Dsouza",
        "candidate_email": "roystan0518@gmail.com",
        "candidate_phone": "+91 96064 90428",
        "position_id": "cats-16856097",
        "years": 4.5,
        "relationship": "Former Colleague",
        "note": "Azure Data Engineer experienced in PySpark, Databricks, Azure Data Factory, and CI/CD data pipelines.",
    },
    {
        "file": "Data Engineer -2.pdf",
        "candidate_name": "Purva Ragit",
        "candidate_email": "ragitpurva@gmail.com",
        "candidate_phone": "+91 93256 04402",
        "position_id": "cats-16856097",
        "years": 10.0,
        "relationship": "Professional Network",
        "note": "Lead Data Architect with extensive Databricks, ETL, and cloud data platform expertise.",
    },
    {
        "file": "DevSecOps  Cloud Engineer - 1.pdf",
        "candidate_name": "Ramya Mohan",
        "candidate_email": "ramyamohan301077@gmail.com",
        "candidate_phone": "+1 647 214-0796",
        "position_id": "job-005",
        "years": 6.0,
        "relationship": "Industry Peer",
        "note": "DevSecOps engineer specializing in CI/CD pipeline security, Terraform IaC, and Kubernetes compliance.",
    },
    {
        "file": "DevSecOps  Cloud Engineer - 2.pdf",
        "candidate_name": "Eric McDonald",
        "candidate_email": "eric.d.mcdonald@gmail.com",
        "candidate_phone": "+1 647 570-5379",
        "position_id": "job-005",
        "years": 9.0,
        "relationship": "Former Colleague",
        "note": "Cloud Automation & DevOps leader with deep AWS, Azure, and infrastructure-as-code mastery.",
    },
    {
        "file": "Naukri_AsmitaDamahe[5y_6m] (1).pdf",
        "candidate_name": "Asmita Damahe",
        "candidate_email": "asmitadamahe1998@gmail.com",
        "candidate_phone": "9987815501",
        "position_id": "cats-16849726",
        "years": 5.5,
        "relationship": "Professional Network",
        "note": "Certified MuleSoft Integration Developer with 5+ years delivering secure enterprise API solutions.",
    },
    {
        "file": "Naukri_Hemanth[7y_0m] (1).pdf",
        "candidate_name": "Hemanth Eswararaju",
        "candidate_email": "hemantheswararaju@gmail.com",
        "candidate_phone": "+91 77320 02350",
        "position_id": "cats-16849726",
        "years": 7.0,
        "relationship": "Former Colleague",
        "note": "Senior Integration Architect with 7 years of MuleSoft Anypoint Platform, cloud integration, and RESTful APIs.",
    },
    {
        "file": "Program Director-Resume.pdf",
        "candidate_name": "Ajinkya Birwadkar",
        "candidate_email": "ajinkya.birwadkar@gmail.com",
        "candidate_phone": "+91 77159 06118",
        "position_id": "cats-16793607",
        "years": 14.0,
        "relationship": "Industry Peer",
        "note": "Seasoned Program Director and delivery leader driving multi-million dollar enterprise automation transformations.",
    },
    {
        "file": "Prompt Engineer.docx",
        "candidate_name": "Aryan Verma",
        "candidate_email": "aryan.verma@example.com",
        "candidate_phone": "+91 99345 67890",
        "position_id": "job-002",
        "years": 3.0,
        "relationship": "College Alumni",
        "note": "Junior Prompt Engineer and GenAI specialist working with LangChain, LlamaIndex, and RAG pipelines.",
    },
    {
        "file": "Prompt Engineer2.docx",
        "candidate_name": "Siddharth Mehta",
        "candidate_email": "siddharth.mehta@example.com",
        "candidate_phone": "+91 98220 12345",
        "position_id": "job-002",
        "years": 12.0,
        "relationship": "Former Colleague",
        "note": "Principal Prompt Engineer with deep expertise in LLM system prompt design, fine-tuning, and Agentic workflows.",
    },
    {
        "file": "QA1.pdf",
        "candidate_name": "B Anand",
        "candidate_email": "anandbalakrishnan50@gmail.com",
        "candidate_phone": "+91 88488 56050",
        "position_id": "cats-16856991",
        "years": 2.0,
        "relationship": "Industry Peer",
        "note": "QA tester specializing in functional, regression, and RPA bot validation.",
    },
    {
        "file": "QA2.pdf",
        "candidate_name": "Abisha Rajesh",
        "candidate_email": "abishadashlin@gmail.com",
        "candidate_phone": "+91 94001 74498",
        "position_id": "cats-16856991",
        "years": 17.0,
        "relationship": "Former Colleague",
        "note": "Senior QA Lead with 17+ years in enterprise testing, manual, APA/AI, and automated test frameworks.",
    },
    {
        "file": "QA3.pdf",
        "candidate_name": "Balaji S",
        "candidate_email": "balajis2998@gmail.com",
        "candidate_phone": "+91 96267 41197",
        "position_id": "cats-16856991",
        "years": 6.0,
        "relationship": "College Alumni",
        "note": "Senior QA Engineer with comprehensive automation testing skills across Selenium, API testing, and CI pipelines.",
    },
    {
        "file": "Scrum_Lead.docx",
        "candidate_name": "Rohit Deshmukh",
        "candidate_email": "rohit.deshmukh@example.com",
        "candidate_phone": "+91 98200 45678",
        "position_id": "cats-16699887",
        "years": 10.0,
        "relationship": "Former Colleague",
        "note": "Agile Scrum Master and delivery coach with certified Scrum Master credentials (CSM) and safe agile governance.",
    },
    {
        "file": "Solution Architect - Lead.docx",
        "candidate_name": "Tariq Mansoor",
        "candidate_email": "tariq.mansoor@example.com",
        "candidate_phone": "+91 98450 78901",
        "position_id": "job-003",
        "years": 9.0,
        "relationship": "Professional Network",
        "note": "Lead Solutions Architect designing scalable enterprise microservices, cloud migrations, and resilient cloud architectures.",
    },
    {
        "file": "Solution Architect.docx",
        "candidate_name": "Mohamed Faheem Ashique",
        "candidate_email": "faheemashique@gmail.com",
        "candidate_phone": "+91 97467 12667",
        "position_id": "job-003",
        "years": 7.0,
        "relationship": "Industry Peer",
        "note": "AI & RPA Solution Architect building multi-agent systems, intelligent workflow automation, and enterprise integrations.",
    },
    {
        "file": "Support1.pdf",
        "candidate_name": "Komal Kutre",
        "candidate_email": "komalkutre2014@gmail.com",
        "candidate_phone": "7040407360",
        "position_id": "cats-16849726",
        "years": 4.0,
        "relationship": "Former Colleague",
        "note": "Senior Technical Support Analyst and RPA operations engineer managing production bot incidents.",
    },
    {
        "file": "Support2.docx",
        "candidate_name": "Allen Manu Philip",
        "candidate_email": "allen.philip@example.com",
        "candidate_phone": "+91 94471 23456",
        "position_id": "cats-16849726",
        "years": 2.0,
        "relationship": "College Alumni",
        "note": "Application support engineer with Automation Anywhere and Microsoft Power Platform troubleshooting skills.",
    },
    {
        "file": "Support3.pdf",
        "candidate_name": "Virendra Salgaonkar",
        "candidate_email": "virendrasalgaonkar777@gmail.com",
        "candidate_phone": "+91 77758 39001",
        "position_id": "cats-16849726",
        "years": 2.0,
        "relationship": "Former Colleague",
        "note": "RPA support developer monitoring bot schedules, exception handling, and credential management.",
    },
    {
        "file": "Tech Lead.docx",
        "candidate_name": "Kunal Sengupta",
        "candidate_email": "kunal.sengupta@example.com",
        "candidate_phone": "+91 98300 11223",
        "position_id": "job-001",
        "years": 10.0,
        "relationship": "Industry Peer",
        "note": "Hands-on Technical Lead with deep experience in Python, FastAPI, distributed systems, and team mentoring.",
    },
    {
        "file": "UI-UX Designer.docx",
        "candidate_name": "Daryl Emmanuel Vaz",
        "candidate_email": "darylemmanuel23@gmail.com",
        "candidate_phone": "+91 70203 77137",
        "position_id": "job-004",
        "years": 4.0,
        "relationship": "Former Colleague",
        "note": "UI/UX Designer and Frontend Specialist creating high-fidelity wireframes, Figma prototypes, and responsive layouts.",
    },
]

REFERRERS = [
    {
        "name": "Priya Sharma",
        "email": "priya.sharma@tangentia.com",
        "phone": "+91 98201 11223",
    },
    {
        "name": "Rahul Verma",
        "email": "rahul.verma@tangentia.com",
        "phone": "+91 98202 22334",
    },
    {
        "name": "Sneha Patil",
        "email": "sneha.patil@tangentia.com",
        "phone": "+91 98203 33445",
    },
    {
        "name": "Vikram Malhotra",
        "email": "vikram.malhotra@tangentia.com",
        "phone": "+91 98204 44556",
    },
    {
        "name": "Alex Morgan",
        "email": "dev.user@tangentia.com",
        "phone": "+1 416 555-0199",
    },
]


def purge_all_referrals():
    """Purge all referrals across DB, Excel, Mock SharePoint, and CV Intelligence."""
    print("\n--- 1. Purging All Existing Referral Data ---")

    # A. Clear SQLite Main DB
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        del_notes = db.query(HRNote).delete()
        del_hist = db.query(ReferralStatusHistory).delete()
        del_refs = db.query(Referral).delete()
        db.commit()
        print(f"  [Main DB] Deleted {del_refs} referrals, {del_hist} status history entries, {del_notes} HR notes.")
    except Exception as e:
        db.rollback()
        print(f"  [Main DB] Error clearing tables: {e}")
    finally:
        db.close()

    # B. Clear Excel Workbook
    excel_path = settings.EXCEL_FILE_PATH
    if os.path.exists(excel_path):
        wb = openpyxl.load_workbook(excel_path)
        sheets_to_clear = ["Referrals", "StatusHistory", "HRNotes", "HiredHistory"]
        for sheet_name in sheets_to_clear:
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                if ws.max_row > 1:
                    deleted_rows = ws.max_row - 1
                    ws.delete_rows(2, deleted_rows)
                    print(f"  [Excel] Cleared {deleted_rows} data rows in sheet '{sheet_name}'")
        wb.save(excel_path)
        wb.close()
        print(f"  [Excel] Saved clean workbook: {excel_path}")

    # C. Clear mock SharePoint storage files
    sp_dir = settings.LOCAL_STORAGE_DIR
    current_year = str(datetime.now(timezone.utc).year)
    year_dir = os.path.join(sp_dir, current_year)
    if os.path.exists(year_dir):
        shutil.rmtree(year_dir)
        os.makedirs(year_dir, exist_ok=True)
        print(f"  [SharePoint Mock] Cleared files in {year_dir}")

    # Reset _index.json
    index_file = os.path.join(sp_dir, "_index.json")
    with open(index_file, "w") as f:
        f.write("{}")
    print("  [SharePoint Mock] Reset _index.json")

    # D. Clear CV Intelligence DB
    cv_db_path = settings.CV_INTELLIGENCE_DB_PATH
    if os.path.exists(cv_db_path):
        cv_db = CVSessionLocal()
        try:
            del_matches = cv_db.query(JobMatch).delete()
            del_profiles = cv_db.query(CandidateProfile).delete()
            cv_db.commit()
            print(f"  [CV Intelligence DB] Deleted {del_profiles} candidate profiles and {del_matches} job matches.")
        except Exception as e:
            cv_db.rollback()
            print(f"  [CV Intelligence DB] Error clearing tables: {e}")
        finally:
            cv_db.close()


async def ingest_resumes_folder_cvs():
    """Ingest all 29 CVs from resumes/ into the portal."""
    print(f"\n--- 2. Ingesting {len(RESUMES_METADATA)} CVs from {CV_DIR} ---")

    Base.metadata.create_all(bind=engine)
    from app.cv_intelligence.database import init_cv_db
    init_cv_db()

    excel_svc = LocalExcelService()
    sp_svc = MockSharePointService()

    db = SessionLocal()
    cv_db = CVSessionLocal()

    # Sync positions from Excel
    from app.services.excel.sync import initialize_and_sync_excel
    initialize_and_sync_excel(db, excel_svc)

    positions = {p.id: p for p in db.query(JobPosition).all()}
    print(f"  Loaded {len(positions)} active job positions from database.")

    statuses = [
        ReferralStatus.SUBMITTED.value,
        ReferralStatus.UNDER_REVIEW.value,
        ReferralStatus.SHORTLISTED.value,
        ReferralStatus.INTERVIEW.value,
    ]

    current_year = datetime.now(timezone.utc).year
    extractor = get_cv_extractor()

    ingested = []

    for idx, item in enumerate(RESUMES_METADATA, 1):
        filename = item["file"]
        file_path = os.path.join(CV_DIR, filename)
        if not os.path.exists(file_path):
            print(f"  [WARN] File not found: {file_path}")
            continue

        with open(file_path, "rb") as f:
            cv_bytes = f.read()

        # 1. Test CV text extraction
        cv_text = extract_cv_text(file_bytes=cv_bytes, filename=filename)

        # 2. Extract structured profile
        try:
            extracted = extractor.extract(cv_text)
        except Exception:
            extracted = heuristic_cv_extract(cv_text)

        cand_name = extracted.candidate_name
        if not cand_name or not is_valid_human_name(cand_name):
            cand_name = item["candidate_name"]

        cand_email = extracted.email or item["candidate_email"]
        cand_phone = extracted.phone or item["candidate_phone"]
        cand_years = extracted.years_of_experience if (extracted.years_of_experience and extracted.years_of_experience > 0) else item["years"]

        pos_id = item["position_id"]
        position = positions.get(pos_id)
        if not position:
            position = list(positions.values())[0]

        referrer = REFERRERS[idx % len(REFERRERS)]
        referral_number = f"REF-{current_year}-{idx:06d}"

        from app.utils.security import generate_sharepoint_filename
        stored_filename = generate_sharepoint_filename(
            referral_number=referral_number,
            candidate_name=cand_name,
            position_title=position.title,
            original_filename=filename,
        )

        # Save to mock SharePoint
        sp_result = await sp_svc.upload_cv(
            file_bytes=cv_bytes,
            filename=stored_filename,
            referral_number=referral_number,
        )

        ref_status = statuses[idx % len(statuses)]
        ref_id = str(uuid.uuid4())

        referral = Referral(
            id=ref_id,
            referral_number=referral_number,
            candidate_name=cand_name,
            candidate_email=cand_email,
            candidate_phone=cand_phone,
            years_of_experience=cand_years,
            relationship=item["relationship"],
            referral_note=item["note"],
            position_id=position.id,
            referred_by_user_id="dev-user-001",
            referred_by_name=referrer["name"],
            referred_by_email=referrer["email"],
            referred_by_phone=referrer["phone"],
            status=ref_status,
            sharepoint_drive_id=sp_result.drive_id,
            sharepoint_item_id=sp_result.item_id,
            sharepoint_file_id=sp_result.file_id,
            sharepoint_file_url=sp_result.web_url,
            original_filename=filename,
            stored_filename=stored_filename,
            candidate_consent=True,
        )
        db.add(referral)

        # Status History
        hist = ReferralStatusHistory(
            referral_id=referral.id,
            old_status=None,
            new_status=ref_status,
            changed_by_user_id="dev-user-001",
            comment=f"Referral submitted by {referrer['name']} ({referrer['email']}).",
        )
        db.add(hist)

        # HR Note
        hr_note = HRNote(
            referral_id=referral.id,
            created_by_user_id="dev-user-001",
            note=f"Candidate resume evaluated. Matched for {position.title}. Candidate phone: {cand_phone}.",
        )
        db.add(hr_note)

        db.commit()
        db.refresh(referral)

        # Write-through to Excel
        excel_svc.append_referral({
            "id": referral.id,
            "referral_number": referral.referral_number,
            "candidate_name": referral.candidate_name,
            "candidate_email": referral.candidate_email,
            "candidate_phone": referral.candidate_phone,
            "referred_by_name": referral.referred_by_name,
            "referred_by_email": referral.referred_by_email,
            "years_of_experience": referral.years_of_experience,
            "relationship": referral.relationship,
            "position_title": position.title,
            "position_id": position.id,
            "referred_by_user_id": "dev-user-001",
            "status": referral.status,
            "linkedin_url": "",
            "github_url": "",
            "original_filename": referral.original_filename,
            "sharepoint_file_url": referral.sharepoint_file_url,
            "referral_note": referral.referral_note,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        })

        # Process CV Intelligence
        try:
            profile = await CVIntelligenceService.process_referral_cv(
                db=db,
                cv_db=cv_db,
                referral_id=referral.id,
                force_reprocess=True,
            )
            match = cv_db.query(JobMatch).filter(
                JobMatch.candidate_profile_id == profile.id,
                JobMatch.position_id == position.id,
            ).first()
            m_level = match.match_level if match else "None"
        except Exception as e:
            m_level = f"Failed ({e})"

        print(f"  [{idx:02d}/29] Ingested {filename} -> {cand_name} ({cand_email}) | Match: {m_level}")
        ingested.append({
            "num": referral_number,
            "name": cand_name,
            "email": cand_email,
            "job": position.title,
            "status": ref_status,
            "match": m_level,
        })

    db.close()
    cv_db.close()

    # Step 3: Trigger Azure Blob sync if enabled
    if is_cv_blob_sync_enabled():
        print("\n--- 3. Syncing cv_intelligence.db to Azure Blob Storage ---")
        uploaded = upload_cv_db_to_blob()
        print(f"  Azure Blob upload result: {uploaded}")
    else:
        print("\n--- 3. Local SQLite Mode: cv_intelligence.db saved to disk ---")
        print(f"  Path: {settings.CV_INTELLIGENCE_DB_PATH} ({os.path.getsize(settings.CV_INTELLIGENCE_DB_PATH)} bytes)")

    print(f"\nSuccessfully populated {len(ingested)} referrals from resumes/ folder!")
    return ingested


if __name__ == "__main__":
    purge_all_referrals()
    asyncio.run(ingest_resumes_folder_cvs())
