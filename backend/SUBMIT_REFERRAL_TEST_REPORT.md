# Tangentia Referral Portal - Submit Referral & Extraction Pipeline Test Report

**Execution Date**: 2026-09-22 18:57:08 UTC  
**Scope**: Full end-to-end testing of the Referral Submission Flow:
1. Complete purge of existing referrals across all data stores.
2. Ingestion of all 18 CVs via `POST /api/referrals/extract-cv` (autofill preview).
3. Candidate email vs. Employee email validation verification:
   - Candidate (referral) email: **Any standard email permitted (e.g., `@gmail.com`, `@yahoo.com`) — DOES NOT require `@tangentia.com`**.
   - Referring employee email: **Must be corporate `@tangentia.com`**.
4. Creation of referrals via `POST /api/referrals` (multipart form + CV file upload).
5. CV Intelligence profile parsing and match evaluation across active positions.
6. Persistence verification across SQLite, Excel, and Mock SharePoint storage.

---

## 1. Zero-State Purge Verification

| Data Store | Entities Cleared | Post-Purge Count | Verification Endpoint |
|---|---|---|---|
| **Live FastAPI / SQLite** | `referrals`, `referral_status_history`, `hr_notes` | **0** | `GET /api/referrals` &rarr; `[]` (0 records) |
| **Microsoft Excel** | `tangentia_referrals.xlsx` (Referrals & StatusHistory) | **0** | Worksheet inspected (header preserved) |
| **Mock SharePoint** | `/storage/mock_sharepoint/2026` & `_index.json` | **0** | Folder cleaned, index reset to `{}` |
| **CV Intelligence DB** | `candidate_profiles`, `job_matches` | **0** | SQLite query confirmed 0 records |

---

## 2. Extraction & Referral Submission Results (18/18 CVs)

| # | Referral Number | Resume File | Candidate Name | Candidate (Referral) Email | Referring Employee Email | Autofill Status | Manual Fill Notice |
|---|---|---|---|---|---|---|---|
| 1 | `REF-2026-000001` | `APA Developer.docx` | Jassim Shaji | `jassim.shaji@example.com` | `vansh.rupesh@tangentia.com` | Name only | `⚠️ Cannot find email/phone in CV` |
| 2 | `REF-2026-000002` | `APA Developer.pdf` | Keerthi K | `keerthikrishnan3778@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 3 | `REF-2026-000003` | `Business Analyst -2.pdf` | Vinayak Chari | `vinayakrchari@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 4 | `REF-2026-000004` | `Business Analyst.pdf` | Ruchita Elekar | `ruchitaelekar05@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 5 | `REF-2026-000005` | `Program Director-Resume.pdf` | Ajinkya Birwadkar | `ajinkya.birwadkar@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 6 | `REF-2026-000006` | `Prompt Engineer.docx` | Aryan Verma | `aryan.verma@example.com` | `vansh.rupesh@tangentia.com` | Name only | `⚠️ Cannot find email/phone in CV` |
| 7 | `REF-2026-000007` | `Prompt Engineer2.docx` | Rohan Mehta | `rohan.mehta@example.com` | `vansh.rupesh@tangentia.com` | Name only | `⚠️ Cannot find email/phone in CV` |
| 8 | `REF-2026-000008` | `QA1.pdf` | B Anand | `anandbalakrishnan50@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 9 | `REF-2026-000009` | `QA2.pdf` | Abisha Rajesh | `abishadashlin@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 10 | `REF-2026-000010` | `QA3.pdf` | Balaji S | `balajis2998@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 11 | `REF-2026-000011` | `Scrum_Lead.docx` | Neha Kulkarni | `neha.kulkarni@example.com` | `vansh.rupesh@tangentia.com` | Missing all | `⚠️ Cannot find name/email/phone in CV` |
| 12 | `REF-2026-000012` | `Solution Architect - Lead.docx` | Siddharth Nair | `siddharth.nair@example.com` | `vansh.rupesh@tangentia.com` | Name only | `⚠️ Cannot find email/phone in CV` |
| 13 | `REF-2026-000013` | `Solution Architect.docx` | Mohamed Faheem Ashique | `faheemashique@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 14 | `REF-2026-000014` | `Support1.pdf` | Komal Kutre | `komalkutre2014@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 15 | `REF-2026-000015` | `Support2.docx` | Allen Manu Philip | `allen.philip@example.com` | `vansh.rupesh@tangentia.com` | Name only | `⚠️ Cannot find email/phone in CV` |
| 16 | `REF-2026-000016` | `Support3.pdf` | Virendra Salgaonkar | `virendrasalgaonkar777@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 17 | `REF-2026-000017` | `Tech Lead.docx` | Mohamed Faheem Ashique | `faheemashique@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |
| 18 | `REF-2026-000018` | `UI-UX Designer.docx` | Daryl Emmanuel Vaz | `darylemmanuel23@gmail.com` | `vansh.rupesh@tangentia.com` | **100% Autofilled** | None |

---

## 3. Email Domain Validation Verification

- **Referring Employee Email (`referred_by_email`)**:
  - Validated against `@tangentia.com`.
  - Non-tangentia employee emails (e.g. `user@gmail.com`) return `HTTP 400 Bad Request: Employee email must be an official @tangentia.com corporate email address.`
  - Successfully verified with `vansh.rupesh@tangentia.com`.
- **Candidate Referral Email (`candidate_email`)**:
  - **No corporate domain restriction enforced**.
  - Standard candidate personal email domains (e.g., `vinayakrchari@gmail.com`, `abishadashlin@gmail.com`, `komalkutre2014@gmail.com`) are fully accepted, stored in SQLite and written to Excel.

---

## 4. Final Data Store Verification

| Data Store | Expected Count | Verified Live Count | Status |
|---|---|---|---|
| **Live API (`GET /api/referrals`)** | 18 | **18** | **PASS** |
| **Excel Workbook (`tangentia_referrals.xlsx`)** | 18 | **18** | **PASS** |
| **Mock SharePoint Storage (`storage/mock_sharepoint/2026`)** | 18 | **18** | **PASS** |
| **Active Openings with Ranked Candidates** | 10 | **10** | **PASS** |
| **Total Candidates Evaluated by CV Intelligence** | 18 | **18** | **PASS** |
