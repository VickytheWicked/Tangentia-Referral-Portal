# Tangentia Employee Referral Portal

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.2+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![AI Engine](https://img.shields.io/badge/AI%20Engine-Gemini%20%7C%20OpenAI-8E44AD.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev/)
[![Microsoft Graph](https://img.shields.io/badge/Microsoft%20Graph-API-0078D4.svg?style=flat&logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/graph/)
[![openpyxl](https://img.shields.io/badge/Excel-openpyxl-217346.svg?style=flat&logo=microsoftexcel&logoColor=white)](https://openpyxl.readthedocs.io/)
[![Azure Blob Storage](https://img.shields.io/badge/Azure-Blob%20Storage-0078D4.svg?style=flat&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/services/storage/blobs/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

A production-ready internal **Employee Referral Portal** engineered for enterprise security, dedicated corporate HR JWT authentication, automated candidate CV document archival into **Azure Blob Storage**, persistent record management via an **Azure Blob Storage Excel Ledger** (`Tangentia_Referrals.xlsx`), **AI-powered CV Intelligence & Resume Matcher**, **Historical Candidate RAG Recommendations**, and automated 6-hour cron synchronization with **Tangentia CATS Careers ATS**.

---

## 📑 Table of Contents

- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Quick Start (Local Development)](#-quick-start-local-development)
- [Configuration Guide (`.env`)](#-configuration-guide-env)
- [AI-Powered CV Intelligence Engine](#-ai-powered-cv-intelligence-engine)
- [Historical Candidate RAG Recommendations](#-historical-candidate-rag-recommendations)
- [Automated CATS ATS Scraper & Cron Scheduler](#-automated-cats-ats-scraper--cron-scheduler)
- [Azure Blob Storage & HR Auth Setup](#-azure-blob-storage--hr-auth-setup)
- [API Reference](#-api-reference)
- [Production Deployment (Docker)](#-production-deployment-docker)
- [Security & Compliance Highlights](#-security--compliance-highlights)
- [Running Automated Tests](#-running-automated-tests)
- [Maintainer](#-maintainer)

---

## 🏛 System Architecture

```text
                           ┌─────────────────────────────────────────┐
                           │      Frontend (React 19 + TypeScript)   │
                           │   - Vite SPA + Enterprise Dark UI       │
                           │   - AuthContext Portal JWT Auth         │
                           │   - Zero-Friction Employee Submission   │
                           │   - Live CV Auto-Fill & AI Fit Radar    │
                           │   - Candidate Intelligence & RAG UI     │
                           └────────────────────┬────────────────────┘
                                                │ HTTPS / Bearer JWT
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │      Backend API (FastAPI + Python)     │
                           │   - PBKDF2 + JWT Token Authentication   │
                           │   - Role-Based Access Control (RBAC)    │
                           │   - Pre-Submission Duplicate Engine     │
                           │   - CV Intelligence Queue Worker        │
                           │   - CATS ATS Background Cron Scheduler  │
                           └──────┬──────────────────┬───────────────┘
                                  │                  │
            Azure Blob Storage SDK│                  │ BlobExcelService (openpyxl)
            (or Local Mock Disk)  │                  │ Write-Through Sync to Blob
                                  ▼                  ▼
               ┌───────────────────────────┐ ┌───────────────────────────┐
               │ Azure Blob Storage (CVs)  │ │ Azure Blob Storage (Data) │
               │ - referral-cvs/{YEAR}/    │ │ - referral-data/          │
               │ - Zero DB BLOB Storage    │ │ - Tangentia_Referrals.xlsx│
               │ - Secure CV Proxy Stream  │ │ - 6-Sheet Audit Ledger    │
               └───────────────────────────┘ └─────────────┬─────────────┘
                                                           │
                                                           ▼
               ┌─────────────────────────────────────────────────────────┐
               │            AI Intelligence & Data Engine               │
               │  - LLM Requirement Analyzer (Gemini / Azure OpenAI)     │
               │  - JEV Candidate-Job Relevance Scoring Engine           │
               │  - Isolated CV Intelligence SQLite (`cv_intelligence.db`) │
               │  - Historical Candidate RAG Database (`historical_rag.db`)│
               │  - Azure Blob Storage Persist & Sync (`referral-data`)  │
               └─────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 👤 Employee Experience
- **Instant Dashboard Landing**: Direct zero-friction access to candidate referral statistics (*Total*, *In Review*, *Interviewing*, *Hired*) and recent referral updates.
- **AI-Powered CV Auto-Fill**: Uploading a CV (`.pdf` / `.docx`) automatically extracts candidate name, email, phone, experience, summary, and skills to populate the submission form in seconds.
- **Submit Candidate Referrals**: Streamlined submission workflow including target requisition, experience, candidate contact, relationship, and corporate email verification.
- **Drag-and-Drop CV Uploader**: Validates `.pdf` and `.docx` files with client-side & server-side magic-byte inspection, text extraction, and 10MB size capping.
- **Real-Time Duplicate Warning Modal**: Instant pre-submission alerts matching candidate email, normalized phone, or candidate name + target position within a configurable 6-month (180-day) window.
- **Referral Portfolio (`My Referrals`)**: Filterable data table with live status badges, secure CV streaming download, and themed **Referral Withdrawal Modal** (with optional withdrawal rationale).
- **Client Telemetry & Viewport Stability**: Dual-layer client runtime infrastructure combining release verification (`systemMeta.ts`) with active DOM layout monitoring (`viewportObserver.ts`) ensuring persistent viewport status indicators and responsive layout stability across SPA route transitions.

### 🛡️ HR Administrator Hub
- **Executive Hiring Pipeline Overview**: Real-time conversion funnel metrics, departmental statistics, and top referrer leaderboards.
- **Enterprise Candidate Database**: Multi-dimensional filtering by status, department, position, search query, and submission date.
- **Candidate Intelligence Dossier**: Deep AI candidate analysis modal showing job-fit match scores (0–100%), skill breakdown matrix, experience alignment, candidate key strengths, potential gaps, and suggested interview questions.
- **Candidate Profile Reviewer**: Full candidate history, direct secure CV stream, status progression manager (`Submitted` → `Under Review` → `Shortlisted` → `Interview` → `Selected` → `Hired` / `Rejected`), and complete status audit timeline.
- **Confidential Internal HR Notes**: Private recruiter evaluations thread, completely isolated and hidden from regular employees.
- **Historical Candidate AI Suggestions (RAG)**: AI-driven matching engine that analyzes past archived/referred candidates to surface passive talent for new job requisitions.
- **Requisition Manager & AI Requirement Analyzer**: Create and manage job postings with automated LLM requirement extraction that breaks job descriptions down into key technical skills, experience criteria, and domain qualifications.
- **Permanent Candidate Deletion**: Complete candidate purge with cascade deletion from active database, internal notes, CV intelligence cache, and Microsoft Excel storage.
- **Hired History Excel Export**: Dedicated export functionality to download styled Microsoft Excel spreadsheets of all hired candidate referrals.

### 🤖 AI CV Intelligence & JEV Relevance Engine
- **Automated Resume Extraction**: Multi-stage parsing pipeline supporting `pdfplumber`, `PyMuPDF (fitz)`, `docx2txt`, and fallback regex parsers.
- **Structured Requirement Extraction**: LLM-driven analyzer distills raw job descriptions into structured JSON requirements (*Core Skills*, *Experience Range*, *Domain Knowledge*, *Education Requirements*, *Nice-to-haves*).
- **Job-Candidate Fit (JEV) Relevance Scoring**: Calculates multi-vector fit scores incorporating skill overlap, years of experience, role alignment, strengths, gaps, and custom technical interview questions.
- **Asynchronous Queue Worker**: Background process (`cv_intelligence/queue.py`) automatically ingests, extracts, and scores newly uploaded CVs without slowing down UI request threads.
- **Azure Blob Persistence**: Optional synchronization adapter (`blob_sync.py`) to backup and restore `cv_intelligence.db` to Azure Blob Storage on application startup and shutdown.

### 🔄 Automated CATS ATS Web Scraper & Background Cron Scheduler
- **Live Requisition Ingestion**: Connects directly to the live [Tangentia CATS Careers Portal](https://tangentia.catsone.com/careers/9463-General) to scrape all active corporate postings across India, the US, and Canada.
- **Automated Background Scheduler**: Built-in cron scheduler (`cats_scheduler.py`) that runs every 6 hours to keep the internal job catalog synchronized with CATS ATS automatically.
- **Intelligent 1–2 Liner Summarizer**: Cleans raw HTML, strips boilerplate headers, styles, and scripts, distilling comprehensive job descriptions into crisp 1–2 sentence summaries.
- **Automated Taxonomy Categorization**: Accurately maps postings into corporate departments (*Intelligent Automation*, *Cloud & Integration*, *Data & Analytics*, *Finance & Enterprise*, *Global Sales*, *Project & Product Management*, *Engineering*) and employment types (*Full-time*, *Contract*, *Internship*).
- **Idempotent Dual-Storage Persistence**: Scraped positions use deterministic IDs (`cats-{id}`) preventing duplicate entries. Every sync immediately writes through to `Tangentia_Referrals.xlsx` and the runtime database.
- **One-Click HR ATS Sync Button & ATS Badges**: HR Admins can manually click **"Sync CATS ATS"** from the Job Openings page; synced roles carry a distinct **`CATS ATS`** badge.

### 📊 Multi-Sheet Microsoft Excel Ledger in Azure Blob Storage
- **Permanent Audit-Ready Ledger**: Every referral submission, status transition, and confidential HR note is automatically written through to `Tangentia_Referrals.xlsx`, persisted directly in Azure Blob Storage via `BlobExcelService`.
- **Multi-Sheet Structured Worksheets**:
  - `Referrals`: Comprehensive candidate information, submission timestamps, contact details, and CV storage pointers.
  - `JobPositions`: Requisitions, departments, locations, employment types, and active statuses.
  - `StatusHistory`: Full audit trail recording who changed what status, when, and rationale notes.
  - `HRNotes`: Internal evaluations tagged with author and timestamps.
  - `Users`: Internal user accounts and roles.
  - `HiredHistory`: Permanent record of hired candidates.
- **Instant One-Click Export**: HR Admins can download the full, styled Microsoft Excel workbook directly from the dashboard at any time.
- **Deployment Modes**: Seamlessly uses Azure Blob Storage persistence (`EXCEL_STORAGE_TYPE=blob`) in cloud environments or isolated local `.xlsx` file (`EXCEL_STORAGE_TYPE=mock`) for offline development.

### ☁️ Cloud & Enterprise Security
- **Corporate HR Authentication**: Secure PBKDF2-HMAC-SHA256 password verification and signed JWT sessions (`/api/auth/login`) for HR administrators, with frictionless submission for regular employees.
- **Azure Blob Storage / Secure Document Repository**: Resumes are archived directly into cloud blob storage (or local offline mock storage in dev mode) with year partitioning (`referral-cvs/{YEAR}/{filename}`).
- **Zero-Orphan Transaction Rollback**: If a database commit fails after a CV upload, the uploaded file in blob storage is automatically removed via `delete_cv` to eliminate orphaned files.
- **Zero-Trust Proxied Streaming**: Cloud storage connection strings and raw blob URLs are never exposed to client browsers; CV downloads are securely proxied through authenticated backend streams.

---

## 🛠 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, python-jose (JWT), passlib/hashlib, HTTPX, APScheduler |
| **AI & NLP** | Google Gemini API / Azure OpenAI, `pdfplumber`, `fitz (PyMuPDF)`, `docx2txt`, Scikit-Learn |
| **Frontend** | React 19, TypeScript 5, Vite 8, Lucide Icons, Vanilla CSS Enterprise Theme, React AuthContext |
| **Storage & Ledger** | SQLite / PostgreSQL 16, Excel Ledger (`openpyxl` via `BlobExcelService`), Azure Blob Storage (`referral-cvs` & `referral-data`) |
| **Infrastructure** | Azure App Service, Azure Static Web Apps, Azure Blob Storage, Docker |

---

## 📂 Repository Structure

```text
Tangentia-Referral-Portal/
├── backend/
│   ├── alembic_migrations/         # Database migration revisions
│   ├── app/
│   │   ├── api/                    # FastAPI routers (auth, jobs, referrals, hr, analytics, cv_intelligence, historical_suggestions)
│   │   ├── cv_intelligence/        # AI CV Intelligence & JEV Relevance engine
│   │   │   ├── blob_sync.py        # Azure Blob persistence for CV database
│   │   │   ├── database.py         # SQLite database schema for CV intelligence
│   │   │   ├── extractor.py        # Multi-stage CV text & metadata extraction
│   │   │   ├── jev_relevance.py    # Job-candidate relevance scoring engine
│   │   │   ├── matcher.py          # LLM skill & fit evaluation matcher
│   │   │   ├── queue.py            # Async background CV processing worker queue
│   │   │   ├── requirement_analyzer.py # Job requisition LLM requirement parser
│   │   │   └── service.py          # CV Intelligence orchestration service
│   │   ├── historical_suggestions/ # Historical candidate RAG recommendation service
│   │   │   ├── api.py              # Historical suggestions API endpoints
│   │   │   ├── matcher.py          # Vector/keyword match engine for candidate pool
│   │   │   └── rag_service.py      # RAG index and similarity query service
│   │   ├── models/                 # SQLAlchemy ORM database models
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   ├── services/
│   │   │   ├── excel/              # Excel ledger (Azure Blob Storage & local) sync services
│   │   │   ├── storage/            # Cloud Azure Blob & Local mock document storage adapters
│   │   │   ├── cats_scraper.py     # CATS Careers ATS web scraper & 1-2 liner engine
│   │   │   ├── cats_scheduler.py   # 6-hour background cron scheduler for ATS sync
│   │   │   ├── auth_service.py     # Corporate HR JWT authentication & PBKDF2 hashing
│   │   │   └── referral_service.py # Core business logic & duplicate detection engine
│   │   ├── utils/                  # Document validation & security sanitization
│   │   ├── config.py               # Pydantic settings & environment management
│   │   ├── database.py             # Main SQLAlchemy engine & session factory
│   │   └── main.py                 # FastAPI application entry point & lifecycle hooks
│   ├── data/                       # Local Excel workbook (`Tangentia_Referrals.xlsx`) & SQLite DBs
│   ├── storage/mock_storage/       # Local offline document library mock
│   ├── tests/                      # Pytest integration & role authorization test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                     # Database seeder with sample positions & candidates
├── frontend/
│   ├── src/
│   │   ├── auth/                   # MSAL authentication config & React AuthContext
│   │   ├── components/
│   │   │   ├── common/             # UI elements (Modals, Badges, Tabs, Search)
│   │   │   ├── employee/           # Referral Form, CV Extractor Auto-Fill, My Referrals Table
│   │   │   ├── hr/                 # CandidateIntelligenceModal, AIRequirementAnalysisSection, HistoricalCandidateDetailModal
│   │   │   └── layout/             # Top Navigation, Sidebar, Role Switcher
│   │   ├── pages/
│   │   │   ├── employee/           # Dashboard, Submit Referral, My Referrals
│   │   │   └── hr/                 # HR Dashboard, Candidate Database, Job Openings, HR Suggestions, Analytics
│   │   ├── services/api.ts         # Centralized REST API client & dev token injector
│   │   ├── types/                  # TypeScript data interfaces & AI types
│   │   ├── utils/
│   │   │   ├── systemMeta.ts       # Client runtime telemetry, release integrity & header status triggers
│   │   │   └── viewportObserver.ts # Viewport anchor observer & floating status badge guardian
│   │   └── index.css               # Curated enterprise dark theme design system
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml              # Multi-container production compose file
└── README.md
```

---

## 🚀 Quick Start (Local Development)

The repository includes an isolated **Development Mode** (`DEV_MODE=True`, `EXCEL_STORAGE_TYPE=mock`, `STORAGE_TYPE=mock`) allowing instant local execution without needing live Azure tenant credentials or cloud infrastructure.

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** and **npm 10+**

### 1. Clone & Configure
```bash
git clone https://github.com/VickytheWicked/Tangentia-Referral-Portal.git
cd Tangentia-Referral-Portal

# Copy environment configuration templates
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 2. Start the Backend API
```bash
cd backend

# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the backend API server (automatically seeds Excel & database on first launch)
uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 3. Start the Frontend Web Portal
Open a **new terminal tab**:
```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- **Web Portal**: [http://localhost:5173](http://localhost:5173)

---

## ⚙️ Configuration Guide (`.env`)

### `backend/.env`
```env
# Application Settings
PROJECT_NAME="Tangentia Employee Referral Portal"
ENVIRONMENT=development
DEBUG=True
DEV_MODE=True  # Set to False in production to enforce strict JWT authentication

# Database Settings
DATABASE_URL=sqlite:///:memory:
# DATABASE_URL=postgresql://postgres:password@localhost:5432/referral_portal

# Excel Storage (Azure Blob Storage or Local)
# Set to 'blob' for Azure Blob Storage ledger; 'mock' for local development .xlsx file
EXCEL_STORAGE_TYPE=blob
EXCEL_WORKBOOK_NAME=Tangentia_Referrals.xlsx

# Authentication (Portal JWT & PBKDF2 Password Hashing)
JWT_SECRET_KEY=your-secure-jwt-signing-secret

# Document & CV Storage (Azure Blob Storage / Local Mock)
# Set to 'blob' for Azure Blob Storage; 'mock' for local offline development
STORAGE_TYPE=mock
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
BLOB_CV_CONTAINER=referral-cvs
BLOB_DATA_CONTAINER=referral-data

# AI CV Intelligence & HR Suggestions Engine
CV_INTELLIGENCE_ENABLED=True
CV_LLM_PROVIDER=gemini  # gemini | azure | openai | anthropic
CV_LLM_MODEL=gemini-3.5-flash-lite
GEMINI_API_KEY=your-gemini-api-key
CV_STORAGE_TYPE=local  # local | blob
BLOB_CV_INTELLIGENCE_NAME=cv_intelligence.db

# JEV Relevance Check (Optional pre-screen)
CV_RELEVANCE_CHECK_ENABLED=False
CV_RELEVANCE_BLOCK_ENABLED=False
CV_RELEVANCE_BLOCK_THRESHOLD=0.30

# Historical Candidate RAG Recommendations
HISTORICAL_REFERRAL_SEARCH_ENABLED=True
HISTORICAL_MATCH_THRESHOLD=0.45

# Duplicate Detection Window (6 Months / 180 Days)
REFERRAL_DUPLICATE_WINDOW_DAYS=180
```

### `frontend/.env`
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_AZURE_CLIENT_ID=your-azure-client-id
VITE_AZURE_TENANT_ID=your-azure-tenant-id
```

---

## 🤖 AI-Powered CV Intelligence Engine

The CV Intelligence Engine provides automated resume extraction, job requirement analysis, candidate-to-job matching, and intelligent scoring.

```text
 Candidate CV (.pdf / .docx)
             │
             ▼
  ┌──────────────────────┐
  │ CV Text Extractor    │ ── (pdfplumber / PyMuPDF / docx2txt)
  └──────────┬───────────┘
             ▼
  ┌──────────────────────┐
  │ LLM Matcher & JEV    │ ◄── Job Requisition Requirements
  │ Scoring Engine       │     (Parsed by Requirement Analyzer)
  └──────────┬───────────┘
             ▼
  ┌──────────────────────┐
  │ Candidate Dossier    │ ── Fit Score %, Skill Match, Strengths,
  │ & HR Dashboard       │    Gaps, & Custom Interview Questions
  └──────────────────────┘
```

1. **Auto-Fill Resume Ingestion**: When submitting a referral, employees can click **"Auto-fill from CV"**. The API (`POST /api/referrals/extract-cv`) extracts key candidate fields in real time to pre-fill the form.
2. **Requisition Requirement Analysis**: When a job requisition is created or updated, the requirement analyzer parses the description into structured criteria (*Skills*, *Experience Range*, *Domain Alignment*, *Certifications*).
3. **Async Queue Worker**: Newly uploaded CVs enter the background worker queue (`cv_intelligence/queue.py`) for automated background extraction and scoring without blocking user operations.
4. **Candidate Dossier Modal**: HR Admins can view complete candidate fit breakdowns directly from the candidate table by clicking **"AI Fit Profile"**.

---

## 🔍 Historical Candidate RAG Recommendations

The Historical Candidate Suggestions feature surfaces passive talent from prior referral submissions when a new job requisition opens.

- **Vector & Keyword Matching**: Scans historical candidate profiles and past CV extractions stored in `historical_rag.db`.
- **Match Threshold Filter**: Filters candidates based on configurable similarity thresholds (`HISTORICAL_MATCH_THRESHOLD=0.45`).
- **HR Tab**: HR Admins can access the **"HR Suggestions"** page in the portal to review recommended passive candidates for active job openings.

---

## 🔄 Automated CATS ATS Scraper & Cron Scheduler

The portal synchronizes corporate job openings with Tangentia's official public ATS portal ([`https://tangentia.catsone.com/careers/9463-General`](https://tangentia.catsone.com/careers/9463-General)).

### Background Cron Scheduler
- Runs automatically in the background every **6 hours** (`cats_scheduler.py`).
- Crawls active postings, generates 1–2 sentence job summaries, categorizes departments/types, and updates the database & Excel workbook.

### Manual Synchronization Options
1. **HR Portal Button**: Click **"Sync CATS ATS"** in the **Job Openings** tab.
2. **REST API Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/jobs/sync-cats \
     -H "Authorization: Bearer dev-hr-token"
   ```
3. **Python CLI Command**:
   ```bash
   PYTHONPATH=. .venv/bin/python -c "
   from app.database import SessionLocal, Base, engine
   from app.services.cats_scraper import sync_cats_jobs_with_db
   Base.metadata.create_all(bind=engine)
   db = SessionLocal()
   print(sync_cats_jobs_with_db(db)['message'])
   db.close()
   "
   ```

---

## 🔐 Azure Blob Storage & HR Auth Setup

### 1. Configure Azure Blob Storage
1. In the **[Azure Portal](https://portal.azure.com)**, navigate to your Azure Storage Account.
2. Under **Data storage** > **Containers**, create two containers:
   - `referral-cvs` (for candidate resumes)
   - `referral-data` (for `Tangentia_Referrals.xlsx` and `cv_intelligence.db`)
3. Under **Security + networking** > **Access keys**, copy the **Connection string** and set `AZURE_STORAGE_CONNECTION_STRING`.
4. Set:
   - `STORAGE_TYPE=blob`
   - `EXCEL_STORAGE_TYPE=blob`
   - `CV_STORAGE_TYPE=azure`
5. The portal will automatically populate and maintain `Tangentia_Referrals.xlsx` inside the `referral-data` blob container on every operation via `BlobExcelService`.

### 2. Corporate HR Authentication
1. HR Administrator accounts and credentials are securely maintained in the `Users` sheet of `Tangentia_Referrals.xlsx` and synchronized into the database.
2. Login is performed via `/api/auth/login` using `@tangentia.com` email and password.
3. Passwords are salted and hashed using PBKDF2-HMAC-SHA256, and authenticated sessions are granted cryptographically signed JWT bearer tokens (`JWT_SECRET_KEY`).
4. Regular employees submit candidate referrals with zero login friction (no sign-in required).

---

## 📡 API Reference

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/auth/config` | Public | Returns auth domain configuration & dev status |
| `GET` | `/api/auth/me` | Authenticated | Current user profile and security roles |
| `GET` | `/api/jobs` | Authenticated | List active/inactive job requisitions |
| `POST`| `/api/jobs` | HR Admin | Create a new job requisition |
| `PUT` | `/api/jobs/{id}` | HR Admin | Update requisition details or active status |
| `POST`| `/api/jobs/sync-cats` | HR Admin | Manually trigger CATS ATS web scraper sync |
| `GET` | `/api/jobs/sync-cats/preview` | HR Admin | Preview live open jobs from CATS ATS |
| `POST`| `/api/referrals/check-duplicate` | Employee | Pre-submission duplicate candidate detection |
| `POST`| `/api/referrals/extract-cv` | Employee | Auto-fill extraction from candidate CV file |
| `POST`| `/api/referrals` | Employee | Submit candidate referral with CV document |
| `GET` | `/api/referrals` | Employee | List current employee's submitted referrals |
| `GET` | `/api/referrals/hired-history` | Employee / HR | List hired candidate referral history |
| `GET` | `/api/referrals/hired-history/excel-export` | Employee / HR | Download Hired Referral History Excel sheet |
| `GET` | `/api/referrals/{id}` | Employee / HR | Retrieve candidate referral details |
| `GET` | `/api/referrals/{id}/cv` | Employee / HR | Authenticated proxy download of candidate CV |
| `PUT` | `/api/referrals/{id}/withdraw` | Referrer | Withdraw candidate referral from review |
| `GET` | `/api/hr/referrals` | HR Admin | Full candidate referral database with filters |
| `PUT` | `/api/hr/referrals/{id}/status` | HR Admin | Update candidate referral status & write audit log |
| `DELETE`| `/api/hr/referrals/{id}` | HR Admin | Permanently delete referral from DB and Excel |
| `GET` | `/api/hr/referrals/{id}/notes` | HR Admin | Retrieve confidential internal HR notes |
| `POST`| `/api/hr/referrals/{id}/notes` | HR Admin | Add confidential internal HR note |
| `GET` | `/api/hr/referrals/excel-export` | HR Admin | Download full Microsoft Excel workbook (`.xlsx`) |
| `GET` | `/api/hr/analytics` | HR Admin | Conversion funnel, department metrics, top referrers |
| `GET` | `/api/cv-intelligence/status` | HR Admin | Returns CV Intelligence system & queue status |
| `GET` | `/api/cv-intelligence/suggestions` | HR Admin | Get AI suggestions across active job requisitions |
| `GET` | `/api/cv-intelligence/candidates/{id}`| HR Admin | Get deep AI Candidate Intelligence dossier |
| `POST`| `/api/cv-intelligence/process/{id}` | HR Admin | Manually trigger AI extraction/scoring for a CV |
| `GET` | `/api/historical-suggestions/positions/{id}`| HR Admin | Get passive historical candidate suggestions for job |

---

## 🐳 Production Deployment (Docker)

Deploy the full production stack (FastAPI backend + PostgreSQL 16 + Nginx frontend SPA) using Docker Compose:

```bash
# 1. Start containers in detached mode
docker-compose up -d --build

# 2. Apply database migrations
docker-compose exec backend alembic upgrade head
```

- **Web Portal**: `http://<your-server-ip>:3000`
- **Backend API**: `http://<your-server-ip>:8000`
- **PostgreSQL**: Port `5432`

---

## 🛡️ Security & Compliance Highlights

- **Server-Side Token Verification**: Tokens are cryptographically validated server-side using signed JWT tokens with HS256 and PBKDF2-HMAC-SHA256 password security.
- **Strict Role-Based Access Control (RBAC)**: HR endpoints (`/api/hr/*`, `/api/cv-intelligence/*`) enforce strict admin authorization. Regular employees can only view their own referrals.
- **Zero Raw Document Exposure**: Cloud storage credentials and raw blob URLs are never exposed to browsers; all file downloads stream securely through authenticated backend proxies.
- **Magic-Byte & Anti-Traversal Validation**: Uploaded resumes undergo magic-byte signature checking (`%PDF-`, `PK\x03\x04`), 10MB file caps, and path sanitization.
- **Explicit GDPR Candidate Consent**: Mandatory candidate consent tracking recorded on every referral submission.

---

## 🧪 Running Automated Tests

Run the backend test suite:

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

---

Engineered and maintained by **[VickytheWicked](https://github.com/VickytheWicked)**.
