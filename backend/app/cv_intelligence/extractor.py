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

    # 7. Robust Section-Aware Education Extraction
    education_items = extract_education_from_cv(cv_text)

    return CandidateProfileExtraction(
        candidate_name=candidate_name,
        email=email,
        phone=phone,
        linkedin_url=linkedin_url,
        github_url=github_url,
        years_of_experience=years_exp,
        skills=sorted(list(skills_found)),
        education=education_items,
        experience=[],
        projects=[],
        certifications=[],
    )


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

    def extract(self, cv_text: str) -> CandidateProfileExtraction:
        """
        Extract structured candidate profile from CV text.
        Returns a validated CandidateProfileExtraction model.
        """
        if not cv_text or not cv_text.strip():
            raise ExtractionServiceError("Extracted CV text is empty.")

        # If no API key configured, use rule-based fallback directly
        if not self.api_key:
            logger.info("No Gemini API key configured. Using heuristic CV extractor.")
            return heuristic_cv_extract(cv_text)

        # Fast path if circuit breaker is open
        if time.time() < GeminiCVExtractor._circuit_open_until:
            logger.info("Gemini API circuit breaker is OPEN. Using fast heuristic parser.")
            return heuristic_cv_extract(cv_text)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key, http_options={"timeout": 15000})
            prompt = f"{EXTRACTION_SYSTEM_PROMPT}\n\nCandidate CV Text:\n---\n{cv_text}\n---"

            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )

            response_text = response.text
            if not response_text:
                raise ExtractionServiceError("Received empty response from Gemini API.")

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


# Factory function
def get_cv_extractor() -> GeminiCVExtractor:
    return GeminiCVExtractor()
