# Tangentia Employee Referral Portal

A production-ready internal **Employee Referral Portal** built for enterprise security, seamless corporate Microsoft Entra ID (Azure AD) authentication, and automated CV document archival into **Microsoft SharePoint Online** document libraries via the **Microsoft Graph API**.

---

## 1. System Architecture

```text
┌────────────────────────────────────────────────────────┐
│               Frontend (React + TypeScript)            │
│         Single Sign-On via Microsoft Entra ID          │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / Authorization: Bearer <Token>
                           ▼
┌────────────────────────────────────────────────────────┐
│             Backend API (FastAPI + Python)             │
│  - Token Verification & Identity Synchronization       │
│  - Role-Based Access Control (Employee vs. HR Admin)   │
│  - Duplicate Candidate Detection Engine                │
│  - Atomic Transactions & SharePoint Rollback Manager   │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
  Microsoft Graph API                      │ SQLAlchemy 2.0 ORM
  (OAuth2 Client Credentials)              │
               ▼                           ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│   Microsoft SharePoint       │ │     PostgreSQL Database     │
│   Document Library           │ │  - Users & Security Roles   │
│   (Referral-CVs/{YEAR}/...)  │ │  - Active Job Openings      │
│   *Source of Truth for CVs*  │ │  - Candidate Referrals      │
│                              │ │  - Status History Audit Log │
│                              │ │  - Confidential HR Notes    │
└──────────────────────────────┘ └─────────────────────────────┘
```

---

## 2. Key Features

- **Microsoft Entra ID (Azure AD) Authentication:**
  - Authenticates users with corporate Microsoft accounts.
  - Zero custom passwords stored or managed.
  - User identity (name, email, entra_user_id) validated and synchronized directly from verified cryptographic JWT tokens.
- **Microsoft SharePoint Document Library CV Storage:**
  - CVs are **never** stored in PostgreSQL binary columns or arbitrary local disks.
  - Resumes are streamed through the backend and uploaded directly to Microsoft SharePoint Online via Microsoft Graph API.
  - Automated directory organization: `Referral-CVs/{YEAR}/REF-{YEAR}-{NUMBER}_{Candidate}_{Position}.pdf`.
  - Transaction safety: If PostgreSQL commit fails, the uploaded SharePoint file is immediately rolled back to prevent orphaned storage.
- **Role-Based Access Control (RBAC):**
  - **Employee:**
    - Submit referrals with PDF / DOCX resumes.
    - Real-time duplicate candidate detection warning modal.
    - View their own submitted referrals and timeline status.
    - Withdraw submitted referrals before review.
    - Strictly forbidden from viewing other employees' referrals, HR notes, or admin tools.
  - **HR Admin:**
    - Full candidate referral data grid with advanced filtering (status, department, position, date, search).
    - One-click secure CV download streamed through the backend.
    - Change referral status (`Submitted` → `Under Review` → `Shortlisted` → `Interview` → `Selected` → `Hired` / `Rejected`).
    - Confidential Internal HR Notes thread (completely hidden from employees).
    - Manage active/archived corporate job requisitions.
    - Visual hiring funnel analytics, department breakdown, and top referrers leaderboard.
- **Duplicate Candidate Detection:**
  - Multi-attribute matching (candidate email, normalized phone, candidate name + target position).
  - Pre-submission alerts showing matching referral numbers, previous status, and referrer details.
- **AI-Readiness Layer:**
  - Decoupled `AIServiceInterface` for future integration with Azure OpenAI or Anthropic (resume parsing, job fit scoring, candidate summaries).

---

## 3. Microsoft Entra ID App Registration Guide

### Step 1: Register the Application in Azure Portal
1. Navigate to **Microsoft Entra admin center** (or Azure Portal > Microsoft Entra ID).
2. Go to **App registrations** > **New registration**.
3. Name: `Tangentia Employee Referral Portal`.
4. Supported account types: `Accounts in this organizational directory only (Single tenant)`.
5. Redirect URI:
   - Platform: `Single-page application (SPA)`
   - URI: `http://localhost:3000` (and your production domain).
6. Click **Register**.

### Step 2: Note Core Identifiers
From the Overview tab, record:
- **Application (client) ID**: `AZURE_CLIENT_ID`
- **Directory (tenant) ID**: `AZURE_TENANT_ID`

### Step 3: Create Client Secret
1. Go to **Certificates & secrets** > **Client secrets** > **New client secret**.
2. Add a description (e.g. `Referral Portal Backend`) and select an expiration.
3. Copy the **Value** immediately: `AZURE_CLIENT_SECRET`.

### Step 4: Configure Microsoft Graph API Permissions
1. Go to **API permissions** > **Add a permission** > **Microsoft Graph**.
2. Select **Application permissions** (required for backend server-to-server SharePoint operations).
3. Add the following permissions:
   - `Sites.ReadWrite.All` or `Files.ReadWrite.All` (for SharePoint document library uploads and downloads).
   - `User.Read.All` (optional, for directory lookups).
4. Click **Grant admin consent for [Your Organization]** (Status must display green checkmarks).

### Step 5: Define App Roles or Security Groups (for HR Admins)
1. Go to **App roles** > **Create app role**.
   - Display name: `HR Administrator`
   - Allowed member types: `Users/Groups`
   - Value: `HR_Admin`
   - Description: `Full administrative access to referral candidate pipeline and HR notes`
2. Assign your HR team members or security group to this role under **Enterprise applications**.
3. (Optional) Alternatively, supply `AZURE_HR_GROUP_ID` with the Object ID of your HR security group.

---

## 4. Microsoft SharePoint Document Library Configuration

1. Create or select a dedicated SharePoint site (e.g. `https://tangentia.sharepoint.com/sites/HumanResources`).
2. Inside the site, create a Document Library named `Referral-CVs`.
3. To obtain the `SHAREPOINT_SITE_ID` and `SHAREPOINT_DRIVE_ID`:
   - Run a Graph Explorer query:
     ```http
     GET https://graph.microsoft.com/v1.0/sites/tangentia.sharepoint.com:/sites/HumanResources
     ```
     The returned `id` is your `SHAREPOINT_SITE_ID` (format: `tenant.sharepoint.com,site-guid,web-guid`).
   - Query drives for that site:
     ```http
     GET https://graph.microsoft.com/v1.0/sites/{site_id}/drives
     ```
     Locate the drive with name `Referral-CVs` and record its `id` as `SHAREPOINT_DRIVE_ID`.

---

## 5. Local Development Setup

The application features an isolated **Dev Mode** (`DEV_MODE=True` and `SHAREPOINT_STORAGE_TYPE=mock`) allowing developers to test the full application immediately without requiring live Azure tenant credentials or a local PostgreSQL server.

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** & **npm 10+**

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env as needed. By default, it uses SQLite and Mock SharePoint for zero-config local testing.

# 5. Seed sample job openings and initial referrals
python seed.py

# 6. Run automated test suite
PYTHONPATH=. pytest tests/ -v

# 7. Start FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
API Documentation will be accessible at: `http://localhost:8000/api/docs`

### Frontend Setup

```bash
# 1. Navigate to frontend directory (in a new terminal)
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env

# 4. Start Vite dev server
npm run dev
```
The Web Portal will be live at: `http://localhost:5173`

---

## 6. Testing & Verifying User Workflows

### Employee Workflow:
1. Open `http://localhost:5173`.
2. Click **"Employee View"** (or login as Sarah Jenkins).
3. Notice the **Employee Dashboard** showing metrics and recent submissions.
4. Click **"Submit Referral"**:
   - Fill in candidate details (e.g. `Aniket Verma`, `aniket@example.com`, `+14165550188`).
   - Select the target job opening and your relationship to the candidate.
   - Upload a sample PDF resume (`.pdf` or `.docx`).
   - Check the mandatory **Candidate Consent Confirmation**.
   - Click **"Submit Referral & Upload CV"**.
   - Notice the generated referral ID (`REF-2026-00000X`) and confirmation screen.
5. In **"My Referrals"**, view the submitted referral and click **"Download"** to test secure CV streaming.

### Duplicate Detection Verification:
- Try submitting a referral with the same email (`aniket@example.com`).
- The portal immediately displays the **Duplicate Candidate Alert Dialog** with previous referral number, status, and referrer information before allowing you to proceed.

### HR Administrator Workflow:
1. Click **"HR Admin View"** in the top navigation bar.
2. The UI instantly transitions to the **HR & Talent Acquisition Hub**.
3. Go to **"All Referrals"**:
   - Search by candidate name, filter by department or status.
   - Click **"Profile"** on any candidate to open the comprehensive review drawer.
   - Click **"Change Status"**: Select `Interview` and enter an interview scheduling note.
   - Under **"Confidential Internal HR Notes"**, enter a private note (e.g. `Strong system design performance. Advancing to director round.`).
4. Switch back to **"Employee View"**:
   - Observe that the candidate status reflects `Interview`, but the **HR Notes remain completely hidden** from the employee!

---

## 7. Production Deployment (Docker Orchestration)

To deploy the portal to production with a real PostgreSQL database:

1. Create a root `.env` file containing your production secrets:
   ```env
   AZURE_TENANT_ID=your-azure-tenant-id
   AZURE_CLIENT_ID=your-azure-client-id
   AZURE_CLIENT_SECRET=your-azure-client-secret
   AZURE_HR_GROUP_ID=your-entra-security-group-id-for-hr-admins
   SHAREPOINT_STORAGE_TYPE=graph
   SHAREPOINT_SITE_ID=your-tenant.sharepoint.com,site-id,web-id
   SHAREPOINT_DRIVE_ID=your-sharepoint-drive-id
   SHAREPOINT_ROOT_FOLDER=Referral-CVs
   ```

2. Launch all services via Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

3. Run database migrations:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

Services:
- **Web Portal:** `http://your-server-ip:3000` (Nginx + React SPA)
- **API Server:** `http://your-server-ip:8000` (FastAPI)
- **Database:** PostgreSQL on port 5432

---

## 8. Security Highlights

- **Server-Side Token Verification:** All incoming requests validate Microsoft Entra ID public signing keys (JWKS) and client audiences. Email addresses from frontend headers are never trusted.
- **Strict Role-Based Authorization:** HR routes (`/api/hr/*`) enforce `require_hr_admin`. Regular employees can only query their own referrals (`referred_by_user_id == current_user.id`).
- **CV Stream Proxying:** Microsoft Graph tokens and SharePoint access secrets are never exposed to client browsers. CV downloads are securely proxied through authenticated backend streaming.
- **File Validation & Anti-Traversal:** All CV uploads are validated using file magic byte signatures (`%PDF-`, `PK\x03\x04`), max file size enforcement (10MB), and sanitized filenames.
