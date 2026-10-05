# Tangentia Employee Referral Portal
# Features Specification Document

**Document Reference:** FSD-TERP-2026  
**Version:** 2.0.0  
**Effective Date:** October 2026  
**Classification:** Internal — Product, HR & Functional Architecture  
**Product:** Tangentia Employee Referral Portal  
**Target Audience:** Tangentia Employees, HR Recruitment Teams, Hiring Managers, Product Leadership  

---

## 📑 Table of Contents

1. [Executive Summary & Product Vision](#1-executive-summary--product-vision)
2. [User Roles & Functional Permission Matrix](#2-user-roles--functional-permission-matrix)
3. [Employee Experience & Referral Submission Features](#3-employee-experience--referral-submission-features)
   - 3.1 [Live Job Board & Requisition Browser](#31-live-job-board--requisition-browser)
   - 3.2 [AI-Powered Instant CV Auto-Fill](#32-ai-powered-instant-cv-auto-fill)
   - 3.3 [Streamlined Referral Submission Form](#33-streamlined-referral-submission-form)
   - 3.4 [Real-Time Pre-Submission Duplicate Prevention Engine](#34-real-time-pre-submission-duplicate-prevention-engine)
   - 3.5 [Employee Referral Portfolio ("My Referrals")](#35-employee-referral-portfolio-my-referrals)
   - 3.6 [Referral Withdrawal Workflow](#36-referral-withdrawal-workflow)
   - 3.7 [Company-Wide Hired History Ledger](#37-company-wide-hired-history-ledger)
4. [HR Administrator Hub & Recruitment Console Features](#4-hr-administrator-hub--recruitment-console-features)
   - 4.1 [Executive Recruitment Dashboard & Funnel Analytics](#41-executive-recruitment-dashboard--funnel-analytics)
   - 4.2 [Enterprise Candidate Database & Search Engine](#42-enterprise-candidate-database--search-engine)
   - 4.3 [Candidate Lifecycle Status Progression](#43-candidate-lifecycle-status-progression)
   - 4.4 [Chronological Status Audit Trail](#44-chronological-status-audit-trail)
   - 4.5 [Confidential Internal Recruiter Notes](#45-confidential-internal-recruiter-notes)
   - 4.6 [Permanent Candidate Deletion (Cascade Purge)](#46-permanent-candidate-deletion-cascade-purge)
   - 4.7 [Requisition Manager & CATS Manual Synchronization](#47-requisition-manager--cats-manual-synchronization)
   - 4.8 [Multi-Sheet Microsoft Excel Audit Ledger in Azure Blob Storage](#48-multi-sheet-microsoft-excel-audit-ledger-in-azure-blob-storage)
5. [AI CV Intelligence & Candidate Evaluation Features](#5-ai-cv-intelligence--candidate-evaluation-features)
   - 5.1 [Multi-Format Resume Text Extraction](#51-multi-format-resume-text-extraction)
   - 5.2 [Evidence-Based Structured Requirement Analyzer](#52-evidence-based-structured-requirement-analyzer)
   - 5.3 [Anti-Hallucination Factual Citations](#53-anti-hallucination-factual-citations)
   - 5.4 [Comprehensive Candidate Intelligence Dossier](#54-comprehensive-candidate-intelligence-dossier)
   - 5.5 [Direct CATS ATS Requisition Integration ("Open in CATSOne")](#55-direct-cats-ats-requisition-integration-open-in-catsone)
   - 5.6 [Pre-Cached Requisition Specifications](#56-pre-cached-requisition-specifications)
   - 5.7 [Automated Background Evaluation Queue](#57-automated-background-evaluation-queue)
   - 5.8 [Pre-Submission JEV Relevance Pre-Screening](#58-pre-submission-jev-relevance-pre-screening)
6. [Historical Candidate RAG Recommendations Features](#6-historical-candidate-rag-recommendations-features)
   - 6.1 [Passive Talent Discovery for New Positions](#61-passive-talent-discovery-for-new-positions)
   - 6.2 [Semantic Similarity Scoring & Profile Retrieval](#62-semantic-similarity-scoring--profile-retrieval)
   - 6.3 [Candidate Comparison & Match Rationale](#63-candidate-comparison--match-rationale)
7. [Automated CATS Careers ATS Synchronization Features](#7-automated-cats-careers-ats-synchronization-features)
   - 7.1 [Live Requisition Ingestion](#71-live-requisition-ingestion)
   - 7.2 [Automated 6-Hour Background Sync](#72-automated-6-hour-background-sync)
   - 7.3 [Intelligent 1–2 Sentence Job Summarizer](#73-intelligent-12-sentence-job-summarizer)
   - 7.4 [Automated Taxonomy Classification](#74-automated-taxonomy-classification)
   - 7.5 [Deterministic Requisition Management](#75-deterministic-requisition-management)
8. [Data Privacy, Security & User Experience Highlights](#8-data-privacy-security--user-experience-highlights)

---

## 1. Executive Summary & Product Vision

The **Tangentia Employee Referral Portal** is an internal corporate platform engineered to transform how Tangentia discovers, evaluates, and hires talent through employee networks across its international hubs in India, the United States, and Canada.

### Core Objectives
- **Zero Friction for Employees:** Allow staff to refer candidates in under 60 seconds with instant AI CV parsing, auto-filling, and duplicate prevention.
- **Empowered Recruiter Decision-Making:** Provide HR teams with AI-grounded requirement evaluation dossiers, comparing candidate credentials directly against requisition criteria with evidence citations.
- **Live ATS Alignment:** Continuously synchronize open positions with Tangentia's primary CATS Careers ATS, ensuring employees only refer candidates to genuine, active vacancies.
- **Permanent Enterprise Transparency:** Maintain complete, audit-ready synchronization across runtime databases and the persistent Microsoft Excel workbook in Azure Blob Storage.

---

## 2. User Roles & Functional Permission Matrix

The portal separates capabilities across two functional experiences: the **Public Employee Workspace** (designed for zero friction, requiring no login to submit referrals) and the **Protected HR Administration Hub** (secured by dedicated corporate HR email & password authentication issuing signed JWT tokens).

| Portal Feature / Capability | Employee Workspace | HR Administration Hub |
|:---|:---:|:---:|
| Browse live job openings & search by department/location |  |  |
| Upload CV and trigger instant AI form auto-fill |  |  |
| Submit candidate referral with contact details & consent |  |  |
| Run real-time pre-submission duplicate warning check |  |  |
| View own submitted referrals portfolio & status radar |  |  |
| Download original submitted CV for own candidates |  |  |
| Voluntarily withdraw own candidate referral |  |  |
| View company-wide hired candidates history & export Excel |  |  |
| View entire corporate candidate database across all referrers | ❌ |  |
| Transition candidate recruitment status (`Under Review` $\rightarrow$ `Hired`) | ❌ |  |
| Read and write confidential internal HR recruiter notes | ❌ |  |
| Access full AI Candidate Intelligence Dossiers & Fit Scores | ❌ |  |
| Access Historical Candidate RAG Recommendations | ❌ |  |
| Manually trigger live CATS ATS synchronization & preview | ❌ |  |
| Create, edit, and close job requisitions | ❌ |  |
| Permanently delete candidate records (with cascade cleanup) | ❌ |  |
| Export full 6-sheet audit ledger Excel workbook | ❌ |  |

---

## 3. Employee Experience & Referral Submission Features

### 3.1 Live Job Board & Requisition Browser
- **Live Position Catalog:** Displays all active requisitions sourced from the Tangentia CATS Careers portal.
- **CATS ATS Badging:** Openings imported directly from the corporate ATS display a distinct **`CATS ATS`** badge.
- **Multi-Dimensional Filtering:** Instant search bar filtering by job title, department (*Intelligent Automation*, *Cloud & Integration*, *Data & Analytics*, *Global Sales*, *Engineering*), location (*Toronto*, *Goa*, *Remote*), and employment type (*Full-time*, *Contract*, *Internship*).
- **Direct Referral Trigger:** Clicking **"Refer Candidate"** on any job card immediately launches the submission form with the target position pre-selected.

### 3.2 AI-Powered Instant CV Auto-Fill
- **Drag-and-Drop Document Uploader:** Supports `.pdf` and `.docx` file formats up to 10 MB with client-side and server-side magic-byte verification.
- **Instant Resume Text Extraction:** On upload, an automated parser analyzes the candidate's resume and extracts key attributes within seconds:
  - Candidate Full Name
  - Candidate Email Address
  - Contact Phone Number
  - Calculated Total Years of Professional Experience
  - Core Technical & Professional Skills List
  - 2–3 Sentence Professional Summary
- **Editable Form Population:** Extracted values automatically populate the submission form fields, allowing the employee to review, verify, or refine values before finalizing.

### 3.3 Streamlined Referral Submission Form
- **Frictionless Employee Verification:** The referring employee only enters their official `@tangentia.com` email address. The system automatically derives the employee's display name from the corporate account or identity context.
- **Optional Recommendation Note:** To minimize administrative effort, recommendation notes are optional while still permitting employees to submit qualitative endorsements if desired.
- **Candidate Consent Tracking:** Explicit checkbox verifying candidate consent prior to submission, enforcing corporate compliance and data privacy regulations.
- **Unique Sequential Referral Code:** Every finalized submission generates an immutable tracking code formatted as `REF-{YEAR}-{000001}`.

### 3.4 Real-Time Pre-Submission Duplicate Prevention Engine
- **Instant Pre-Flight Evaluation:** When the employee initiates a referral, the portal evaluates candidate data against all active records submitted within a rolling **180-day window (6 months)**:
  1. **Exact Email Match:** Case-insensitive comparison against existing candidate email records.
  2. **Normalized Phone Match:** Strips all non-digit characters and matches the candidate's standardized contact number.
  3. **Name & Requisition Match:** Identifies candidates with the same name applying for the same open requisition.
- **Interactive Risk Warning Modal:** If an active record is detected within the 180-day window, a clear warning modal opens presenting:
  - Existing referral code and candidate name
  - Target position and current recruitment status
  - Name of the employee who originally referred the candidate
  - Date of original submission
- **Clean 180-Day Re-Referral Rule:** If a candidate was referred more than 180 days ago, the system treats them as eligible for re-referral, updating the record cleanly without triggering false-positive alerts.

### 3.5 Employee Referral Portfolio ("My Referrals")
- **Personal Referral Dashboard:** Dedicated workspace where employees monitor all their submitted candidates.
- **Status Radar Badges:** Visually distinct, color-coded status pills indicating real-time candidate progression:
  - 🟣 `Submitted` — Referral received and entered into the intake queue.
  - 🔵 `Under Review` — Recruitment team is reviewing credentials.
  - 🟡 `Shortlisted` — Candidate cleared initial screening.
  - 🟠 `Interview` — Technical or departmental interviews in progress.
  - 🟢 `Selected` — Candidate received an offer.
  - ❇️ `Hired` — Candidate accepted and successfully onboarded.
  - 🔴 `Rejected` — Candidate not selected for the current role.
  - ⚪ `Withdrawn` — Referral voluntarily rescinded.
  - 🟤 `Archived` — Archived for future requisition matching.
- **Secure CV Download:** Employees can download the exact resume file they submitted at any time via an authenticated streaming proxy.

### 3.6 Referral Withdrawal Workflow
- **Voluntary Withdrawal:** Referring employees can withdraw active candidates if circumstances change (e.g., candidate accepted another offer).
- **Withdrawal Modal:** Prompts the employee for an optional rationale note before transitioning the status to `Withdrawn`.
- **Audit Preservation:** Withdrawn referrals remain recorded in the history log to preserve data integrity and prevent immediate re-submission abuse.

### 3.7 Company-Wide Hired History Ledger
- **Public Celebration & Transparency:** Dedicated view displaying all candidates successfully hired through the referral program.
- **Referral Bonus Reconciliation:** Displays candidate names, requisition titles, hiring departments, referring employees, and hire dates.
- **Excel Export:** Employees and HR staff can download a styled Microsoft Excel spreadsheet of hired history for record-keeping.

---

## 4. HR Administrator Hub & Recruitment Console Features

### 4.1 Executive Recruitment Dashboard & Funnel Analytics
- **Conversion Funnel Visualization:** Visual funnel showing pipeline progression from initial submission to final hire.
- **Departmental Distribution:** Metrics breaking down referral volume across business divisions (*Engineering*, *Cloud*, *AI*, *Sales*).
- **Top Referrer Leaderboard:** Recognition rankings celebrating employees who submit the highest number of successful candidates.
- **Quick-Action Modals:** Direct access to recent candidate submissions requiring review.

### 4.2 Enterprise Candidate Database & Search Engine
- **Centralized Pipeline Ledger:** Comprehensive data table listing all candidate referrals across the organization.
- **Multi-Parameter Search:** Real-time search across candidate names, emails, phones, job titles, and referrer names.
- **Advanced Status & Department Filters:** Filter by recruitment stage, target department, date range, or active openings.
- **Responsive Candidate Drawer:** Clicking any candidate row opens their detailed profile drawer without navigating away from the database.

### 4.3 Candidate Lifecycle Status Progression
- **Interactive Status Updater:** Recruiter modal enabling seamless transitions across the complete recruitment lifecycle:
  $$\text{Submitted} \longrightarrow \text{Under Review} \longrightarrow \text{Shortlisted} \longrightarrow \text{Interview} \longrightarrow \text{Selected} \longrightarrow \text{Hired}$$
- **Rejection & Archival:** Support for terminal states (`Rejected`, `Archived`) with optional recruiter rationale notes.
- **Write-Through Synchronization:** Every status update immediately updates the runtime database, audit trail, and Microsoft Excel ledger stored in Azure Blob Storage.

### 4.4 Chronological Status Audit Trail
- **Immutable Timeline:** Every status change produces a permanent timeline entry.
- **Audit Details:** Logs previous status, new status, exact UTC timestamp, and the full name of the HR administrator who authorized the transition.
- **Review Notes:** Displays any contextual comments or interview feedback recorded during the transition.

### 4.5 Confidential Internal Recruiter Notes
- **Strictly Isolated Discussion Thread:** Private discussion area for HR administrators and hiring committees to exchange interview impressions, compensation expectations, and background check notes.
- **Zero Employee Visibility:** Confidential notes are never accessible to regular employees or visible in employee portfolio views.
- **Timestamped Author Attribution:** Each note is stamped with the author's identity and creation date.

### 4.6 Permanent Candidate Deletion (Cascade Purge)
- **GDPR & Right-to-be-Forgotten Compliance:** HR administrators have the authority to permanently delete a referral.
- **Full Cascade Cleanup:** Purges the candidate from:
  1. Primary referral database records
  2. Status history logs and confidential notes
  3. AI extraction profiles and match scores in `cv_intelligence.db`
  4. Cloud resume document storage in Azure Blob Storage
  5. Microsoft Excel workbook entries in Azure Blob Storage

### 4.7 Requisition Manager & CATS Manual Synchronization
- **Requisition Administration:** HR administrators can create custom manual positions, edit job titles, update descriptions, and toggle active status.
- **One-Click "Sync CATS ATS" Button:** Manual sync trigger in the HR console fetching fresh job postings directly from the live CATS careers portal.
- **Live Preview Modal:** HR recruiters can view a preview of live positions published on CATS ATS before committing them to the system.

### 4.8 Multi-Sheet Microsoft Excel Audit Ledger in Azure Blob Storage
- **Automatic Write-Through Ledger:** Synchronizes all referral operations in real time to `Tangentia_Referrals.xlsx`, persisted securely in Azure Blob Storage via `BlobExcelService`.
- **6 Structured Worksheets:**
  - `Referrals` (Candidate data, contact info, status, CV pointers)
  - `JobPositions` (Requisition titles, departments, locations)
  - `StatusHistory` (Chronological status change logs)
  - `HRNotes` (Private recruiter evaluations)
  - `Users` (Internal user accounts and access roles)
  - `HiredHistory` (Historical ledger of successful hires)
- **One-Click Full Workbook Export:** HR administrators can download the entire styled spreadsheet directly from the dashboard at any time.

---

## 5. AI CV Intelligence & Candidate Evaluation Features

### 5.1 Multi-Format Resume Text Extraction
- **Fault-Tolerant Parsing Pipeline:** Extracts text, tables, and metadata from complex resume formats, multi-column layouts, and graphical documents.
- **Format Support:** Full native support for `.pdf` and `.docx` formats.
- **Fallback Heuristics:** Includes regular expression entity parsing to reliably extract contact details and employment dates even if formatting is non-standard.

### 5.2 Evidence-Based Structured Requirement Analyzer
The analyzer decomposes job descriptions into discrete, verifiable requirement specifications and evaluates candidate resumes against them using strict prioritization rules:

```
┌────────────────────────────────────────────────────────────────┐
│             Strict Requirement Priority Ordering               │
├────────────────────────────────────────────────────────────────┤
│ REQ #1: Total Professional Experience (Numeric Years)          │
│         - Evaluated deterministically from CV work chronology  │
├────────────────────────────────────────────────────────────────┤
│ REQ #2: Education & Academic Qualifications                    │
│         - Evaluated for degrees, certifications & disciplines  │
├────────────────────────────────────────────────────────────────┤
│ REQ #3: Core Role & Domain Alignment                           │
│         - Evaluated for industry, vertical & function match    │
├────────────────────────────────────────────────────────────────┤
│ REQ #4+: Technical Skills, Frameworks & Tooling                │
│         - Evaluated for hands-on technical proficiency         │
└────────────────────────────────────────────────────────────────┘
```

- **Guaranteed REQ #1 (Total Experience):** Total years of professional experience is strictly enforced as the primary requirement, computed mathematically from CV employment dates.
- **Guaranteed REQ #2 (Education):** Academic degrees and technical diplomas are guaranteed as the secondary requirement.
- **Deterministic Facts Pre-Loading:** Experience years are calculated in Python prior to LLM evaluation. The computed facts are pre-loaded into the analysis context so the AI model cannot contradict or hallucinate mathematical figures.

### 5.3 Anti-Hallucination Factual Citations
- **Grounded CV Quotes:** Every requirement evaluation cites direct verbatim evidence or specific summaries extracted from the candidate's resume.
- **Strict Evidence Standards:**
  - `SUPPORTED`: Clear evidence confirms the requirement is satisfied.
  - `PARTIALLY_SUPPORTED`: Some relevant experience is documented, but depth or duration is incomplete.
  - `NOT_DEMONSTRATED`: The resume text contains insufficient evidence to confirm the requirement.
  - `NOT_MET`: The resume contains explicit factual evidence that contradicts the requirement (e.g., candidate has 3 years of experience when 8+ are required).
- **Prohibition on Subjective Verdicts:** The AI engine is strictly barred from inventing qualifications or rendering subjective hiring recommendations.

### 5.4 Comprehensive Candidate Intelligence Dossier
HR recruiters can inspect a deep-dive AI evaluation dossier for any candidate:
- **Job-Fit Match Score:** Quantitative alignment score ranging from 0% to 100%.
- **4-Tier Match Level:**
  - 🟢 **Strong Match** (Score $\ge 75\%$)
  - 🟡 **Good Match** (Score $\ge 55\%$)
  - 🟠 **Potential Match** (Score $\ge 35\%$)
  - 🔴 **Irrelevant** (Score $< 35\%$)
- **Skills Comparison Matrix:** Side-by-side breakdown of matched skills vs missing required skills.
- **Experience Alignment Breakdown:** Factual analysis comparing required seniority against verified CV chronology.
- **Candidate Key Strengths:** Highlighted professional accomplishments and specialized competencies.
- **Identified Competency Gaps:** Clear identification of missing qualifications or tools.
- **Custom Interview Questions:** Tailored technical and situational interview questions designed to test the candidate's identified gap areas.

### 5.5 Direct CATS ATS Requisition Integration ("Open in CATSOne")
- **Direct Candidate-to-ATS Bridge:** In the Candidate Intelligence Dossier, recruiters have access to an **"Open in CATSOne"** button.
- **Instant Deep-Link:** Clicking the button directly opens the live requisition on the Tangentia CATS Careers portal (`tangentia.catsone.com/careers/9463-General/jobs/{cats_job_id}`), allowing recruiters to cross-reference hiring manager notes immediately.

### 5.6 Pre-Cached Requisition Specifications
- **Instant Dossier Generation:** Structured requirements for all active job positions are parsed once and pre-cached.
- **Zero Redundancy:** When evaluating multiple candidates against the same job position, the system reuses pre-cached requirements, delivering instant results without duplicate AI processing.

### 5.7 Automated Background Evaluation Queue
- **Non-Blocking Submissions:** Referral submission is instantaneous; candidates do not wait for AI evaluation to finish before receiving their submission confirmation.
- **Sequential Pacing:** Background jobs are processed in a sequential queue with an enforced **4.0-second delay** between successive resumes to respect API capacity and ensure system stability.
- **Intelligent Backoff:** If high traffic occurs, the queue automatically backs off for 20 seconds before resuming without human intervention.

### 5.8 Pre-Submission JEV Relevance Pre-Screening
- **Relevance Scoring:** Analyzes candidate resume alignment against job requirements prior to final submission.
- **Early Warning:** Alerts employees if a candidate has very low relevance for a chosen position, suggesting alternative openings before submission.

---

## 6. Historical Candidate RAG Recommendations Features

### 6.1 Passive Talent Discovery for New Positions
When a new job position is opened or synchronized from CATS ATS, HR recruiters can discover qualified passive candidates who were previously referred for earlier positions:
- **Automated Archive Indexing:** Extracts profile summaries and credentials from past candidates.
- **Surfacing Passive Talent:** Matches past candidates against new requisition criteria, identifying candidates who may be an ideal fit for new roles.

### 6.2 Semantic Similarity Scoring & Profile Retrieval
- **Deep Semantic Matching:** Leverages AI embeddings to understand candidate qualifications beyond exact keyword matches (e.g., recognizing that *FastAPI* relates to *Python Backend Development*).
- **Match Cutoff Threshold:** Filters recommendations using a similarity threshold (minimum 45% alignment), ensuring recruiters only review high-probability candidates.

### 6.3 Candidate Comparison & Match Rationale
- **Historical Comparison View:** Recruiters can view a side-by-side comparison explaining why an archived candidate is recommended for the new opening.
- **Original Submission Context:** Displays the candidate's original referring employee, submission date, and past status.

---

## 7. Automated CATS Careers ATS Synchronization Features

### 7.1 Live Requisition Ingestion
- **Automated Source:** Continuously scrapes the live [Tangentia CATS Careers Portal](https://tangentia.catsone.com/careers/9463-General).
- **Comprehensive Coverage:** Ingests openings across all Tangentia global regions (India, Canada, United States).

### 7.2 Automated 6-Hour Background Sync
- **Scheduled Synchronization:** An internal cron job runs automatically every 6 hours without requiring human initiation.
- **Continuous Alignment:** Newly posted openings on CATS ATS automatically appear on the portal's job board, while closed positions are retired.

### 7.3 Intelligent 1–2 Sentence Job Summarizer
- **Boilerplate Stripping:** Removes redundant corporate legal text, application instructions, and formatting noise from ATS descriptions.
- **Crisp Executive Summaries:** Generates a concise 1–2 sentence overview for each position, enabling employees to understand role requirements at a glance.

### 7.4 Automated Taxonomy Classification
- **Department Categorization:** Automatically maps requisitions into standardized departments (*Intelligent Automation*, *Cloud & Integration*, *Data & Analytics*, *Finance & Enterprise*, *Global Sales*, *Engineering*).
- **Employment Type Classification:** Identifies whether a role is *Full-time*, *Contract*, or *Internship*.

### 7.5 Deterministic Requisition Management
- **Deterministic Job Identifiers:** Requisitions synchronize using predictable IDs (`cats-{job_id}`).
- **Idempotent Updates:** Sync runs update existing positions cleanly without duplicating listings or breaking existing referral links.

---

## 8. Data Privacy, Security & User Experience Highlights

### 8.1 Public vs Protected Boundary
- **Public Employee Workspace:** Employees access job listings, submit referrals, and track their submissions without needing to manage separate user credentials or passwords.
- **Protected HR Hub:** Access to candidate databases, notes, AI dossiers, and ATS sync controls requires corporate authentication.

### 8.2 Zero-Trust Document Streaming
- **Hidden Cloud Storage:** Raw storage bucket URLs, cloud storage keys, and connection strings are strictly concealed on the server.
- **Authenticated Proxy:** All resume downloads are proxied through an authenticated backend stream that validates user permissions before transmitting file bytes.

### 8.3 Consent Tracking & Regulatory Compliance
- **GDPR & Privacy Compliance:** Referrals mandate explicit candidate consent confirmation before submission.
- **Full Deletion Audit:** Deleting a candidate purges all associated resume files, notes, and AI match dossiers completely.

### 8.4 User Experience Reliability Controls
- **4-Second Authentication Watchdog:** If corporate SSO verification encounters network latency, an automated 4-second watchdog prevents the interface from hanging on loading screens.
- **25-Second Network Timeout:** All network requests enforce a 25-second timeout with informative error notifications.
- **Tangentia 2026 Brand Aesthetics:** Features official Tangentia corporate branding, dark-mode design tokens, responsive mobile views, and smooth micro-animations.

---

*Tangentia Employee Referral Portal — Features Specification Document v2.0.0*  
*Document finalized: October 2026*
