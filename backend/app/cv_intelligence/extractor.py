import os
import re
import json
import time
import logging
from typing import Optional
from pydantic import ValidationError
from app.config import settings
from app.cv_intelligence.schemas import CandidateProfileExtraction
from app.cv_intelligence.matcher import STANDARD_SKILL_KEYWORDS, canonicalize_skill

logger = logging.getLogger("cv_intelligence")


class ExtractionServiceError(Exception):
    """Raised when CV extraction via Gemini or provider fails."""
    pass


EXTRACTION_SYSTEM_PROMPT = """
You are an expert HR assistant extracting structured candidate profile information from a CV/resume.
Extract ONLY factual information explicitly present in the provided CV text.

CRITICAL RULES FOR ACCURACY:
1. "candidate_name": Must be the real person's full human name (e.g. "Ruchita Elekar", "Ajinkya Birwadkar", "Jassim Shaji").
   - STRICTLY FORBIDDEN as candidate_name: Do NOT extract section headers (e.g. "CORE COMPETENCIES", "PROFESSIONAL SUMMARY", "TECHNICAL SKILLS", "EDUCATION", "REPRESENTATIVE"), job titles (e.g. "SCRUM LEAD", "PROMPT ENGINEER", "SOFTWARE DEVELOPER", "BUSINESS ANALYST"), email addresses, or company names.
   - If no valid human name is found in the text, set candidate_name to null.

2. "years_of_experience": A float number representing total years of career/work experience.
   - Look for overall summary statements (e.g., "14+ years of experience" -> 14.0, "10+ Years" -> 10.0, "8+ years" -> 8.0, "4.5 years" -> 4.5).
   - Alternatively, compute total duration across employment history date ranges (e.g. 2013 to Present -> ~13.0 years).
   - Set to 0.0 if not discernible.

3. "skills": Comprehensive list of technical tools, programming languages, libraries, platforms, testing frameworks, methodologies, and business capabilities explicitly mentioned (e.g. ["Python", "FastAPI", "Automation Anywhere", "A360", "RPA", "BRD", "User Stories", "Agile", "Scrum", "SQL", "Docker"]).

4. "education": Array of educational qualifications. For each qualification:
   - "degree": Degree/qualification title (e.g. "Bachelor of Technology in Computer Science", "B.E. Computer Science Engineering", "Diploma in Computer Engineering", "Bachelor of Commerce", "Higher Secondary (12th)").
   - "institution": College, university, polytechnic, institute, or school name (e.g. "Marian College of Engineering", "Don Bosco College of Engineering", "Goa College of Engineering", "Centennial College", "University of Pune", "Loyola High School"). Do NOT leave null if an institution is mentioned.
   - "graduation_year": Year of completion or duration string (e.g. "2024", "2018", "2015-2019", "2008").
   - "field_of_study": Major, specialization, or branch (e.g. "Computer Science", "Electronics & Communication", "Information Technology").
   - "grade_or_score": CGPA, grade, percentage, or class if stated (e.g. "CGPA: 8.2", "First Class", "7.16 CGPA").
   - Note: Do NOT classify technical certifications (e.g. "Automation Anywhere Master RPA", "AWS Certified", "PMI Generative AI") as academic education; place those under "certifications".

5. "experience": array of objects with company, job_title, duration, and list of responsibilities.
6. "projects": array of objects with name, description, and technologies.
7. "certifications": array of objects with name, issuer, and year.
8. Return strictly valid JSON matching the required schema.
"""

NAME_BLACKLIST = {
    "core competencies", "professional summary", "technical skills", "work experience",
    "professional experience", "representative", "representative 4", "education",
    "certifications", "projects", "profile", "contact", "summary", "skills", "details",
    "scrum lead", "prompt engineer", "junior prompt engineer", "software developer",
    "solutions architect", "solution architect", "senior qa engineer", "qa engineer",
    "business analyst", "head of pmo", "program director", "tech lead", "ui/ux designer",
    "ui-ux designer", "it engineer", "rpa developer", "curriculum vitae", "resume",
    "address", "experience", "qualifications", "personal details", "declaration",
    "career objective", "job profile", "project experience", "technical profile"
}


NON_NAME_WORDS = {
    "competencies", "summary", "representative", "engineer", "developer", "architect",
    "analyst", "curriculum", "resume", "systems", "system", "windows", "desktop",
    "operating", "core", "skills", "skill", "generative", "prompt", "engineering",
    "domains", "marketing", "page", "contact", "address", "phone", "email", "profile",
    "lead", "scrum", "india", "usa", "canada", "goa", "mumbai", "kozhikode", "vadakara",
    "kerala", "toronto", "calicut", "chandrapur", "nagpur", "panaji", "trivandrum",
    "delhi", "bangalore", "bengaluru", "maharashtra", "flat", "bldg", "apts", "dob",
    "nationality", "indian", "overview", "experience", "education", "certifications",
    "linkedin", "github", "twitter", "website", "jan", "feb", "mar", "apr", "may",
    "jun", "jul", "aug", "sep", "oct", "nov", "dec", "models", "model", "language",
    "large", "retrieval", "knowledge", "rag", "llm", "llms", "ai",
    "requirements", "uat", "structured", "output", "generation", "testing",
    "design", "designer", "automation", "intelligent", "solutions", "solution",
    "business", "analysis", "rpa", "process", "improvement", "operations", "operation",
    "change", "it", "web", "technologies", "technology", "risk", "controls", "control",
    "stakeholder", "leadership", "communication", "making", "decision"
}


def is_valid_human_name(name_candidate: str) -> bool:
    """Validate that candidate name looks like a legitimate human name."""
    if not name_candidate or not name_candidate.strip():
        return False
    cleaned = name_candidate.strip()
    lower = cleaned.lower()

    if lower in NAME_BLACKLIST:
        return False

    # Check against non-name keywords
    words = cleaned.split()
    if not (1 <= len(words) <= 4):
        return False

    word_lowers = [w.lower().rstrip(".,") for w in words]
    if any(wl in NON_NAME_WORDS for wl in word_lowers):
        return False

    if any(b in lower for b in ["competencies", "summary", "representative", "engineer", "developer", "architect", "analyst", "curriculum", "resume", "operating systems"]):
        return False

    # Must not contain email or URL characters
    if "@" in cleaned or "http" in lower or ".com" in lower or ".in" in lower:
        return False

    # Must not contain digits
    if re.search(r"\d", cleaned):
        return False

    # Length check
    if len(cleaned) < 3 or len(cleaned) > 40:
        return False

    # Each word must be mostly letters
    for w in words:
        if not re.match(r"^[A-Za-z.']+$", w):
            return False

    return True


def heuristic_cv_extract(cv_text: str) -> CandidateProfileExtraction:
    """
    Rule-based heuristic extractor used as an ultra-reliable fallback
    if the external LLM API is temporarily unavailable (e.g. 503 spikes or rate limits).
    """
    lines = [line.strip() for line in cv_text.split("\n") if line.strip()]

    # 1. Candidate Name Detection
    candidate_name = None
    for line in lines[:15]:
        cleaned = re.sub(r"[^A-Za-z\s.'-]", "", line).strip()
        # Remove single letters prefix like 'KK'
        if cleaned.startswith("KK ") or cleaned == "KK":
            cleaned = cleaned[3:].strip()
        if is_valid_human_name(cleaned):
            candidate_name = " ".join(w.capitalize() for w in cleaned.split())
            break

    # If still not found, search for all-caps full names anywhere in the top 30 lines
    if not candidate_name:
        for line in lines[:30]:
            cleaned = line.strip()
            if cleaned.isupper() and is_valid_human_name(cleaned):
                candidate_name = " ".join(w.capitalize() for w in cleaned.split())
                break

    # 2. Email
    email = None
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", cv_text)
    if email_match:
        email = email_match.group(0).strip()

    # 3. Phone
    phone = None
    phone_match = re.search(r"(?:\+?\d{1,3}[\s-]?)?\(?\d{2,5}\)?[\s-]?\d{3,5}[\s-]?\d{3,5}", cv_text)
    if phone_match and len(phone_match.group(0).strip()) >= 8:
        phone = phone_match.group(0).strip()

    # 4. URLs
    linkedin_url = None
    li_match = re.search(r"https?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+", cv_text)
    if li_match:
        linkedin_url = li_match.group(0)

    github_url = None
    gh_match = re.search(r"https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+", cv_text)
    if gh_match:
        github_url = gh_match.group(0)

    # 5. Years of Experience Detection
    years_exp = 0.0

    # Pattern A: Explicit summary mentions (e.g. "14+ years", "10+ Years", "8 years of IT")
    exp_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?", cv_text, re.IGNORECASE)
    if exp_matches:
        try:
            candidates = [float(m) for m in exp_matches if 0.5 <= float(m) <= 35.0]
            if candidates:
                years_exp = max(candidates)
        except Exception:
            years_exp = 0.0

    # Pattern B: Parse employment date ranges (e.g. "2013 - Present" -> ~13.0 yrs)
    date_ranges = re.findall(r"(?:19|20)\d{2}\s*[-–to]\s*(?:present|current|till date|(?:19|20)\d{2})", cv_text, re.IGNORECASE)
    if date_ranges:
        earliest_year = 9999
        for dr in date_ranges:
            m_year = re.search(r"((?:19|20)\d{2})", dr)
            if m_year:
                earliest_year = min(earliest_year, int(m_year.group(1)))
        if earliest_year < 9999:
            calculated_exp = float(max(0, 2026 - earliest_year))
            if calculated_exp > years_exp and calculated_exp <= 35.0:
                years_exp = calculated_exp

    # 6. Deep Skills Extraction
    skills_found = set()
    lower_cv = cv_text.lower()
    for kw in STANDARD_SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, lower_cv):
            skills_found.add(canonicalize_skill(kw))

    # 7. Robust Section-Aware Extractors for Education, Experience, Projects, Certifications
    from app.cv_intelligence.schemas import EducationItem, ExperienceItem, ProjectItem, CertificationItem

    education_items = [EducationItem.model_validate(e) if isinstance(e, dict) else e for e in extract_education_from_cv(cv_text)]
    experience_items = [ExperienceItem.model_validate(exp) if isinstance(exp, dict) else exp for exp in extract_experience_from_cv(cv_text)]
    project_items = [ProjectItem.model_validate(p) if isinstance(p, dict) else p for p in extract_projects_from_cv(cv_text)]
    cert_items = [CertificationItem.model_validate(c) if isinstance(c, dict) else c for c in extract_certifications_from_cv(cv_text)]

    return CandidateProfileExtraction(
        candidate_name=candidate_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        years_of_experience=years_exp,
        skills=sorted(list(skills_found)),
        education=education_items,
        experience=experience_items,
        projects=project_items,
        certifications=cert_items,
    )


def extract_experience_from_cv(raw_text: str) -> list:
    """
    Section-aware heuristic extractor for work experience entries.
    Identifies job titles, employers, date ranges, and bullet point responsibilities.
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    exp_start = None
    exp_end = None
    for i, line in enumerate(lines):
        clean = line.strip().strip(":").upper()
        if clean in [
            "EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE",
            "EMPLOYMENT HISTORY", "WORK HISTORY", "CAREER HISTORY",
            "RELEVANT EXPERIENCE", "PROFESSIONAL BACKGROUND"
        ]:
            exp_start = i
            break

    if exp_start is None:
        for i, line in enumerate(lines):
            clean = line.strip().strip(":").upper()
            if any(clean.startswith(h) for h in ["EXPERIENCE", "WORK EXPERIENCE", "PROFESSIONAL EXPERIENCE"]):
                exp_start = i
                break

    if exp_start is None:
        return []

    for j in range(exp_start + 1, min(len(lines), exp_start + 80)):
        clean_next = lines[j].strip().strip(":").upper()
        if any(clean_next.startswith(h) for h in [
            "EDUCATION", "ACADEMIC", "PROJECTS", "KEY PROJECTS", "SKILLS",
            "TECHNICAL SKILLS", "CERTIFICATIONS", "CERTIFICATES", "DECLARATION",
            "LANGUAGES", "STRENGTHS", "PERSONAL DETAILS", "ACHIEVEMENTS"
        ]):
            exp_end = j
            break

    exp_lines = lines[exp_start + 1: exp_end if exp_end else exp_start + 50]
    if not exp_lines:
        return []

    date_pattern = re.compile(
        r"\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2}/\d{2,4})?\s*(?:19|20)\d{2}\s*[-–to\s]+\s*(?:Present|Current|Till Date|(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?|\d{1,2}/\d{2,4})?\s*(?:19|20)\d{2})",
        re.IGNORECASE
    )

    items = []
    current_entry = None

    for line in exp_lines:
        date_match = date_pattern.search(line)
        is_bullet = line.startswith(("-", "•", "*", "–", "—", "▪", "▫", ">")) or bool(re.match(r"^\d+\.\s+", line))

        if date_match and not is_bullet:
            if current_entry:
                items.append(current_entry)

            dur = date_match.group(0).strip()
            rest = (line[:date_match.start()] + " " + line[date_match.end():]).strip(" |,-–()")
            parts = [p.strip() for p in re.split(r"[-–|@]|(?:at\s+)", rest) if p.strip()]
            job_title = parts[0] if parts else "Role"
            company = parts[1] if len(parts) > 1 else None

            current_entry = {
                "job_title": job_title,
                "company": company,
                "duration": dur,
                "responsibilities": []
            }
        elif is_bullet:
            cleaned_bullet = re.sub(r"^[-•*–—▪▫>\d.]+\s*", "", line).strip()
            if cleaned_bullet:
                if not current_entry:
                    current_entry = {
                        "job_title": "Professional Experience",
                        "company": None,
                        "duration": None,
                        "responsibilities": []
                    }
                current_entry["responsibilities"].append(cleaned_bullet[:250])
        else:
            if not current_entry or not current_entry.get("company"):
                parts = [p.strip() for p in re.split(r"[-–|@]|(?:at\s+)", line) if p.strip()]
                if len(parts) >= 2 and any(t in line.lower() for t in ["engineer", "developer", "architect", "lead", "analyst", "manager", "specialist", "consultant", "intern"]):
                    if current_entry and not current_entry.get("responsibilities"):
                        current_entry["job_title"] = parts[0]
                        current_entry["company"] = parts[1]
                    else:
                        if current_entry:
                            items.append(current_entry)
                        current_entry = {
                            "job_title": parts[0],
                            "company": parts[1],
                            "duration": None,
                            "responsibilities": []
                        }

    if current_entry:
        items.append(current_entry)

    valid_items = []
    for it in items:
        if it.get("job_title") or it.get("company") or it.get("responsibilities"):
            valid_items.append(it)
    return valid_items[:8]


def extract_projects_from_cv(raw_text: str) -> list:
    """
    Section-aware heuristic extractor for project items.
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    proj_start = None
    proj_end = None
    for i, line in enumerate(lines):
        clean = line.strip().strip(":").upper()
        if clean in [
            "PROJECTS", "KEY PROJECTS", "ACADEMIC PROJECTS", "PERSONAL PROJECTS",
            "REPRESENTATIVE PROJECTS", "PROJECT EXPERIENCE", "NOTABLE PROJECTS"
        ]:
            proj_start = i
            break

    if proj_start is None:
        for i, line in enumerate(lines):
            clean = line.strip().strip(":").upper()
            if any(clean.startswith(h) for h in ["KEY PROJECTS", "PROJECTS:", "NOTABLE PROJECTS"]):
                proj_start = i
                break

    if proj_start is None:
        return []

    for j in range(proj_start + 1, min(len(lines), proj_start + 60)):
        clean_next = lines[j].strip().strip(":").upper()
        if any(clean_next.startswith(h) for h in [
            "EDUCATION", "ACADEMIC", "EXPERIENCE", "WORK EXPERIENCE", "SKILLS",
            "TECHNICAL SKILLS", "CERTIFICATIONS", "DECLARATION", "LANGUAGES", "STRENGTHS"
        ]):
            proj_end = j
            break

    proj_lines = lines[proj_start + 1: proj_end if proj_end else proj_start + 40]
    if not proj_lines:
        return []

    projects = []
    current_proj = None

    for line in proj_lines:
        is_bullet = line.startswith(("-", "•", "*", "–", "—", "▪", "▫", ">")) or bool(re.match(r"^\d+\.\s+", line))
        tech_match = re.search(r"(?:tech(?:nologies|nology)?(?:\s*stack)?|tools|environment)\s*[:–-]\s*(.+)", line, re.IGNORECASE)

        if tech_match:
            tech_raw = tech_match.group(1).strip()
            techs = [t.strip() for t in re.split(r"[,;|/]", tech_raw) if t.strip()]
            if not current_proj:
                current_proj = {"name": "Project", "description": "", "technologies": []}
            current_proj["technologies"].extend(techs[:8])
        elif not is_bullet and len(line) <= 80 and not line.endswith("."):
            if current_proj:
                projects.append(current_proj)
            clean_title = re.sub(r"^(?:project\s*[:–-]?\s*|\d+\.\s*)", "", line, flags=re.IGNORECASE).strip()
            current_proj = {
                "name": clean_title,
                "description": "",
                "technologies": []
            }
        else:
            cleaned_text = re.sub(r"^[-•*–—▪▫>\d.]+\s*", "", line).strip()
            if cleaned_text:
                if not current_proj:
                    current_proj = {"name": "Project", "description": "", "technologies": []}
                if current_proj["description"]:
                    current_proj["description"] += " " + cleaned_text
                else:
                    current_proj["description"] = cleaned_text

    if current_proj:
        projects.append(current_proj)

    valid_projects = []
    for p in projects:
        if p.get("name") and len(p["name"]) >= 3:
            p["description"] = p.get("description", "")[:300]
            valid_projects.append(p)
    return valid_projects[:6]


def extract_certifications_from_cv(raw_text: str) -> list:
    """
    Section-aware heuristic extractor for certifications.
    """
    if not raw_text or not raw_text.strip():
        return []

    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

    cert_start = None
    cert_end = None
    for i, line in enumerate(lines):
        clean = line.strip().strip(":").upper()
        if clean in [
            "CERTIFICATIONS", "CERTIFICATES", "LICENSES & CERTIFICATIONS",
            "PROFESSIONAL CERTIFICATIONS", "ACCREDITATIONS", "COURSES & CERTIFICATIONS"
        ]:
            cert_start = i
            break

    if cert_start is None:
        for i, line in enumerate(lines):
            clean = line.strip().strip(":").upper()
            if any(clean.startswith(h) for h in ["CERTIFICATIONS", "CERTIFICATES", "LICENSES"]):
                cert_start = i
                break

    if cert_start is None:
        return []

    for j in range(cert_start + 1, min(len(lines), cert_start + 40)):
        clean_next = lines[j].strip().strip(":").upper()
        if any(clean_next.startswith(h) for h in [
            "EDUCATION", "EXPERIENCE", "PROJECTS", "SKILLS", "DECLARATION",
            "LANGUAGES", "STRENGTHS", "PERSONAL DETAILS", "HOBBIES"
        ]):
            cert_end = j
            break

    cert_lines = lines[cert_start + 1: cert_end if cert_end else cert_start + 25]
    if not cert_lines:
        return []

    items = []
    KNOWN_ISSUERS = [
        ("AWS", "Amazon Web Services"),
        ("Amazon", "Amazon Web Services"),
        ("Microsoft", "Microsoft"),
        ("Azure", "Microsoft Azure"),
        ("Google", "Google Cloud"),
        ("GCP", "Google Cloud"),
        ("Automation Anywhere", "Automation Anywhere"),
        ("UiPath", "UiPath"),
        ("Scrum Alliance", "Scrum Alliance"),
        ("Scrum.org", "Scrum.org"),
        ("PMI", "Project Management Institute"),
        ("Cisco", "Cisco"),
        ("Oracle", "Oracle"),
        ("CompTIA", "CompTIA"),
        ("Salesforce", "Salesforce"),
        ("HashiCorp", "HashiCorp"),
        ("Kubernetes", "CNCF / Linux Foundation"),
    ]

    for line in cert_lines:
        clean = re.sub(r"^[-•*–—▪▫>\d.]+\s*", "", line).strip()
        if not clean or len(clean) < 4 or len(clean) > 120:
            continue

        year_match = re.search(r"\b((?:19|20)\d{2})\b", clean)
        year = year_match.group(1) if year_match else None

        name = clean
        if year:
            name = re.sub(r"\b" + year + r"\b", "", name).strip(" ,-–()")

        issuer = None
        for keyword, full_name in KNOWN_ISSUERS:
            if re.search(r"\b" + re.escape(keyword) + r"\b", clean, re.IGNORECASE):
                issuer = full_name
                break

        by_match = re.search(r"(?:by|from|issued by)\s+([A-Za-z0-9\s&]+)", clean, re.IGNORECASE)
        if by_match and not issuer:
            issuer = by_match.group(1).strip()[:50]

        items.append({
            "name": name[:100],
            "issuer": issuer,
            "year": year
        })

    return items[:8]


DEGREE_EXTRACTION_RULES = [
    (r'\b(?:Bachelor\s+of\s+Technology|B\.?[-–]?\s*Tech\.?)(?:\s*\(\s*|\s*(?:in|of|-|–)\s*|\s+)([A-Za-z\s&/]+)', 'Bachelor of Technology'),
    (r'\b(?:Bachelor\s+(?:of|in)\s+Engineering|B\.E\.?)(?:\s*\(\s*|\s*(?:in|of|-|–)\s*|\s+)([A-Za-z\s&/]+)', 'Bachelor of Engineering'),
    (r'\bBachelor(?:[\'’]?s)?\s+Degree(?:\s+(?:in|of)\s+([A-Za-z\s&/]+))?', 'Bachelor\'s Degree'),
    (r'\bBachelor\s+of\s+Computer\s+Science\b', 'Bachelor of Computer Science'),
    (r'\bBachelor\s+of\s+Commerce\b', 'Bachelor of Commerce'),
    (r'\bBachelor\s+of\s+Science\b|\bB\.?\s*Sc\.?\b(?:\s+(?:in|of)\s+([A-Za-z\s&/]+))?', 'Bachelor of Science'),
    (r'\bBCA\b', 'Bachelor of Computer Applications (BCA)'),
    (r'\b(?:Master\s+of\s+Technology|M\.?[-–]?\s*Tech\.?)(?:\s*\(\s*|\s*(?:in|of|-|–)\s*|\s+)([A-Za-z\s&/]+)', 'Master of Technology'),
    (r'\b(?:Master\s+(?:of|in)\s+Engineering|M\.E\.?)(?:\s*\(\s*|\s*(?:in|of|-|–)\s*|\s+)([A-Za-z\s&/]+)', 'Master of Engineering'),
    (r'\bMaster(?:[\'’]?s)?\s+Degree(?:\s+(?:in|of)\s+([A-Za-z\s&/]+))?', 'Master\'s Degree'),
    (r'\bMCA\b', 'Master of Computer Applications (MCA)'),
    (r'\bMBA\b', 'Master of Business Administration (MBA)'),
    (r'\bM\.?\s*Sc\.?\b(?:\s+(?:in|of)\s+([A-Za-z\s&/]+))?', 'Master of Science'),
    (r'\bDiploma\s+in\s+([A-Za-z\s&/]+)', 'Diploma'),
    (r'\b(?:Higher\s+Secondary(?:\s+Education)?|HSSC|10\+2)(?:\s+in\s+([A-Za-z\s&/]+))?', 'Higher Secondary (12th)'),
    (r'\b(?:Secondary\s+School\s+Certificate|SSC|10th\s+Standard|10th\s+Grade)\b', 'Secondary School (10th)'),
]

INSTITUTION_PATTERNS = [
    r'([A-Z][A-Za-z0-9&.,\'’\s-]*?(?:College|University|Institute|School|Polytechnic|Academy|Centennial College|NCERT|SCERT|KTU|PCCE|Goa Engineering College)[A-Za-z0-9&.,\'’\s-]*)',
]


def clean_extracted_inst(candidate: str) -> Optional[str]:
    """Clean and validate candidate institution strings."""
    if not candidate:
        return None
    cleaned = re.split(
        r'[\n\r]|(?:\b(?:CGPA|GPA|Grade|Securing|Percentage|Bachelor|Master|Diploma|B\.Tech|B\.E|EDUCATION|CERTIFICATION|DETAILS|KEY PROJECTS?)\b)',
        candidate,
        flags=re.IGNORECASE
    )[0]
    cleaned = re.sub(r'^[,\s.–-]+|[,\s.–-]+$', '', cleaned)
    cleaned = re.sub(r'^(?:from|at|in|attended|completed\s+at)\s+', '', cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.strip()

    lower = cleaned.lower()
    if any(b in lower for b in ['slas', 'mail content', 'bot developer', 'functional testing', 'automation anywhere', 'uipath']):
        return None
    if len(cleaned) < 4:
        return None
    return cleaned[:75]


def extract_education_from_cv(raw_text: str) -> list:
    """
    Robust section-aware education extractor that parses degree titles, institutions,
    graduation years, fields of study, and academic scores/grades.
    """
    if not raw_text or not raw_text.strip():
        return []

    text = re.sub(r'([A-Za-z0-9,])\n([A-Za-z0-9])', r'\1 \2', raw_text)
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # 1. Locate Education section boundary
    edu_start = None
    edu_end = None
    for i, line in enumerate(lines):
        clean = line.strip().strip(':')
        if clean.upper() in [
            'EDUCATION', 'EDUCATION DETAILS', 'EDUCATIONAL QUALIFICATION',
            'EDUCATIONAL QUALIFICATIONS', 'ACADEMIC QUALIFICATIONS',
            'ACADEMIC BACKGROUND', 'ACADEMICS', 'QUALIFICATIONS',
            'EDUCATION & CERTIFICATIONS', 'EDUCATION AND TRAINING'
        ]:
            edu_start = i
            break

    if edu_start is not None:
        for j in range(edu_start + 1, min(len(lines), edu_start + 45)):
            clean_next = lines[j].strip().strip(':').upper()
            if any(clean_next.startswith(h) for h in [
                'WORK EXPERIENCE', 'PROFESSIONAL EXPERIENCE', 'EXPERIENCE',
                'KEY PROJECT', 'PROJECTS', 'TECHNOLOGY STACK', 'SKILLS',
                'TECHNICAL SKILLS', 'CORE COMPETENCIES', 'LANGUAGES',
                'ADDITIONAL INFORMATION', 'DECLARATION', 'STRENGTH'
            ]):
                edu_end = j
                break
        edu_lines = lines[edu_start + 1: edu_end if edu_end else edu_start + 25]
    else:
        edu_lines = lines

    edu_corpus = '\n'.join(edu_lines)
    search_texts = [edu_corpus]
    if len(edu_lines) < len(lines):
        search_texts.append(text)

    # University/College in section if explicitly listed
    sec_university = None
    if edu_start is not None:
        for l in edu_lines:
            im = re.search(r'([A-Z][A-Za-z0-9&.,\'’\s-]*?(?:College|University|Institute|School|Polytechnic|Academy|KTU)[A-Za-z0-9&.,\'’\s-]*)', l)
            if im:
                c_inst = clean_extracted_inst(im.group(1))
                if c_inst:
                    sec_university = c_inst
                    break

    items = []

    for target_corpus in search_texts:
        for pat, base_title in DEGREE_EXTRACTION_RULES:
            for match in re.finditer(pat, target_corpus, re.IGNORECASE):
                spec = match.group(1).strip() if match.lastindex and match.group(1) else None
                field_of_study = None
                if spec:
                    spec = spec.rstrip(' )')
                    spec = re.split(r'[,|\n\–\-]|(?:\b(?:from|at|cgpa|in\s+the\s+year|securing|grade)\b)', spec, flags=re.IGNORECASE)[0].strip()
                    if len(spec) > 50:
                        spec = spec[:50]
                    field_of_study = spec
                    degree_name = f'{base_title} in {spec}' if base_title not in spec else spec
                else:
                    degree_name = base_title

                deg_lower = degree_name.lower()
                if any(bad in deg_lower for bad in ['before', 'between', 'benefit', 'beverage', 'become', 'behavior', ' automated', ' reused']):
                    continue

                start_pos = max(0, match.start() - 120)
                end_pos = min(len(target_corpus), match.end() + 140)
                context = target_corpus[start_pos:end_pos]

                inst = sec_university
                if not inst:
                    for ipat in INSTITUTION_PATTERNS:
                        im = re.search(ipat, context)
                        if im:
                            cand = clean_extracted_inst(im.group(1))
                            if cand and not any(d in cand.lower() for d in ['bachelor', 'master', 'diploma', 'degree in', 'b.tech', 'b.e.']):
                                inst = cand
                                break

                year = None
                ym = re.search(r'\b((?:19|20)\d{2}(?:\s*[-–]\s*(?:19|20)\d{2})?)\b', context)
                if ym:
                    year = ym.group(1)

                score = None
                sm = re.search(r'(?i)(?:CGPA:?\s*(\d+\.?\d*)|(\d+\.?\d*)\s*CGPA|First\s+Class|Second\s+Class|\b\d{2}(?:\.\d+)?%)', context)
                if sm:
                    score = sm.group(0).strip()

                if not any(it['degree'].lower() == degree_name.lower() for it in items):
                    items.append({
                        'degree': degree_name,
                        'institution': inst,
                        'graduation_year': year,
                        'field_of_study': field_of_study,
                        'grade_or_score': score
                    })

        if items:
            break

    return items


class GeminiCVExtractor:
    """
    Isolated extraction service using Google Gemini with an ultra-reliable
    heuristic parser fallback and automatic circuit breaker for fast response times.
    """

    _consecutive_failures = 0
    _circuit_open_until = 0.0

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model_name or settings.CV_LLM_MODEL or "gemini-2.5-flash"

    def is_available(self) -> bool:
        """Check if Gemini extraction is currently available."""
        if not self.api_key:
            return False
        if time.time() < GeminiCVExtractor._circuit_open_until:
            return False
        return True

    def extract(self, cv_text: str) -> CandidateProfileExtraction:
        """
        Extract structured candidate profile from CV text using Google Gemini.
        Raises ExtractionServiceError if Gemini is unavailable, unconfigured, or fails.
        """
        if not cv_text or not cv_text.strip():
            raise ExtractionServiceError("Extracted CV text is empty.")

        # If no API key configured, signal that Gemini is unavailable
        if not self.api_key:
            raise ExtractionServiceError("No Gemini API key configured.")

        # Fast path if circuit breaker is open
        if time.time() < GeminiCVExtractor._circuit_open_until:
            raise ExtractionServiceError("Gemini API circuit breaker is OPEN (service temporarily unavailable).")

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key, http_options={"timeout": 15000})
            prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nCandidate CV Text:\n---\n{cv_text}\n---"

            candidate_models = [
                # 1. Active Flash-Lite models (highest throughput, instant response, verified active)
                "gemini-3.5-flash-lite",
                "gemini-flash-lite-latest",
                "gemini-3.1-flash-lite",
                # 2. Configured model (if distinct)
                self.model_name,
                # 3. Next-gen standard & pro models recommended by Google
                "gemini-3.8-flash",
                "gemini-3.1-pro-preview",
                "gemini-flash-latest",
                # 4. Legacy models (kept as lower priority fallbacks)
                "gemini-2.5-flash",
                "gemini-1.5-flash",
                "gemini-2.5-pro",
            ]
            candidate_models = list(dict.fromkeys([m for m in candidate_models if m]))
            response = None
            last_err = None
            for m_name in candidate_models:
                try:
                    response = client.models.generate_content(
                        model=m_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.1,
                        ),
                    )
                    if response and response.text:
                        logger.info(f"Gemini CV extraction succeeded using model '{m_name}'")
                        break
                except Exception as model_err:
                    last_err = model_err
                    is_exhausted = "429" in str(model_err) or "RESOURCE_EXHAUSTED" in str(model_err)
                    log_fn = logger.warning if is_exhausted else logger.info
                    log_fn(
                        f"Gemini model '{m_name}' {'exhausted quota (429)' if is_exhausted else 'failed'}: {model_err}. "
                        "Falling back to next model..."
                    )
                    continue

            if not response or not response.text:
                raise ExtractionServiceError(f"Gemini CV extraction failed: {last_err}")

            response_text = response.text
            result = self._parse_and_validate(response_text)

            # Extra sanity check on candidate_name from AI
            if result.candidate_name and not is_valid_human_name(result.candidate_name):
                logger.info(f"Discarding invalid AI candidate name '{result.candidate_name}'")
                result.candidate_name = None

            GeminiCVExtractor._consecutive_failures = 0
            GeminiCVExtractor._circuit_open_until = 0.0
            return result

        except ExtractionServiceError:
            raise
        except ValidationError as ve:
            logger.error(f"Pydantic validation error on Gemini response: {ve}")
            raise ExtractionServiceError(f"AI response did not match expected structure: {ve.error_count()} validation error(s).")
        except Exception as e:
            logger.warning(f"Gemini extraction failed ({str(e)[:100]}).")
            GeminiCVExtractor._consecutive_failures += 1
            if GeminiCVExtractor._consecutive_failures >= 2:
                GeminiCVExtractor._circuit_open_until = time.time() + 180.0
            raise ExtractionServiceError(f"Gemini CV extraction failed: {str(e)}")

    def extract_with_fallback(self, cv_text: str) -> CandidateProfileExtraction:
        """
        Attempts Gemini extraction, filling missing fields from fallback.
        If Gemini is unavailable, returns full heuristic fallback.
        """
        fallback = heuristic_cv_extract(cv_text)
        try:
            primary = self.extract(cv_text)
            return fill_missing_from_fallback(primary, fallback)
        except Exception as e:
            logger.info(f"Gemini extraction unavailable ({e}), using heuristic parser.")
            return fallback

    def _parse_and_validate(self, json_string: str) -> CandidateProfileExtraction:
        """
        Clean markdown formatting (if any) and parse JSON with Pydantic.
        """
        cleaned = json_string.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        data = json.loads(cleaned)
        return CandidateProfileExtraction.model_validate(data)


def fill_missing_from_fallback(
    primary: CandidateProfileExtraction,
    fallback: CandidateProfileExtraction,
) -> CandidateProfileExtraction:
    """
    Fills any details that were not given by Gemini (or are empty/invalid)
    using the rule-based fallback extraction.
    """
    # 1. Candidate name
    cand_name = primary.candidate_name
    if not cand_name or not is_valid_human_name(cand_name):
        cand_name = fallback.candidate_name

    # 2. Email
    email = primary.email
    if not email or "@" not in email:
        email = fallback.email

    # 3. Phone
    phone = primary.phone
    if not phone or len(re.sub(r"\D", "", phone)) < 7:
        phone = fallback.phone

    # 4. URLs
    linkedin_url = primary.linkedin_url or fallback.linkedin_url
    github_url = primary.github_url or fallback.github_url

    # 5. Years of experience
    years_exp = primary.years_of_experience
    if not years_exp or years_exp <= 0:
        years_exp = fallback.years_of_experience

    # 6. Skills: Merge primary skills with fallback skills so no skills are lost
    seen_skills = set()
    merged_skills = []
    for s in (primary.skills or []):
        if s and str(s).strip():
            clean_s = canonicalize_skill(str(s).strip())
            low = clean_s.lower()
            if low not in seen_skills:
                seen_skills.add(low)
                merged_skills.append(clean_s)

    for s in (fallback.skills or []):
        if s and str(s).strip():
            clean_s = canonicalize_skill(str(s).strip())
            low = clean_s.lower()
            if low not in seen_skills:
                seen_skills.add(low)
                merged_skills.append(clean_s)

    # 7. Education: If primary has education, keep it and supplement any missing degrees from fallback
    if primary.education:
        merged_edu = list(primary.education)
        existing_degrees = {str(e.degree).lower() for e in merged_edu if e.degree}
        for f in (fallback.education or []):
            if f.degree and str(f.degree).lower() not in existing_degrees:
                merged_edu.append(f)
                existing_degrees.add(str(f.degree).lower())
    else:
        merged_edu = list(fallback.education or [])

    # 8. Experience
    merged_exp = list(primary.experience or []) if primary.experience else list(fallback.experience or [])

    # 9. Projects
    merged_proj = list(primary.projects or []) if primary.projects else list(fallback.projects or [])

    # 10. Certifications
    merged_cert = list(primary.certifications or []) if primary.certifications else list(fallback.certifications or [])

    return CandidateProfileExtraction(
        candidate_name=cand_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        years_of_experience=years_exp or 0.0,
        skills=merged_skills,
        education=merged_edu,
        experience=merged_exp,
        projects=merged_proj,
        certifications=merged_cert,
    )


# Factory function
def get_cv_extractor() -> GeminiCVExtractor:
    return GeminiCVExtractor()

