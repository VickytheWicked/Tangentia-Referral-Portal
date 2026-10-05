# Tangentia Employee Referral Portal — Functional Specification Document
**Document Reference:** FSD-TERP-2026-V2.1  
**Version:** 2.1.0  
**Effective Date:** October 2026  
**Classification:** Internal — Product & Functional Requirements  
**Product:** Tangentia Employee Referral Portal  
**Target Audience:** Tangentia Employees, HR Recruitment Teams, Hiring Committees, Product Managers  

---

## 📑 Table of Contents

1. [Executive Summary & Product Objectives](#1-executive-summary--product-objectives)
2. [User Personas & Functional Permission Matrix](#2-user-personas--functional-permission-matrix)
3. [Employee Experience & Referral Submission Workflows](#3-employee-experience--referral-submission-workflows)
   - 3.1 [Live Job Board & Vacancy Discovery](#31-live-job-board--vacancy-discovery)
   - 3.2 [Instant AI CV Text Extraction & Auto-Fill](#32-instant-ai-cv-text-extraction--auto-fill)
   - 3.3 [Referral Form Inputs & Validation Rules](#33-referral-form-inputs--validation-rules)
   - 3.4 [Real-Time 180-Day Duplicate Prevention Modal](#34-real-time-180-day-duplicate-prevention-modal)
   - 3.5 [Personal "My Referrals" Portfolio & Radar Badges](#35-personal-my-referrals-portfolio--radar-badges)
   - 3.6 [Voluntary Candidate Withdrawal Workflow](#36-voluntary-candidate-withdrawal-workflow)
   - 3.7 [Corporate Hired History Ledger & Export](#37-corporate-hired-history-ledger--export)
4. [HR Administrator Hub & Recruitment Console](#4-hr-administrator-hub--recruitment-console)
   - 4.1 [Corporate HR Authentication & Session Management](#41-corporate-hr-authentication--session-management)
   - 4.2 [Recruiter Dashboard, Funnel Metrics & Leaderboard](#42-recruiter-dashboard-funnel-metrics--leaderboard)
   - 4.3 [Candidate Pipeline Ledger & Multi-Dimensional Search](#43-candidate-pipeline-ledger--multi-dimensional-search)
   - 4.4 [Recruitment Lifecycle Status Progression](#44-recruitment-lifecycle-status-progression)
   - 4.5 [Chronological Status Audit Trail](#45-chronological-status-audit-trail)
   - 4.6 [Confidential Internal Recruiter Notes](#46-confidential-internal-recruiter-notes)
   - 4.7 [Permanent Candidate Cascade Purge (GDPR Compliance)](#47-permanent-candidate-cascade-purge-gdpr-compliance)
   - 4.8 [Requisition Management & CATS Manual Trigger](#48-requisition-management--cats-manual-trigger)
   - 4.9 [Multi-Sheet Microsoft Excel Ledger in Azure Blob Storage](#49-multi-sheet-microsoft-excel-ledger-in-azure-blob-storage)
5. [AI CV Intelligence & Evidence Evaluation Engine](#5-ai-cv-intelligence--evidence-evaluation-engine)
   - 5.1 [Strict Requirement Prioritization (REQ #1 Exp, REQ #2 Edu)](#51-strict-requirement-prioritization-req-1-exp-req-2-edu)
   - 5.2 [Deterministic Mathematical Timeline Verification](#52-deterministic-mathematical-timeline-verification)
   - 5.3 [Anti-Hallucination Factual Quotations & Evidence Grounding](#53-anti-hallucination-factual-quotations--evidence-grounding)
   - 5.4 [Candidate Intelligence Dossier & Interview Guide](#54-candidate-intelligence-dossier--interview-guide)
   - 5.5 [Rate-Limited Sequential Queue (4.0s Inter-Job Delay)](#55-rate-limited-sequential-queue-40s-inter-job-delay)
   - 5.6 [Direct CATS ATS Integration ("Open in CATSOne")](#56-direct-cats-ats-integration-open-in-catsone)
6. [Historical Candidate RAG Recommendations Engine](#6-historical-candidate-rag-recommendations-engine)
   - 6.1 [Passive Talent Discovery for New Requisitions](#61-passive-talent-discovery-for-new-requisitions)
   - 6.2 [Dual Vectorization & 0.45 Similarity Cutoff](#62-dual-vectorization--045-similarity-cutoff)
   - 6.3 [One-Click Candidate Re-Engagement](#63-one-click-candidate-re-engagement)
7. [Automated CATS Careers ATS Synchronization](#7-automated-cats-careers-ats-synchronization)
   - 7.1 [Periodic 6-Hour Background Sync](#71-periodic-6-hour-background-sync)
   - 7.2 [Intelligent 1–2 Sentence Job Summarizer](#72-intelligent-12-sentence-job-summarizer)
   - 7.3 [Corporate Taxonomy Mapping](#73-corporate-taxonomy-mapping)
   - 7.4 [Deterministic Identifier Upserts](#74-deterministic-identifier-upserts)
8. [Data Privacy, Security & User Experience Standards](#8-data-privacy-security--user-experience-standards)

---

## 1. Executive Summary & Product Objectives

The **Tangentia Employee Referral Portal** is designed to maximize talent acquisition efficiency across Tangentia's offices in India, the US, and Canada. By pairing employee networks with automated AI evaluation and ATS synchronization, the portal accelerates hiring speed and eliminates recruiter administrative friction.

### Primary Product Objectives
1. **Zero Employee Friction:** Enable employees to refer high-caliber contacts in under 60 seconds with drag-and-drop resume parsing, auto-fill, and duplicate alerts. No login barriers required for employee submissions.
2. **Deterministic, Hallucination-Free Candidate Screening:** Empower HR hiring teams with AI evaluation dossiers that prioritize verifiable work experience (REQ #1) and education (REQ #2) with strict factual citations from the resume text.
3. **Live Requisition Synchronization:** Maintain continuous alignment with live openings on Tangentia's CATS One careers portal, guaranteeing employees only refer to active, budgeted vacancies.
4. **Permanent Audit-Ready Persistence:** Guarantee enterprise durability by syncing every referral, status transition, and HR note directly into a multi-sheet Microsoft Excel ledger (`Tangentia_Referrals.xlsx`) stored in Azure Blob Storage.

---

## 2. User Personas & Functional Permission Matrix

The application cleanly divides features between two user tiers:

```
┌───────────────────────────────────────┬───────────────────────────────────────┐
│       Public Employee Workspace       │       Protected HR Recruiter Hub      │
│      (Zero-Friction Submission)       │       (Corporate HR JWT Auth)         │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ • Any corporate Tangentia employee    │ • Verified HR administrators & hiring │
│ • No password / SSO sign-in required  │   committee members                   │
│ • Submit candidate referrals          │ • Full corporate candidate database   │
│ • Real-time duplicate risk checking   │ • Candidate status transitions        │
│ • Track personal submissions portfolio│ • Confidential recruiter notes        │
│ • Download original submitted CVs     │ • Deep AI intelligence dossiers       │
│ • Withdraw own submitted referrals    │ • CATS ATS sync trigger & management  │
│ • Browse active corporate openings    │ • Excel ledger export & cascade purge │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

### Granular Functional Permissions Matrix

| Feature / Action | Public Employee Workspace | Protected HR Recruiter Hub |
|:---|:---:|:---:|
| Browse active job requisitions | ✅ | ✅ |
| Search positions by department, location, or keyword | ✅ | ✅ |
| Drag-and-drop resume upload (.pdf, .docx) | ✅ | ✅ |
| Trigger instant AI CV parsing & form auto-fill | ✅ | ✅ |
| Execute real-time duplicate check (180-day window) | ✅ | ✅ |
| Submit candidate referral with contact details | ✅ | ✅ |
| View personal submitted referrals & status radar | ✅ | ✅ |
| Download submitted candidate resume (Zero-Trust stream) | ✅ (Own Only) | ✅ (All Candidates) |
| Voluntarily withdraw submitted referral with rationale | ✅ (Own Only) | ✅ |
| View company-wide hired candidates history & export | ✅ | ✅ |
| View corporate candidate ledger across all employees | ❌ | ✅ |
| Advance candidate lifecycle status (`Submitted` $\rightarrow$ `Hired`) | ❌ | ✅ |
| Author and view confidential internal recruiter notes | ❌ | ✅ |
| Trigger manual CATS ATS sync and inspect live preview | ❌ | ✅ |
| Create, edit, or deactivate manual job requisitions | ❌ | ✅ |
| View deep AI Candidate Intelligence Dossier | ❌ | ✅ |
| Access Historical Candidate RAG Recommendations | ❌ | ✅ |
| Export 6-sheet `Tangentia_Referrals.xlsx` workbook | ❌ | ✅ |
| Permanently purge candidate record (GDPR cascade purge) | ❌ | ✅ |

---

## 3. Employee Experience & Referral Submission Workflows

### 3.1 Live Job Board & Vacancy Discovery
- **Visual Card Grid:** Displays all open requisitions with department tags, location badges, and employment types.
- **CATS ATS Indicators:** Synced positions carry an official `CATS ATS` badge to designate roles synchronized from Tangentia's primary recruitment portal.
- **Dynamic Search & Filtering:** Instant client-side search across job titles, descriptions, and regions with zero page reload latency.
- **Direct Referral Trigger:** Clicking **"Refer Candidate"** on any job card opens the pre-configured submission workflow for that requisition.

### 3.2 Instant AI CV Text Extraction & Auto-Fill
- **Supported Formats:** `.pdf` and `.docx` documents up to 10MB.
- **Magic-Byte Inspection:** Inspects binary headers (`%PDF-` for PDF, `PK\x03\x04` for DOCX) to ensure genuine documents before parsing.
- **Extraction Pipeline:** 
  1. Primary text extraction via `pdfplumber` / `python-docx`.
  2. Entity distillation (name, email, phone, total experience, skills, summary) powered by Gemini 3.5.
  3. Deterministic regular expression fallbacks for phone and email extraction if LLM is unavailable.
- **Auto-Fill Speed:** Completes extraction in under 2.5 seconds, populating the form fields automatically while allowing the employee to review or edit.

### 3.3 Referral Form Inputs & Validation Rules

```
┌────────────────────────────────────────────────────────┐
│             Referral Submission Form Fields            │
├─────────────────────────┬──────────────────────────────┤
│ Target Job Opening      │ Pre-selected / Dropdown      │
│ Candidate Full Name     │ Text (Required, Min 2 chars) │
│ Candidate Email Address │ Valid Email Format (Required)│
│ Candidate Phone Number  │ E.164 International Format   │
│ Years of Experience     │ Numeric (>= 0, e.g. 5.5)     │
│ Referring Employee Email│ Corporate @tangentia.com     │
│ Key Skills Summary      │ Extracted / Editable Text    │
│ Recommendation Note     │ Optional personal context    │
│ GDPR / Candidate Consent│ Mandatory confirmation toggle│
└─────────────────────────┴──────────────────────────────┘
```

### 3.4 Real-Time 180-Day Duplicate Prevention Modal
Before a referral is written to the database, a pre-submission duplicate check executes against all historical records:
1. **Evaluation Criteria:**
   - Exact email match.
   - Normalized E.164 phone number match.
   - Case-insensitive candidate name match for the same job requisition.
2. **180-Day Window Rule:**
   - **Active Window ($\le$ 180 days):** Displays a warning modal identifying the existing referral, original submission date, and current status. If the candidate is currently active in the pipeline (`Submitted`, `Under Review`, `Shortlisted`, `Interview`, `Selected`), duplicate submission is blocked.
   - **Expired Window (> 180 days):** If the prior submission was over 6 months ago and concluded, the employee can proceed with a re-referral.

### 3.5 Personal "My Referrals" Portfolio & Radar Badges
- **Employee Ledger:** Clean table listing every candidate submitted by the employee.
- **Status Radar Pills:** Real-time color-coded badges indicating recruitment stage:
  - `Submitted` (Blue)
  - `Under Review` (Yellow)
  - `Shortlisted` (Indigo)
  - `Interview` (Purple)
  - `Selected` (Teal)
  - `Hired` (Emerald Green)
  - `Rejected` (Red)
  - `Archived` / `Withdrawn` (Gray)
- **Secure CV Download:** Allows referring employees to download the exact resume binary they uploaded.

### 3.6 Voluntary Candidate Withdrawal Workflow
- **Employee-Initiated Withdrawal:** If a candidate accepts an offer elsewhere or requests withdrawal, the referring employee can click **"Withdraw"**.
- **Rationale Modal:** Prompts for an optional reason for withdrawal.
- **State Transition:** Moves the referral status to `Withdrawn`, timestamps the action in the status audit log, and notifies the recruitment hub.

### 3.7 Corporate Hired History Ledger & Export
- **Company-Wide Celebratory Feed:** Showcases all successfully hired referrals across the organization, highlighting candidate names, hired roles, departments, and referring colleagues.
- **Excel Export:** Employees and HR can download a styled Excel report of hired talent directly from the page.

---

## 4. HR Administrator Hub & Recruitment Console

### 4.1 Corporate HR Authentication & Session Management
- **Zero Entra ID Dependency:** Authentication is direct and self-contained within the portal.
- **HR Credentials:** HR recruiters authenticate at `/api/auth/login` using their `@tangentia.com` email address and password.
- **Cryptographic Security:** Passwords are verified against PBKDF2-HMAC-SHA256 salted hashes stored in the database (synced from the `Users` sheet in `Tangentia_Referrals.xlsx`).
- **Session Tokens:** Successful authentication grants a signed HS256 JWT access token valid for 7 days.
- **Role Gating:** Protected HR endpoints strictly enforce `role == 'hr_admin'`, rejecting unauthorized attempts with HTTP 403 Forbidden.

### 4.2 Recruiter Dashboard, Funnel Metrics & Leaderboard
- **Executive KPI Cards:** Total Referrals, Active Pipeline, Interviews Scheduled, Total Hired, and Overall Conversion Rate.
- **Recruitment Funnel Visualization:** Visual progression displaying conversion rates from `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Interview` $\rightarrow$ `Hired`.
- **Top Referrer Leaderboard:** Recognizes employees with the highest number of successful submissions and hires.

### 4.3 Candidate Pipeline Ledger & Multi-Dimensional Search
- **Centralized Master Table:** Master view of every candidate referral across all business units.
- **Filtering Dimensions:** Filter by Recruitment Status, Department, Job Requisition, Referring Employee, and Date Range.
- **Quick-Action Drawer:** Clicking any row slides open the Candidate Profile Drawer without navigating away from the table.

### 4.4 Recruitment Lifecycle Status Progression
Recruiters transition candidates through structured stages:
$$\text{Submitted} \longrightarrow \text{Under Review} \longrightarrow \text{Shortlisted} \longrightarrow \text{Interview} \longrightarrow \text{Selected} \longrightarrow \text{Hired}$$
- **Terminal States:** `Rejected` (requires mandatory rationale note) or `Archived`.
- **Automatic Promotion to HiredHistory:** Transitioning a candidate to `Hired` automatically copies the candidate's details into the `HiredHistory` database table and the `HiredHistory` worksheet in `Tangentia_Referrals.xlsx`.

### 4.5 Chronological Status Audit Trail
- **Immutable Timeline:** Every status modification creates a permanent audit log entry.
- **Captured Metadata:** Previous status, new status, UTC timestamp, HR recruiter identity, and any transition feedback comments.

### 4.6 Confidential Internal Recruiter Notes
- **Private Recruiter Thread:** Attached directly to each referral record for internal committee feedback, salary negotiations, and interview impressions.
- **Strict Role Isolation:** Confidential notes are stripped from all employee-facing API responses and UI views.
- **Persistent Archival:** Notes write through immediately to the `HRNotes` worksheet in `Tangentia_Referrals.xlsx`.

### 4.7 Permanent Candidate Cascade Purge (GDPR Compliance)
HR administrators can execute a permanent candidate purge to satisfy GDPR "Right to be Forgotten" requirements. An atomic 5-stage cascade purge removes:
1. Candidate record in primary database `referrals` table.
2. Associated audit history entries and confidential HR notes.
3. Candidate profile and evaluation dossier from `cv_intelligence.db`.
4. Original CV binary file from Azure Blob Storage (`referral-cvs/{YEAR}/`).
5. Matching rows across all worksheets in `Tangentia_Referrals.xlsx`.

### 4.8 Requisition Management & CATS Manual Trigger
- **Manual Requisitions:** HR can create bespoke openings with custom titles, job descriptions, department classifications, and active flags.
- **Manual "Sync CATS ATS" Button:** Recruiter trigger fetching live updates from Tangentia's CATS portal on-demand.
- **Live Preview Modal:** Inspects positions published on CATS ATS before committing changes to the internal database.

### 4.9 Multi-Sheet Microsoft Excel Ledger in Azure Blob Storage
- **Automatic Write-Through:** All system operations write through to `Tangentia_Referrals.xlsx` in the `referral-data` Azure Blob Storage container.
- **6 Structured Worksheets:**
  - `Referrals` (Candidate data, contact info, status, CV pointers)
  - `JobPositions` (Requisition titles, departments, locations, CATS flags)
  - `StatusHistory` (Chronological status change logs)
  - `HRNotes` (Private recruiter evaluations)
  - `Users` (Internal user accounts and access roles)
  - `HiredHistory` (Historical ledger of successful hires)
- **One-Click Export:** HR recruiters can download the entire styled spreadsheet directly from the dashboard at any time.

---

## 5. AI CV Intelligence & Evidence Evaluation Engine

### 5.1 Strict Requirement Prioritization (REQ #1 Exp, REQ #2 Edu)
The AI requirement engine evaluates resumes against requisition specifications with enforced structural prioritization:
1. **REQ #1: Total Experience (Numeric Years)** — Verified deterministically from work chronology.
2. **REQ #2: Education & Academic Qualifications** — Verified for required degrees, disciplines, and certifications.
3. **REQ #3: Role & Domain Alignment** — Functional match for industry, vertical, and core responsibilities.
4. **REQ #4+: Technical Skills & Tooling** — Hands-on proficiency with required frameworks, languages, and platforms.

### 5.2 Deterministic Mathematical Timeline Verification
- Pre-computes candidate total work experience using pure Python before invoking the LLM.
- If the candidate's verified experience is less than the requisition minimum, REQ #1 is deterministically forced to `NOT_MET` or `PARTIALLY_MET`. The LLM cannot hallucinate credit for missing years of experience.

### 5.3 Anti-Hallucination Factual Quotations & Evidence Grounding
- **Verifiable Quotes:** Every evaluation score must cite exact verbatim phrases from the resume text.
- **Evidence Differentiation:**
  - `MET`: Candidate credentials explicitly proven with verbatim citation.
  - `NOT_DEMONSTRATED`: The resume contains no mention or evidence of the requirement.
  - `NOT_MET`: The resume contains evidence directly contradicting the requirement (e.g., 3 years experience when 8 is required).

### 5.4 Candidate Intelligence Dossier & Interview Guide
- **Match Score (0–100%):** Weighted fit score reflecting candidate alignment.
- **Categorical Fit Tier:** `Excellent Match` (85–100%), `Good Match` (70–84%), `Moderate Match` (50–69%), or `Low Match` (<50%).
- **Strengths & Gaps:** High-level executive bullet points summarizing candidate advantages and areas needing verification.
- **Tailored Interview Questions:** 3–5 role-specific technical questions generated to probe identified skill gaps during interviews.

### 5.5 Rate-Limited Sequential Queue (4.0s Inter-Job Delay)
- Background processing worker evaluates newly submitted resumes sequentially.
- Enforces an exact 4.0-second delay between API calls to prevent exceeding Gemini rate limits.
- Includes automated circuit-breaker protection with exponential backoff on network failures.

### 5.6 Direct CATS ATS Integration ("Open in CATSOne")
- When reviewing candidates referred to a CATS-synced opening, the dossier modal displays a direct **"Open in CATSOne"** deep-link button opening the requisition on Tangentia's production recruitment portal.

---

## 6. Historical Candidate RAG Recommendations Engine

### 6.1 Passive Talent Discovery for New Requisitions
Whenever a new requisition is created or synced from CATS ATS, the Historical RAG Engine automatically searches past candidate referrals to find qualified applicants who were not hired for prior roles.

### 6.2 Dual Vectorization & 0.45 Similarity Cutoff
- **Vector Space:** Generates 3072-dimensional embeddings via Gemini `gemini-embedding-001` combined with a 128-dimensional unit hypersphere projection of extracted skill n-grams.
- **Relevance Cutoff:** Only candidates achieving cosine similarity $\ge 0.45$ are surfaced to recruiters, preventing low-relevance noise.

### 6.3 One-Click Candidate Re-Engagement
Recruiters can inspect the candidate's original resume and evaluation dossier directly from the RAG recommendation card and re-engage them for the new role with one click.

---

## 7. Automated CATS Careers ATS Synchronization

### 7.1 Periodic 6-Hour Background Sync
An in-process APScheduler background cron executes every 6 hours to fetch active positions from `tangentia.catsone.com/careers/9463-General`.

### 7.2 Intelligent 1–2 Sentence Job Summarizer
The scraper strips HTML boilerplate, legal disclaimers, and styling, using AI distillation to generate a clean 1–2 sentence job summary highlighting key responsibilities and technologies.

### 7.3 Corporate Taxonomy Mapping
Scraped positions are classified into standardized Tangentia business units:
- *Intelligent Automation*
- *Cloud & Integration*
- *Data & Analytics*
- *Finance & Enterprise Solutions*
- *Global Sales & Marketing*
- *Engineering & Quality Assurance*

### 7.4 Deterministic Identifier Upserts
Openings are keyed by deterministic IDs (`cats-{id}`). Active openings are updated, new positions are inserted, and stale postings are marked inactive without duplicate entries.

---

## 8. Data Privacy, Security & User Experience Standards

1. **Zero-Trust Proxied Document Streaming:** Cloud storage URLs and Azure Storage Account connection strings are never sent to client browsers. All CV downloads stream through authenticated FastAPI backend endpoints.
2. **Strict Corporate Boundary:** Employee submissions require a valid `@tangentia.com` email address. HR administration requires valid corporate credentials.
3. **Responsive Dark-Mode Enterprise UI:** Clean corporate design system styled in accordance with Tangentia's official 2026 branding.
4. **Safety Watchdogs:** Frontend features a 4-second authentication watchdog and 25-second API timeout to eliminate UI loading hangs.

---

*Tangentia Employee Referral Portal — Functional Specification Document v2.1.0*  
*Document finalized: October 2026*
