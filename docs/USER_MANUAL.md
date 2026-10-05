# Tangentia Employee Referral Portal — User Manual & Operations Guide
**Document Reference:** UM-TERP-2026-V2.1  
**Version:** 2.1.0  
**Effective Date:** October 2026  
**Classification:** Internal — Employee & HR Administrator User Guide  
**Product:** Tangentia Employee Referral Portal  

---

## 📑 Table of Contents

1. [Welcome & System Overview](#1-welcome--system-overview)
2. [Employee Guide — Public Referral Workspace](#2-employee-guide--public-referral-workspace)
   - 2.1 [Discovering Open Requisitions](#21-discovering-open-requisitions)
   - 2.2 [Step-by-Step: Submitting a Candidate Referral](#22-step-by-step-submitting-a-candidate-referral)
   - 2.3 [AI CV Auto-Fill & Manual Review](#23-ai-cv-auto-fill--manual-review)
   - 2.4 [Handling the 180-Day Duplicate Warning Modal](#24-handling-the-180-day-duplicate-warning-modal)
   - 2.5 [Tracking Your Portfolio in "My Referrals"](#25-tracking-your-portfolio-in-my-referrals)
   - 2.6 [Voluntarily Withdrawing a Candidate](#26-voluntarily-withdrawing-a-candidate)
   - 2.7 [Viewing Hired History & Excel Export](#27-viewing-hired-history--excel-export)
3. [HR Administrator & Recruiter Guide — Protected Hub](#3-hr-administrator--recruiter-guide--protected-hub)
   - 3.1 [Signing In to the HR Administration Hub](#31-signing-in-to-the-hr-administration-hub)
   - 3.2 [Recruitment Dashboard & Executive KPIs](#32-recruitment-dashboard--executive-kpis)
   - 3.3 [Master Candidate Database & Search Filters](#33-master-candidate-database--search-filters)
   - 3.4 [Progressing Candidate Statuses & Audit Trail](#34-progressing-candidate-statuses--audit-trail)
   - 3.5 [Writing Confidential Internal Recruiter Notes](#35-writing-confidential-internal-recruiter-notes)
   - 3.6 [Inspecting AI Candidate Intelligence Dossiers](#36-inspecting-ai-candidate-intelligence-dossiers)
   - 3.7 [Verifying Experience (REQ #1) & Education (REQ #2)](#37-verifying-experience-req-1--education-req-2)
   - 3.8 [Using the "Open in CATSOne" Deep Link](#38-using-the-open-in-catsone-deep-link)
   - 3.9 [Passive Talent Discovery via Historical RAG Search](#39-passive-talent-discovery-via-historical-rag-search)
   - 3.10 [Synchronizing CATS Careers ATS Job Postings](#310-synchronizing-cats-careers-ats-job-postings)
   - 3.11 [Exporting the Multi-Sheet Excel Ledger from Azure Blob](#311-exporting-the-multi-sheet-excel-ledger-from-azure-blob)
   - 3.12 [Permanent Candidate Cascade Purge (GDPR Compliance)](#312-permanent-candidate-cascade-purge-gdpr-compliance)
4. [Status Badge Reference & Color Codes](#4-status-badge-reference--color-codes)
5. [Frequently Asked Questions (FAQ) & Troubleshooting](#5-frequently-asked-questions-faq--troubleshooting)

---

## 1. Welcome & System Overview

Welcome to the **Tangentia Employee Referral Portal**! This portal enables Tangentia team members across India, the United States, and Canada to recommend exceptional professional contacts for open positions, track their candidate's interview progress, and celebrate colleagues who join our organization.

### Key Highlights
- **Zero-Friction Submission:** Employees submit candidate referrals without any password barriers or SSO log-ins.
- **AI CV Auto-Fill:** Uploading a candidate resume (.pdf or .docx) automatically fills candidate contact details, experience, and core skills in seconds.
- **Fairness & Duplicate Protection:** Instant duplicate alerts protect referral ownership within a 180-day window.
- **HR Intelligence:** HR recruiters evaluate candidates with deterministic AI dossiers verifying work experience and degree requirements with direct factual citations.
- **Enterprise Persistence:** Every submission, note, and status progression is preserved in an audit-ready Microsoft Excel ledger stored in Azure Blob Storage.

---

## 2. Employee Guide — Public Referral Workspace

### 2.1 Discovering Open Requisitions
1. Open the portal URL in your web browser.
2. Navigate to **Job Openings** from the top navigation bar.
3. Browse active opportunities categorized across Tangentia's business units:
   - *Intelligent Automation*
   - *Cloud & Integration*
   - *Data & Analytics*
   - *Finance & Enterprise Solutions*
   - *Global Sales & Marketing*
   - *Engineering & Quality Assurance*
4. Use the search bar to filter by title, location (e.g. *Goa, Toronto, Pune, Remote*), or employment type (*Full-time, Contract*).
5. Openings marked with the **`CATS ATS`** badge represent live openings synchronized directly from Tangentia's careers ATS.
6. Click **"View Details"** to read the full position summary, key responsibilities, and required qualifications.

---

### 2.2 Step-by-Step: Submitting a Candidate Referral

```
┌────────────────────────────────────────────────────────────────────────┐
│                        4-Step Submission Flow                          │
├───────────────────┬───────────────────┬───────────────────┬────────────┤
│ 1. Choose Opening │ 2. Upload CV      │ 3. Review Fields  │ 4. Submit  │
│ Select vacancy    │ Drag & drop file  │ AI auto-populates │ Instant ID │
│ from catalog      │ (.pdf or .docx)   │ name, email, phone│ generated  │
└───────────────────┴───────────────────┴───────────────────┴────────────┘
```

1. Click **"Refer Candidate"** on your chosen job card (or click **"Submit Referral"** in the navigation bar).
2. **Select Requisition:** Confirm the target job title from the dropdown.
3. **Upload Resume:** Drag and drop the candidate's resume (`.pdf` or `.docx`, max 10MB) into the dropzone.
4. **Instant Auto-Fill:** The system parses the document in 2–3 seconds and automatically populates:
   - Candidate Full Name
   - Candidate Email Address
   - Candidate Phone Number
   - Years of Professional Experience
   - Primary Technical Skills & Summary
5. **Review & Confirm:** Inspect the auto-filled fields and make corrections if necessary.
6. **Enter Your Corporate Email:** Enter your official `@tangentia.com` email address so recruitment can credit your referral.
7. **Add an Optional Note:** Share personal context (e.g., *"Worked with Rahul for 3 years at our previous firm; exceptional Python architect"*).
8. **Candidate Consent:** Check the required consent box confirming the candidate agreed to be referred.
9. Click **"Submit Referral"**.

---

### 2.3 AI CV Auto-Fill & Manual Review
- **Supported Formats:** Modern `.pdf` and `.docx` files.
- **Unusual Formatting Notice:** If a candidate's CV uses graphic image text, unusual font glyphs, or omits contact details, the portal will display a clear banner:
  > `⚠️ Cannot find email/phone in CV. Please fill in manually.`
- Simply type in the candidate's email and phone number to complete the submission.

---

### 2.4 Handling the 180-Day Duplicate Warning Modal
To ensure fairness and prevent multiple employees referring the same contact simultaneously, the portal performs a real-time pre-submission duplicate check:

- **What triggers the modal?**
  - An exact candidate email match.
  - A normalized international phone number match (E.164).
  - The same candidate name referred for the same role.
- **Active Pipeline Referral ($\le$ 180 Days):**
  - If the candidate was referred within the last 6 months and is still active in the hiring pipeline, a warning modal will appear detailing the existing submission date and current status.
  - *Action:* The submission will be safely halted to protect the original referrer's ownership.
- **Expired Past Referral (> 180 Days):**
  - If the candidate was referred more than 180 days ago and the prior process concluded, you are free to proceed with a fresh referral.

---

### 2.5 Tracking Your Portfolio in "My Referrals"
1. Click **"My Referrals"** in the top navigation bar.
2. Enter your `@tangentia.com` email address to retrieve your personal submission portfolio.
3. The table displays:
   - **Referral Number:** Official tracking identifier (e.g. `REF-2026-000014`).
   - **Candidate Name & Contact.**
   - **Target Position.**
   - **Submission Date.**
   - **Live Status Radar Badge:** Displays current status (`Submitted`, `Under Review`, `Shortlisted`, `Interview`, `Selected`, `Hired`, `Rejected`, `Withdrawn`).
4. **Download Resume:** Click the download icon in any row to download the original resume you submitted.

---

### 2.6 Voluntarily Withdrawing a Candidate
If your candidate accepts an offer elsewhere, relocates, or requests withdrawal from consideration:
1. In your **"My Referrals"** table, click the **"Withdraw"** button next to their record.
2. A withdrawal modal will appear prompting for an optional rationale (e.g. *"Candidate accepted another role"*).
3. Confirm the action. The referral will move to `Withdrawn` status and notify the recruitment team immediately.

---

### 2.7 Viewing Hired History & Excel Export
1. Click **"Hired History"** in the navigation bar.
2. Celebrate colleagues who successfully joined Tangentia through employee referrals.
3. Click **"Export to Excel"** to download a clean, styled spreadsheet of hired candidates.

---

## 3. HR Administrator & Recruiter Guide — Protected Hub

### 3.1 Signing In to the HR Administration Hub
1. Click **"HR Sign In"** in the upper right corner of the navigation header.
2. Enter your corporate credentials:
   - **Email:** Your `@tangentia.com` account.
   - **Password:** Your assigned HR portal password.
3. Click **"Sign In"**. Upon authentication, a secure 7-day JWT session is established, and the administrative console appears.
4. *Note:* HR accounts are pre-configured and synchronized from the `Users` sheet in `Tangentia_Referrals.xlsx`.

---

### 3.2 Recruitment Dashboard & Executive KPIs
Upon logging in, the **HR Dashboard** presents:
- **KPI Metrics:** Total Submissions, Active Pipeline, Candidates in Interview, Total Hired, and Overall Funnel Conversion Rate.
- **Recruitment Funnel:** Visual stage-by-stage drop-off analysis.
- **Departmental Distribution:** Referral volume broken down by business unit.
- **Top Referrer Leaderboard:** Recognition board displaying team members with the highest referral counts and hires.

---

### 3.3 Master Candidate Database & Search Filters
1. Click **"All Referrals"** in the HR menu.
2. Access the comprehensive candidate ledger featuring:
   - **Global Search:** Search by candidate name, email, phone, or job title.
   - **Status Filter:** Filter by active stages (`Submitted`, `Under Review`, `Interview`, etc.).
   - **Department Filter:** Filter by business vertical.
   - **Date Filter:** Restrict to specific submission windows.
3. Click on any candidate row to open their **Candidate Profile Drawer**.

---

### 3.4 Progressing Candidate Statuses & Audit Trail
1. In the Candidate Profile Drawer (or Candidate Table), locate the **Status Dropdown**.
2. Select the candidate's new recruitment stage:
   - `Submitted` $\rightarrow$ `Under Review` $\rightarrow$ `Shortlisted` $\rightarrow$ `Interview` $\rightarrow$ `Selected` $\rightarrow$ `Hired`
3. **Mandatory Rejection Note:** If marking a candidate as `Rejected`, a modal will require a brief rejection reason (e.g., *"Insufficient hands-on experience with Apache Spark"*).
4. **Automatic Hired Sync:** Transitioning to `Hired` automatically updates the candidate in the `HiredHistory` ledger.
5. **Audit Trail Inspection:** Scroll down in the drawer to view the complete chronological audit timeline detailing every past status change, timestamp, author name, and comments.

---

### 3.5 Writing Confidential Internal Recruiter Notes
1. Open the candidate's profile drawer and navigate to the **"Internal Notes"** tab.
2. Type your evaluation, compensation expectations, or committee feedback.
3. Click **"Add Note"**.
4. *Security Guarantee:* Internal recruiter notes are visible **only** to authenticated HR administrators. They are completely stripped from employee views and write directly to the `HRNotes` sheet in Azure Blob Storage.

---

### 3.6 Inspecting AI Candidate Intelligence Dossiers
1. In the candidate table or drawer, click **"View AI Dossier"** (or click the AI Fit Score pill).
2. The **Candidate Intelligence Dossier** modal opens, displaying:
   - **Overall Fit Score:** 0–100% composite score.
   - **Fit Level Pill:** `Excellent Match`, `Good Match`, `Moderate Match`, or `Low Match`.
   - **Key Strengths:** Executive summary of candidate credentials that strongly align with the requisition.
   - **Potential Gaps:** Explicit areas where the candidate falls short of requirements.
   - **Custom Interview Questions:** 3–5 role-specific technical questions generated to probe potential gaps during the interview.

---

### 3.7 Verifying Experience (REQ #1) & Education (REQ #2)
The portal enforces strict requirement evaluation hierarchy:
- **REQ #1: Total Professional Experience (Numeric Years)**
  - Inspected deterministically using pure-Python timeline calculation.
  - The card clearly displays: *Calculated Work Experience* vs *Required Minimum Experience*.
  - If experience is below the requirement, it is strictly flagged as `NOT_MET`.
- **REQ #2: Education & Academic Qualifications**
  - Checks required degrees (e.g. *B.Tech, B.E., M.S., MCA*).
- **Factual Evidence Citations:** Click on any requirement pill to view the exact verbatim quote extracted directly from the candidate's CV proving or disproving the requirement.

---

### 3.8 Using the "Open in CATSOne" Deep Link
When evaluating a candidate who applied for a position synchronized from Tangentia's primary recruitment portal:
1. Open the candidate dossier modal.
2. In the top-right header, click the blue **"Open in CATSOne"** button.
3. The system will open the live requisition on Tangentia CATS One (`tangentia.catsone.com/careers/9463-General/jobs/...`) in a new browser tab.

---

### 3.9 Passive Talent Discovery via Historical RAG Search
When a new job position is opened:
1. Navigate to **Requisition Manager** $\rightarrow$ select the position.
2. Click **"Passive Talent Recommendations (RAG)"**.
3. The system executes semantic vector similarity search against all archived candidates in the database.
4. Qualified candidates scoring above the 0.45 similarity threshold will be surfaced with their match rationale.
5. Click **"Consider for this Role"** to re-engage the candidate without waiting for new applications.

---

### 3.10 Synchronizing CATS Careers ATS Job Postings
While job postings synchronize automatically every 6 hours in the background:
1. Navigate to **Requisitions** in the HR menu.
2. Click the **"Sync CATS ATS"** button in the top action ribbon.
3. The system scrapes the live careers portal, extracts active requisitions, synthesizes summaries, and updates the database.
4. Click **"Preview Live ATS"** to view what is currently published on the CATS portal before synchronizing.

---

### 3.11 Exporting the Multi-Sheet Excel Ledger from Azure Blob
1. On the **All Referrals** page, click the green **"Export to Excel"** button.
2. The portal downloads the full styled `.xlsx` workbook (`Tangentia_Referrals.xlsx`) maintained in Azure Blob Storage.
3. The workbook contains 6 complete worksheets:
   - `Referrals` (All candidates, contacts, statuses, and CV pointers)
   - `JobPositions` (Openings, departments, locations, and summaries)
   - `StatusHistory` (Chronological transition logs)
   - `HRNotes` (Confidential evaluations)
   - `Users` (System users and accounts)
   - `HiredHistory` (Hired candidate archive)

---

### 3.12 Permanent Candidate Cascade Purge (GDPR Compliance)
If a candidate requests complete removal of their personal data under GDPR / privacy regulations:
1. Open the candidate's profile drawer in the HR Hub.
2. Scroll to the bottom and click **"Permanently Delete Candidate"** (Red Danger Zone).
3. Type the candidate's full name to confirm.
4. The system executes an atomic 5-stage purge:
   - Removes database record.
   - Clears status timeline and HR notes.
   - Clears evaluation dossiers from `cv_intelligence.db`.
   - Deletes original resume from Azure Blob Storage (`referral-cvs`).
   - Removes matching rows across all sheets in `Tangentia_Referrals.xlsx`.

---

## 4. Status Badge Reference & Color Codes

| Status | Badge Color | Meaning & Next Action |
|:---|:---:|:---|
| **`Submitted`** | Blue | Candidate referred; pending initial recruiter review. |
| **`Under Review`** | Amber / Yellow | Recruiter is reviewing the CV and AI intelligence dossier. |
| **`Shortlisted`** | Indigo | Candidate passed screening; shared with hiring manager. |
| **`Interview`** | Purple | Candidate actively in technical or cultural interview loops. |
| **`Selected`** | Teal | Candidate cleared all interviews; offer letter being prepared. |
| **`Hired`** | Emerald Green | Candidate accepted offer and onboarded. Copied to Hired History. |
| **`Rejected`** | Crimson Red | Candidate not moving forward (rationale logged in audit trail). |
| **`Withdrawn`** | Slate Gray | Referral voluntarily withdrawn by the referring employee. |
| **`Archived`** | Cool Gray | Candidate preserved for future historical RAG retrieval. |

---

## 5. Frequently Asked Questions (FAQ) & Troubleshooting

### For Employees

**Q: Do I need a login or password to refer a friend?**  
*A:* No. The Employee Workspace is completely frictionless. Simply enter your `@tangentia.com` email address when submitting.

**Q: What file types and sizes are supported for resumes?**  
*A:* PDF (`.pdf`) and Word documents (`.docx`) up to 10MB in size.

**Q: Why did I get a duplicate warning when submitting?**  
*A:* If the candidate was already referred within the last 180 days and is active in the recruitment process, the portal protects the original employee's referral. If the prior referral was more than 180 days ago, you can submit cleanly.

**Q: Can I refer someone if their CV is missing their phone number?**  
*A:* Yes! The AI will auto-fill whatever it discovers and highlight missing fields. Simply type in the missing phone number manually before clicking submit.

---

### For HR Administrators

**Q: Where are the uploaded resumes and Excel file stored?**  
*A:* All candidate resumes are archived in the `referral-cvs` Azure Blob Storage container. The multi-sheet audit ledger (`Tangentia_Referrals.xlsx`) resides in the `referral-data` container and is updated write-through on every mutation.

**Q: Can employees see my confidential recruiter notes?**  
*A:* Absolutely not. Internal recruiter notes are strictly role-gated on the backend and are completely stripped from all employee APIs and views.

**Q: Why does the AI Dossier take a few seconds to appear for newly submitted candidates?**  
*A:* The background AI evaluation worker operates with a sequential 4.0-second delay between resumes to ensure strict compliance with Google Gemini API rate limits and prevent throttling.

**Q: Can I restore a candidate after clicking "Permanently Delete"?**  
*A:* No. Permanent deletion is an irreversible cascade purge designed to fulfill GDPR "Right to be Forgotten" requirements.

---

*Tangentia Employee Referral Portal — User Manual v2.1.0*  
*Document finalized: October 2026*
