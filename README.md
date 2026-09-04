# Tangentia Employee Referral Portal

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-8.2+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev/)
[![Microsoft Graph](https://img.shields.io/badge/Microsoft%20Graph-API-0078D4.svg?style=flat&logo=microsoft&logoColor=white)](https://learn.microsoft.com/en-us/graph/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat)](LICENSE)

A production-ready internal **Employee Referral Portal** engineered for enterprise security, seamless corporate Microsoft Entra ID (Azure AD) authentication, and automated candidate CV document archival into **Microsoft SharePoint Online** document libraries via the **Microsoft Graph API**.

---

## 📑 Table of Contents

- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Quick Start (Local Development)](#-quick-start-local-development)
- [Configuration Guide (`.env`)](#-configuration-guide-env)
- [Microsoft Entra ID & SharePoint Setup](#-microsoft-entra-id--sharepoint-setup)
- [API Reference](#-api-reference)
- [Production Deployment (Docker)](#-production-deployment-docker)
- [Security & Compliance Highlights](#-security--compliance-highlights)
- [Contributing & Maintainers](#-maintainer)

---

## 🏛 System Architecture

```text
                           ┌─────────────────────────────────────────┐
                           │      Frontend (React 19 + TypeScript)   │
                           │   - Vite SPA + Enterprise Dark UI       │
                           │   - MSAL Microsoft Entra ID SSO         │
                           └────────────────────┬────────────────────┘
                                                │ HTTPS / Bearer JWT
                                                ▼
                           ┌─────────────────────────────────────────┐
                           │      Backend API (FastAPI + Python)     │
                           │   - Entra ID JWKS Token Verifier        │
                           │   - Role-Based Access Control (RBAC)    │
                           │   - Duplicate Candidate Engine          │
                           │   - Atomic SharePoint Rollback Manager  │
                           └──────────┬───────────────────┬──────────┘
                                      │                   │
             Microsoft Graph API      │                   │ SQLAlchemy 2.0 ORM
             (OAuth2 Client Creds)    │                   │
                                      ▼                   ▼
                 ┌───────────────────────────┐   ┌───────────────────────────┐
                 │  SharePoint Online Drive  │   │    PostgreSQL / SQLite    │
                 │  - Referral-CVs/{YEAR}/   │   │  - Users & Permissions    │
                 │  - Zero DB BLOB Storage   │   │  - Job Openings Reqs      │
                 │  - Secure CV Proxy Stream │   │  - Referrals & Audit Logs │
                 │                           │   │  - Confidential HR Notes  │
                 └───────────────────────────┘   └───────────────────────────┘
```

---

## ✨ Key Features

### 👤 Employee Experience
- **Instant Dashboard Landing**: Direct zero-friction access to metrics (Total, In Review, Interviewing, Hired) and recent submissions.
- **Submit Candidate Referrals**: Multi-field submission including target requisition, experience, candidate contact, relationship, and recommendation note.
- **Drag-and-Drop CV Uploader**: Validates `.pdf` and `.docx` files with client-side & server-side magic-byte inspection and 10MB size capping.
- **Real-Time Duplicate Warning Modal**: Instant pre-submission alerts matching candidate email, normalized phone, or candidate name + target position.
- **Referral Portfolio (`My Referrals`)**: Filterable data table with candidate status badges, secure CV streaming download, and themed **Referral Withdrawal Modal** (with optional withdrawal rationale).

### 🛡️ HR Administrator Hub
- **Executive Hiring Pipeline Overview**: Real-time conversion funnel metrics and status breakdowns.
- **Enterprise Candidate Database**: Multi-dimensional filtering by status, department, position, search query, and submission date.
- **Candidate Profile Reviewer**: Full candidate dossier, direct SharePoint CV download, status progression manager (`Submitted` → `Under Review` → `Shortlisted` → `Interview` → `Selected` → `Hired` / `Rejected`), and complete status transition audit timeline.
- **Confidential Internal HR Notes**: Private candidate evaluation and recruiter notes thread, completely isolated and hidden from regular employees.
- **Requisition Manager**: Create, toggle, and manage active and archived corporate job positions.

### ☁️ Cloud & Enterprise Integrations
- **Microsoft Entra ID (Azure AD)**: Server-side cryptographic token verification using Entra ID public keys (`/discovery/v2.0/keys`), client audience, and issuer validation.
- **Microsoft SharePoint Online**: Resumes are uploaded directly to your corporate document library via Microsoft Graph API with year partitioning (`Referral-CVs/{YEAR}/{filename}`).
- **Zero-Orphan Transaction Rollback**: If a database commit fails after a CV upload, the uploaded file in SharePoint is automatically removed via `delete_cv` to eliminate orphaned files.
- **Zero-Trust Proxied Streaming**: Microsoft Graph access tokens and SharePoint URLs are never exposed to client browsers; CV downloads are securely proxied through authenticated backend streams.
- **AI-Ready Abstraction**: Pre-built `AIServiceInterface` prepared for zero-downtime integration with Azure OpenAI or Anthropic for resume parsing and candidate-job matching.

---

## 🛠 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Backend** | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, MSAL Python, PyJWT, HTTPX |
| **Frontend** | React 19, TypeScript, Vite 8, Lucide Icons, Vanilla CSS Design System, MSAL React |
| **Storage & DB**| SQLite (Development) / PostgreSQL 16 (Production), Microsoft SharePoint Online Document Libraries |
| **Infrastructure** | Docker, Docker Compose, Nginx |

---

## 📂 Repository Structure

```text
Tangentia-Referral-Portal/
├── backend/
│   ├── alembic_migrations/         # Database migration revisions
│   ├── app/
│   │   ├── api/                    # FastAPI routes (auth, jobs, referrals, hr, analytics)
│   │   ├── models/                 # SQLAlchemy 2.0 ORM database models
│   │   ├── schemas/                # Pydantic v2 request/response schemas
│   │   ├── services/
│   │   │   ├── sharepoint/         # Graph API client & local mock storage adapter
│   │   │   ├── auth_service.py     # Microsoft Entra ID JWT verification engine
│   │   │   ├── referral_service.py # Business logic & duplicate detection engine
│   │   │   └── ai_service.py       # Extensible LLM / AI resume parsing interface
│   │   ├── utils/                  # CV file validation & filename sanitization
│   │   ├── config.py               # Pydantic settings management
│   │   ├── database.py             # Database engine & session maker
│   │   └── main.py                 # FastAPI application entry point
│   ├── storage/mock_sharepoint/    # Local offline SharePoint mock document library
│   ├── tests/                      # Pytest integration & role authorization test suite
│   ├── Dockerfile
│   ├── requirements.txt
│   └── seed.py                     # Database seeder with sample jobs & candidates
├── frontend/
│   ├── src/
│   │   ├── auth/                   # MSAL config & React AuthContext
│   │   ├── components/             # Reusable UI components (Modal, StatusBadge, WithdrawModal, Timeline)
│   │   ├── pages/
│   │   │   ├── employee/           # Dashboard, Submit Referral, My Referrals
│   │   │   └── hr/                 # HR Dashboard, Candidate Database, Job Openings, Analytics
│   │   ├── services/api.ts         # Centralized API service & dev token injector
│   │   ├── types/                  # TypeScript data interfaces
│   │   └── index.css               # Curated enterprise dark theme design system
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml              # Production multi-container composition
└── README.md
```

---

## 🚀 Quick Start (Local Development)

The repository features an isolated **Development Mode** (`DEV_MODE=True` and `SHAREPOINT_STORAGE_TYPE=mock`) allowing instantaneous local execution without needing live Azure tenant credentials or a local PostgreSQL server.

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

# Seed sample jobs and initial test referrals
python seed.py

# Run the backend API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

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
DEV_MODE=True  # Set to False to enforce live Microsoft Entra ID JWT verification

# Database (SQLite for dev, PostgreSQL for production)
DATABASE_URL=sqlite:///./referrals.db
# DATABASE_URL=postgresql://postgres:password@localhost:5432/referral_portal

# Microsoft Entra ID (Azure AD)
AZURE_TENANT_ID=your-azure-tenant-id-or-common
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_HR_GROUP_ID=your-entra-security-group-id-for-hr-admins

# Microsoft SharePoint Online (via Graph API)
# Set to 'graph' for real SharePoint; 'mock' for local offline storage
SHAREPOINT_STORAGE_TYPE=mock
SHAREPOINT_SITE_ID=yourtenant.sharepoint.com,site-guid,web-guid
SHAREPOINT_DRIVE_ID=b!your-drive-id-from-graph
SHAREPOINT_ROOT_FOLDER=Referral-CVs
```

### `frontend/.env`
```env
VITE_API_BASE_URL=http://localhost:8000/api
VITE_AZURE_CLIENT_ID=your-azure-client-id
VITE_AZURE_TENANT_ID=your-azure-tenant-id
```

> [!TIP]
> **Can I use real SharePoint in Dev Mode?**
> **Yes!** You can set `SHAREPOINT_STORAGE_TYPE=graph` while keeping `DEV_MODE=True`. This allows you to test real SharePoint uploads/downloads without requiring users to log in via Microsoft Entra ID SSO. Furthermore, **no paid Azure subscription** is required—SharePoint storage uses your organization's Microsoft 365 license.

---

## 🔐 Microsoft Entra ID & SharePoint Setup

### 1. Register Entra ID Application
1. Navigate to the **[Microsoft Entra Admin Center](https://entra.microsoft.com)** > **App registrations** > **New registration**.
2. Name: `Tangentia Employee Referral Portal`.
3. Supported account types: `Accounts in this organizational directory only (Single tenant)`.
4. Redirect URI: Platform `Single-page application (SPA)`, URI: `http://localhost:5173` (and production domain).
5. Under **Certificates & secrets**, create a new **Client secret** and copy its value to `AZURE_CLIENT_SECRET`.

### 2. Configure Microsoft Graph API Permissions
1. Go to **API permissions** > **Add a permission** > **Microsoft Graph** > **Application permissions**.
2. Add:
   - `Sites.ReadWrite.All` or `Files.ReadWrite.All` (for SharePoint document uploads/downloads).
   - `User.Read.All` (optional, for directory sync).
3. Click **"Grant admin consent for [Your Organization]"**.

### 3. Retrieve SharePoint Site ID & Drive ID
1. Create a Document Library named `Referral-CVs` in your target SharePoint site.
2. In [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer), run:
   ```http
   GET https://graph.microsoft.com/v1.0/sites/{yourtenant}.sharepoint.com:/sites/{site-name}
   ```
   The returned `id` is your `SHAREPOINT_SITE_ID`.
3. Query drives for that site:
   ```http
   GET https://graph.microsoft.com/v1.0/sites/{site_id}/drives
   ```
   Locate `Referral-CVs` and copy its `id` to `SHAREPOINT_DRIVE_ID`.

---

## 📡 API Reference

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/auth/config` | Public | Returns Entra ID public client parameters |
| `GET` | `/api/auth/me` | Authenticated | Current user profile and role permissions |
| `GET` | `/api/jobs` | Authenticated | List corporate job openings (`?include_inactive=bool`) |
| `POST`| `/api/jobs` | HR Admin | Create a new job requisition |
| `PUT` | `/api/jobs/{id}` | HR Admin | Update job requisition details or toggle active status |
| `POST`| `/api/referrals/check-duplicate` | Employee | Pre-submission duplicate candidate detection |
| `POST`| `/api/referrals` | Employee | Submit candidate referral with multipart CV document |
| `GET` | `/api/referrals` | Employee | List current employee's submitted referrals |
| `GET` | `/api/referrals/{id}` | Employee / HR | Retrieve candidate referral details |
| `GET` | `/api/referrals/{id}/cv` | Employee / HR | Authenticated proxy download of candidate CV |
| `PUT` | `/api/referrals/{id}/withdraw` | Referrer | Withdraw candidate referral from active review |
| `GET` | `/api/hr/referrals` | HR Admin | Full candidate referral database with filters |
| `PUT` | `/api/hr/referrals/{id}/status` | HR Admin | Update candidate referral pipeline status |
| `POST`| `/api/hr/referrals/{id}/notes` | HR Admin | Add confidential internal HR evaluation note |
| `GET` | `/api/hr/analytics` | HR Admin | Conversion funnel, department metrics, top referrers |

---

## 🐳 Production Deployment (Docker)

To deploy the entire production stack (FastAPI backend + PostgreSQL 16 database + Nginx frontend SPA) using Docker Compose:

```bash
# 1. Start all containers
docker-compose up -d --build

# 2. Apply database migrations
docker-compose exec backend alembic upgrade head
```

- **Web Portal**: `http://<your-server-ip>:3000`
- **Backend API**: `http://<your-server-ip>:8000`
- **PostgreSQL**: Port `5432`

---

## 🛡️ Security & Compliance Highlights

- **Server-Side Signature Verification**: Tokens are cryptographically validated against Microsoft JWKS public keys. Client-supplied identity headers are never trusted in production.
- **Strict Role Boundaries**: HR routes (`/api/hr/*`) enforce `require_hr_admin`. Employees are strictly restricted to their own submitted referrals (`referred_by_user_id == current_user.id`).
- **Zero CV Data Leaks**: Internal SharePoint URLs and Graph access tokens are never exposed to client browsers. All downloads are proxied through authenticated backend streams.
- **File Validation & Anti-Traversal**: Resumes are checked for valid PDF/DOCX magic bytes (`%PDF-`, `PK\x03\x04`), 10MB limits, and strict filename sanitization to eliminate path-traversal attacks.
- **Consent Tracking**: Mandatory explicit candidate consent confirmation stored on every referral record for GDPR/compliance.

---

## 🧪 Running Automated Tests

Run the comprehensive pytest test suite (100% passing):

```bash
cd backend
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

---

## 👨‍💻 Maintainer

Created and maintained by **[VickytheWicked](https://github.com/VickytheWicked)** (`rupeshvansh84@gmail.com`).
