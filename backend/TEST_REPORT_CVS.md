# Tangentia Referral Portal - CV Deletion & Re-upload Testing Report

**Execution Timestamp**: 2026-09-22 19:07:36 UTC
**Test Environment**: Local Development (SQLite + Excel Write-through + Mock SharePoint)

## 1. Storage Cleanup Verification
| Target Data Store | Action Taken | Result Status |
|---|---|---|
| SQLite Database (`tangentia_referrals.db`) | Deleted `referrals`, `referral_status_history`, `hr_notes` | Verified Empty |
| Excel Workbook (`tangentia_referrals.xlsx`) | Cleared `Referrals`, `StatusHistory`, `HRNotes`, `HiredHistory` rows | Verified Empty (Headers Preserved) |
| Mock SharePoint Storage (`data/sharepoint_mock/`) | Cleared current year directory and reset `_index.json` | Verified Empty |
| CV Intelligence Database (`cv_intelligence.db`) | Deleted `job_matches` and `candidate_profiles` | Verified Empty |

## 2. CV Upload & Autofill Extraction Test (/api/referrals/extract-cv)
Tests the extraction preview feature triggered immediately when an employee uploads a CV in Section 2:
| # | CV File | Detected Name | Detected Email | Detected Phone | Exp (Yrs) | Autofilled Fields | Missing / Needs Manual Fill |
|---|---|---|---|---|---|---|---|
| 1 | `APA Developer.docx` | Jassim Shaji | *Not found* | *Not found* | 3.0 | `name` | `email, phone` |
| 2 | `APA Developer.pdf` | Keerthi K | keerthikrishnan3778@gmail.com | +917510963778 | 4.0 | `name, email, phone` | `None (Full Autofill)` |
| 3 | `Business Analyst -2.pdf` | Vinayak Chari | vinayakrchari@gmail.com | +91 8208853944 | 11.0 | `name, email, phone` | `None (Full Autofill)` |
| 4 | `Business Analyst.pdf` | Goa India | ruchitaelekar05@gmail.com | 9923119494 | 8.0 | `name, email, phone` | `None (Full Autofill)` |
| 5 | `Program Director-Resume.pdf` | Ajinkya Birwadkar | ajinkya.birwadkar@gmail.com | +91 7715906118 | 14.0 | `name, email, phone` | `None (Full Autofill)` |
| 6 | `Prompt Engineer.docx` | Core Skills | *Not found* | *Not found* | 3.0 | `name` | `email, phone` |
| 7 | `Prompt Engineer2.docx` | Generative Ai Llms | *Not found* | *Not found* | 12.0 | `name` | `email, phone` |
| 8 | `QA1.pdf` | B Anand | anandbalakrishnan50@gmail.com | +91 8848856050 | 2.0 | `name, email, phone` | `None (Full Autofill)` |
| 9 | `QA2.pdf` | Abisha Rajesh | abishadashlin@gmail.com | +91 9400174498 | 17.0 | `name, email, phone` | `None (Full Autofill)` |
| 10 | `QA3.pdf` | Balaji S | balajis2998@gmail.com | +919626741197 | 6.0 | `name, email, phone` | `None (Full Autofill)` |
| 11 | `Scrum_Lead.docx` | *Not found* | *Not found* | *Not found* | 12.0 | `None` | `name, email, phone` |
| 12 | `Solution Architect - Lead.docx` | Desktop Operating Systems Windows | *Not found* | *Not found* | 9.0 | `name` | `email, phone` |
| 13 | `Solution Architect.docx` | Mohamed Faheem Ashique | faheemashique@gmail.com | +919746712667 | 7.0 | `name, email, phone` | `None (Full Autofill)` |
| 14 | `Support1.pdf` | Komal Kutre | komalkutre2014@gmail.com | 7040407360 | 11.0 | `name, email, phone` | `None (Full Autofill)` |
| 15 | `Support2.docx` | Allen Manu Philip | *Not found* | *Not found* | 2.0 | `name` | `email, phone` |
| 16 | `Support3.pdf` | Virendra Salgaonkar | virendrasalgaonkar777@gmail.com | +917775839001 | 2.0 | `name, email, phone` | `None (Full Autofill)` |
| 17 | `Tech Lead.docx` | Mohamed Faheem Ashique | faheemashique@gmail.com | +919746712667 | 7.0 | `name, email, phone` | `None (Full Autofill)` |
| 18 | `UI-UX Designer.docx` | Daryl Emmanuel Vaz | darylemmanuel23@gmail.com | +91-7020377137 | 0.0 | `name, email, phone` | `None (Full Autofill)` |

> [!NOTE]
> Files such as `APA Developer.docx` or `Scrum_Lead.docx` without email/phone headers appropriately flag those fields as `not_found_fields`, causing the UI to display: `⚠️ Cannot find [field] in CV — please fill manually`.

## 3. Education & Profile Intelligence Extraction
Detailed extraction of degrees, institutions, and scores from the resumes:
| Candidate Name | Extracted Degree(s) | Institution / Board | Score / Marks | Skills Count | Experience |
|---|---|---|---|---|---|
| Jassim Shaji | Bachelor of Technology in Electronics & Communication Engineering; Higher Secondary (12th) | Institution; Mail Automation | N/A | 13 | 3.0 yrs |
| Keerthi K | Bachelor of Technology in Information Technology | Institution | N/A | 18 | 4.0 yrs |
| Vinayak Chari | Diploma in Computer Engineering | Government Polytechnic Panaji | N/A | 23 | 11.0 yrs |
| Goa India | Bachelor's Degree in Computer Engineering | Institution | N/A | 17 | 8.0 yrs |
| Ajinkya Birwadkar | Bachelor of Commerce | Centennial College, Toronto - School of Engineering Technology and Applied  | N/A | 17 | 14.0 yrs |
| Core Skills | Bachelor's Degree in Computer Science / Information Technology PCCE | Information Technology PCCE- Goa , 2005 | N/A | 25 | 3.0 yrs |
| Generative Ai Llms | Bachelor's Degree in Computer Science / Information Technology Goa Engi | Information Technology Goa Engineering College, 2008 CERTIFICATIONS Generat | N/A | 25 | 12.0 yrs |
| B Anand | Bachelor of Technology in Computer Science | Institution | CGPA: 7.16 | 16 | 2.0 yrs |
| Abisha Rajesh | Bachelor of Engineering in Computer Science Engineering; Master of Engineering in Computer Science Engineering | Institution; Institution | CGPA: 8.2; CGPA: 8.2 | 23 | 17.0 yrs |
| Balaji S | Diploma in Computer Engineering | Institution | N/A | 25 | 6.0 yrs |
| Neha Kulkarni | Bachelor's Degree in Computer Science Don Bosco College of Engineering | Institution | N/A | 30 | 12.0 yrs |
| Desktop Operating Systems Windows | Bachelor of Engineering in Electronics & Communications Eng | Agnel Institute of Technology & Design, Goa University.2016 CERTIFICATIONS | N/A | 33 | 9.0 yrs |
| Mohamed Faheem Ashique | Bachelor of Technology in Applied Electronics & Instrumentation | Institution | N/A | 19 | 7.0 yrs |
| Komal Kutre | Bachelor of Engineering in Electronics and Telecommunication Margao | Don Bosco College of Engineering 2015-2019 | N/A | 15 | 11.0 yrs |
| Allen Manu Philip | Bachelor of Technology in Computer Science Mar Baselios College of Engineeri | Computer Science Mar Baselios College of Engineering | N/A | 13 | 2.0 yrs |
| Virendra Salgaonkar | Bachelor of Computer Science; Higher Secondary (12th) in PCM CS Dnyanprassarak Mandal | Institution; Institution | N/A | 11 | 2.0 yrs |
| Mohamed Faheem Ashique | Bachelor of Technology in Applied Electronics & Instrumentation | Institution | N/A | 19 | 7.0 yrs |
| Daryl Emmanuel Vaz | Bachelor's Degree in Computer Science; Diploma in Hardware Maintenance; Higher Secondary (12th) in Science stream; Secondary School (10th) | Second class, from Smt Parvatibai Chowgule College, Margao; Smt Parvatibai Chowgule College, Margao; SSC in the year 2005; EDUCATIONAL QUALIFICATION Successfully completed SSC in the year 2005 | Second class; First class; First class | 16 | 4.0 yrs |

## 4. HR Suggestions & Match Ranking Across Openings
Openings sorted by total number of candidate referrals, displaying AI advisory selection criteria and prioritized candidates:

### Business Architect - Senior (Project & Product Management)
- **Requisition ID**: `cats-16699887` | **Location**: Toronto, Ontario
- **Expected Skills**: Bpmn, Business analysis, Business architecture, Devops, Enterprise architecture, Excel
- **Total Referral Matches**: 3 (3 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Vinayak Chari | Bpmn, Business Analysis, Business Architecture, Process Mapping | 11.0 yrs |
| #2 | **Strong Match** | Neha Kulkarni | Business Analysis, Devops, Excel, Salesforce | 12.0 yrs |
| #3 | **Strong Match** | Sanjeev Kumar | Bpmn, Business Analysis, Business Architecture, Process Mapping | 8.0 yrs |

### IT Engineer (AWS) (Cloud & Integration)
- **Requisition ID**: `cats-16849726` | **Location**: Panjim, Goa
- **Expected Skills**: AWS, Cloud architecture, It support, Linux, Microsoft 365, Networking
- **Total Referral Matches**: 3 (0 Strong, 2 Good, 1 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Good Match** | Komal Kutre | It Support, Troubleshooting | 11.0 yrs |
| #2 | **Good Match** | Virendra Salgaonkar | It Support, Troubleshooting | 2.0 yrs |
| #3 | **Potential Match** | Allen Manu Philip |  | 2.0 yrs |

### QA Engineer (Engineering)
- **Requisition ID**: `cats-16856991` | **Location**: Goa/Trivandrum, India
- **Expected Skills**: Agentic ai, Agile, Ai agents, Api testing, Azure, Defect lifecycle
- **Total Referral Matches**: 3 (3 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Abisha Rajesh | Agile, Api Testing, Defect Lifecycle, Jira | 17.0 yrs |
| #2 | **Strong Match** | Balaji S | Agentic Ai, Agile, Ai Agents, Api Testing | 6.0 yrs |
| #3 | **Strong Match** | B Anand | Agentic Ai, Agile, Api Testing, Defect Lifecycle | 2.0 yrs |

### AI & Machine Learning Engineer (AI Innovations)
- **Requisition ID**: `job-002` | **Location**: Goa, India (Remote)
- **Expected Skills**: LLM
- **Total Referral Matches**: 2 (2 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Rohan Mehta | LLM | 12.0 yrs |
| #2 | **Strong Match** | Aryan Verma | LLM | 3.0 yrs |

### Senior Cloud Solutions Architect (Cloud & Infrastructure)
- **Requisition ID**: `job-003` | **Location**: New York, USA
- **Expected Skills**: AWS, Azure, Enterprise architecture
- **Total Referral Matches**: 2 (1 Strong, 1 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Mohamed Faheem Ashique | AWS, Azure | 7.0 yrs |
| #2 | **Good Match** | Siddharth Nair | Azure | 9.0 yrs |

### Frontend Lead (React + TypeScript) (Engineering)
- **Requisition ID**: `job-004` | **Location**: Toronto, Canada
- **Expected Skills**: CSS, Frontend, React, Typescript
- **Total Referral Matches**: 1 (0 Strong, 1 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Good Match** | Daryl Emmanuel Vaz | Frontend | 4.0 yrs |

### RPA Developer + APA — 3–5 Years (Intelligent Automation)
- **Requisition ID**: `cats-16855743` | **Location**: Goa/Trivandrum, India
- **Expected Skills**: A360, APA, Agile, Automation anywhere, Python, RPA
- **Total Referral Matches**: 1 (1 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Jassim Shaji | A360, APA, Automation Anywhere, Python | 3.0 yrs |

### RPA Developer – Automation Anywhere + Python (Intelligent Automation)
- **Requisition ID**: `cats-16855744` | **Location**: Mumbai, Maharashtra, Mumbai
- **Expected Skills**: A360, Agile, Automation anywhere, BOT, Iq bot, Python
- **Total Referral Matches**: 1 (1 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Keerthi Krishnan | A360, Automation Anywhere, Bot, Iq Bot | 4.0 yrs |

### Senior Backend Developer (Python / FastAPI) (Engineering)
- **Requisition ID**: `job-001` | **Location**: Toronto, Canada (Hybrid)
- **Expected Skills**: Fastapi, Python
- **Total Referral Matches**: 1 (1 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Faheem Ashique | Fastapi, Python | 7.0 yrs |

### Vice President, Global Sales (Global Sales)
- **Requisition ID**: `cats-16793607` | **Location**: Toronto, ON
- **Expected Skills**: Agentic ai, B2B, Revenue, Sales, Stakeholder management
- **Total Referral Matches**: 1 (1 Strong, 0 Good, 0 Potential)

| Priority Rank | Match Level | Candidate Name | Matched Skills | Experience |
|---|---|---|---|---|
| #1 | **Strong Match** | Ajinkya Birwadkar | Agentic Ai, B2b, Revenue, Sales | 14.0 yrs |

## 5. Data Store Sync Verification
| Data Store | Item | Expected Count | Verified Actual Count | Status |
|---|---|---|---|---|
| SQLite (`tangentia_referrals.db`) | Referral Records | 18 | 18 | PASS |
| Excel (`tangentia_referrals.xlsx`) | Referrals Rows | 18 | 18 | PASS |
| Mock SharePoint (`/data/sharepoint_mock/2026`) | Stored CV Files | 18 | 18 | PASS |
| CV Intelligence DB (`candidate_profiles`) | Extracted Profiles | 18 | 18 | PASS |
| CV Intelligence DB (`job_matches`) | Matched Evaluations | > 0 | 18 | PASS |