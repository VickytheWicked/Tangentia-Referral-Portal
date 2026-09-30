import re
import json
import logging
from typing import List, Tuple, Set, Dict, Optional
from app.config import settings
from app.cv_intelligence.models import MatchLevel

logger = logging.getLogger("cv_intelligence")

# Broad canonical skill tokens across enterprise engineering, cloud, automation, QA, BA, PM, and design
STANDARD_SKILL_KEYWORDS = [
    # Programming, Scripting & Frameworks
    "python", "fastapi", "django", "flask", "react", "react.js", "next.js", "angular", "vue",
    "javascript", "typescript", "node.js", "nodejs", "express", "sql", "postgresql", "postgres",
    "mysql", "sqlite", "mongodb", "redis", "docker", "kubernetes", "k8s", "aws", "azure", "gcp",
    "git", "ci/cd", "rest", "rest api", "graphql", "html", "css", "tailwind", "linux", "c++", "c#", ".net", "vb.net",
    "java", "spring", "spring boot", "kafka", "rabbitmq", "pandas", "numpy", "tensorflow", "pytorch",
    "sharepoint", "power bi", "power automate", "microsoft 365", "excel", "salesforce",

    # RPA & Intelligent Automation
    "automation anywhere", "a360", "uipath", "blue prism", "rpa", "ocr", "bot", "iq bot", "apa",
    "agentic process automation", "power platform", "ai builder",

    # QA & Test Automation
    "selenium", "testng", "cucumber", "postman", "cypress", "playwright", "junit", "manual testing",
    "automation testing", "qa", "jira", "api testing", "regression testing", "test automation",
    "uat", "defect lifecycle", "performance testing", "sdlc",

    # Business Analysis, Architecture & Project Management
    "scrum", "agile", "sprint", "kanban", "business analysis", "brd", "frd", "gap analysis",
    "stakeholder management", "user stories", "requirements gathering", "process mapping", "bpmn",
    "business architecture", "zachman framework", "enterprise architecture", "product backlog",
    "functional specifications", "pmo", "program delivery", "project management", "delivery leadership",

    # Cloud Architecture, Systems & Big Data
    "solution architecture", "cloud architecture", "microservices", "system design",
    "databricks", "spark", "pyspark", "etl", "data warehouse", "snowflake", "big data",
    "devops", "sre", "zero-trust security",

    # Support, Systems & Infrastructure
    "it support", "troubleshooting", "helpdesk", "active directory", "networking", "vpn",
    "incident management", "itil", "windows server", "hardware maintenance", "sla",

    # AI, Generative AI & Prompt Engineering
    "prompt engineering", "generative ai", "genai", "llm", "large language models", "langchain",
    "rag", "fine-tuning", "agentic ai", "few-shot", "zero-shot", "vector search", "ai agents",

    # UI/UX & Design
    "ui/ux", "ui-ux", "figma", "wireframing", "prototyping", "user research", "user experience",
    "design system", "adobe xd", "photoshop", "illustrator", "responsive design", "web design",

    # Enterprise Sales & Executive
    "sales", "business development", "pre-sales", "account management", "revenue", "b2b",
    "p&l", "solution selling", "executive leadership", "contract negotiation"
]

# Domain synonym & equivalence taxonomy to connect candidate skills with job requirements
SKILL_TAXONOMY_MAP: Dict[str, Set[str]] = {
    "rpa": {
        "rpa", "robotic process automation", "automation anywhere", "a360", "uipath", "blue prism",
        "power automate", "bot", "iq bot", "apa", "agentic process automation", "power platform"
    },
    "automation anywhere": {
        "automation anywhere", "a360", "va360x", "iq bot", "rpa", "apa", "bot"
    },
    "business analysis": {
        "business analysis", "business analyst", "business architect", "business architecture",
        "brd", "frd", "requirements gathering", "process mapping", "bpmn", "gap analysis",
        "uat", "user stories", "functional specifications", "requirements & uat"
    },
    "business architecture": {
        "business architecture", "business architect", "enterprise architecture", "zachman framework",
        "solution architecture", "business functional modeling", "process mapping", "bpmn"
    },
    "agile": {
        "agile", "scrum", "scrum master", "certified scrummaster", "sprint", "kanban",
        "product backlog", "user stories", "jira", "pmo", "delivery leadership"
    },
    "qa": {
        "qa", "quality assurance", "testing", "manual testing", "automation testing",
        "test automation", "selenium", "cypress", "playwright", "testng", "postman",
        "api testing", "regression testing", "jira", "uat", "defect lifecycle"
    },
    "generative ai": {
        "generative ai", "genai", "llm", "large language models", "prompt engineering",
        "rag", "langchain", "agentic ai", "few-shot", "zero-shot", "ai agents", "fine-tuning"
    },
    "prompt engineering": {
        "prompt engineering", "few-shot", "zero-shot", "prompt testing", "context engineering",
        "hallucination mitigation", "llm", "generative ai", "structured outputs"
    },
    "python": {
        "python", "fastapi", "django", "flask", "pyspark", "pandas", "numpy"
    },
    "cloud architecture": {
        "cloud architecture", "solution architecture", "system design", "microservices",
        "aws", "azure", "gcp", "docker", "kubernetes", "databricks"
    },
    "it support": {
        "it support", "troubleshooting", "helpdesk", "active directory", "windows server",
        "networking", "vpn", "incident management", "itil", "hardware maintenance", "sla"
    },
    "frontend": {
        "frontend", "react", "react.js", "next.js", "typescript", "javascript", "html",
        "css", "ui/ux", "figma", "wireframing", "adobe xd", "design system", "responsive design"
    },
    "ui/ux": {
        "ui/ux", "ui-ux", "figma", "adobe xd", "wireframing", "prototyping", "design system",
        "user research", "user experience", "html", "css", "web design"
    },
    "sales": {
        "sales", "business development", "pre-sales", "account management", "revenue",
        "b2b", "stakeholder management", "solution selling", "p&l", "delivery leadership"
    },
}


def canonicalize_skill(skill: str) -> str:
    """Format skill nicely for user display."""
    s = skill.strip()
    upper_tokens = {"rpa", "ai", "llm", "rag", "sql", "api", "qa", "ui", "ux", "ui/ux", "ui-ux", "aws", "gcp", "brd", "frd", "uat", "pmo", "sla", "vpn", "itil", "sdlc", "a360", "apa", "css", "html"}
    if s.lower() in upper_tokens:
        return s.upper()
    return " ".join(word.capitalize() for word in s.split())


def extract_keywords_from_job(job_title: str, department: str, description: str) -> Tuple[Set[str], float]:
    """
    Extract expected technical skills and minimum years of experience from job opening details.
    """
    combined_text = f"{job_title} {department} {description}".lower()

    expected_skills = set()

    # 1. Check title tokens directly (highest priority)
    title_lower = job_title.lower()
    for kw in STANDARD_SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, title_lower):
            expected_skills.add(kw)

    # 2. Check description for skills
    for kw in STANDARD_SKILL_KEYWORDS:
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, combined_text):
            expected_skills.add(kw)

    # 3. Detect domain taxonomy from job title and description
    for domain, aliases in SKILL_TAXONOMY_MAP.items():
        if any(re.search(r"\b" + re.escape(a) + r"\b", title_lower) for a in aliases):
            expected_skills.add(domain)

    # 4. Extract required minimum years of experience
    min_exp_years = 0.0

    # Pattern A: "minimum X years", "at least X years", "X+ years of"
    patterns = [
        r"(?:minimum|at\s+least|total\s+it\s+experience\s+of\s+at\s+least|with\s+minimum)\s+(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?",
        r"(\d+(?:\.\d+)?)\s*(?:\+)?\s*years?\s+(?:of\s+)?(?:it\s+|relevant\s+|work\s+|professional\s+)?experience",
        r"(\d+(?:\.\d+)?)\s*[-–to]\s*(\d+(?:\.\d+)?)\s*years",
    ]
    for p in patterns:
        m = re.search(p, combined_text)
        if m:
            try:
                val = float(m.group(1))
                if 1.0 <= val <= 25.0:
                    min_exp_years = max(min_exp_years, val)
            except (ValueError, IndexError):
                pass

    return expected_skills, min_exp_years


def match_candidate_to_job(
    candidate_skills: List[str],
    candidate_years_exp: float,
    candidate_projects: List[dict],
    candidate_experience: List[dict],
    job_title: str,
    job_department: str,
    job_description: str,
) -> Tuple[MatchLevel, List[str], List[str], str, List[str]]:
    """
    Compare candidate profile with job requirements using domain taxonomy and semantic matching.
    Returns:
    - match_level: Strong Match / Good Match / Potential Match / Irrelevant
    - matched_skills: List of skills matched
    - missing_skills: List of important skills not found
    - experience_match: Text description of experience alignment
    - explanation: List of human-readable bullet points
    """
    expected_skills, min_exp_years = extract_keywords_from_job(job_title, job_department, job_description)

    # Normalize candidate skills from skills array, projects, and experience
    candidate_skill_tokens = set()
    for s in (candidate_skills or []):
        if isinstance(s, str) and s.strip():
            candidate_skill_tokens.add(s.lower().strip())

    for proj in (candidate_projects or []):
        for tech in proj.get("technologies", []):
            if isinstance(tech, str) and tech.strip():
                candidate_skill_tokens.add(tech.lower().strip())

    for exp in (candidate_experience or []):
        for resp in exp.get("responsibilities", []):
            if isinstance(resp, str):
                for kw in STANDARD_SKILL_KEYWORDS:
                    if re.search(r"\b" + re.escape(kw) + r"\b", resp.lower()):
                        candidate_skill_tokens.add(kw)

    # Evaluate matches against expected skills using direct match + taxonomy
    matched_skills_set = set()
    missing_skills_set = set()

    if expected_skills:
        for req in expected_skills:
            req_lower = req.lower()
            found = False

            # Direct string or substring match
            for c_skill in candidate_skill_tokens:
                if req_lower == c_skill or req_lower in c_skill or c_skill in req_lower:
                    matched_skills_set.add(canonicalize_skill(req_lower))
                    found = True
                    break

            # Taxonomy equivalence match
            if not found and req_lower in SKILL_TAXONOMY_MAP:
                tax_aliases = SKILL_TAXONOMY_MAP[req_lower]
                for c_skill in candidate_skill_tokens:
                    if c_skill in tax_aliases or any(alias in c_skill for alias in tax_aliases):
                        matched_skills_set.add(canonicalize_skill(req_lower))
                        found = True
                        break

            # Reverse taxonomy check (if candidate skill has taxonomy including requirement)
            if not found:
                for c_skill in candidate_skill_tokens:
                    if c_skill in SKILL_TAXONOMY_MAP and req_lower in SKILL_TAXONOMY_MAP[c_skill]:
                        matched_skills_set.add(canonicalize_skill(req_lower))
                        found = True
                        break

            if not found:
                # Only report as missing if it's a prominent requirement
                if req_lower not in {"excel", "rest", "git", "sales"}:
                    missing_skills_set.add(canonicalize_skill(req_lower))
    else:
        # Fallback if job description has no recognized technical keywords
        for s in list(candidate_skill_tokens)[:5]:
            matched_skills_set.add(canonicalize_skill(s))

    matched_skills = sorted(list(matched_skills_set))
    missing_skills = sorted(list(missing_skills_set))

    # Experience evaluation
    exp_ok = True
    if min_exp_years > 0:
        if candidate_years_exp >= min_exp_years:
            exp_text = f"{candidate_years_exp:.1f} yrs (Meets {min_exp_years:g}+ yrs requirement)"
            exp_ok = True
        else:
            diff = min_exp_years - candidate_years_exp
            exp_text = f"{candidate_years_exp:.1f} yrs ({diff:.1f} yrs below {min_exp_years:g}+ yrs requirement)"
            # Allow modest experience tolerance if skills match strongly
            exp_ok = (candidate_years_exp >= min_exp_years * 0.75)
    else:
        exp_text = f"{candidate_years_exp:.1f} yrs experience"
        exp_ok = True

    # Project or job title relevance check
    relevant_project = None
    for p in (candidate_projects or []):
        p_name = p.get("name", "")
        p_desc = p.get("description", "")
        if any(kw.lower() in f"{p_name} {p_desc}".lower() for kw in matched_skills_set):
            relevant_project = p_name
            break

    # Determine Match Level
    coverage = len(matched_skills) / max(len(expected_skills), 1) if expected_skills else 0.5

    # Multi-factor tiering
    if (coverage >= 0.5 or len(matched_skills) >= 3) and exp_ok:
        level = MatchLevel.STRONG_MATCH
    elif coverage >= 0.25 or len(matched_skills) >= 1 or (candidate_years_exp >= 2.0 and exp_ok):
        level = MatchLevel.GOOD_MATCH
    else:
        level = MatchLevel.POTENTIAL_MATCH

    # Construct concise, explainable decision highlights
    explanation = []

    # 1. Matched skills highlights
    for s in matched_skills[:4]:
        explanation.append(f"✓ {s}")

    # 2. Experience highlight
    if candidate_years_exp > 0:
        if exp_ok:
            explanation.append(f"✓ {candidate_years_exp:.1f}+ yrs relevant experience")
        else:
            explanation.append(f"• {candidate_years_exp:.1f} yrs experience (target: {min_exp_years:g}+ yrs)")

    # 3. Project highlight
    if relevant_project:
        explanation.append(f"✓ Relevant project: {relevant_project[:40]}")

    # 4. Gaps / missing criteria
    for m in missing_skills[:2]:
        explanation.append(f"• {m} not highlighted in CV")

    if not explanation:
        explanation.append("• Candidate profile submitted for review")

    return level, matched_skills, missing_skills, exp_text, explanation


def llm_match_candidate_to_job(
    candidate_skills: List[str],
    candidate_years_exp: float,
    candidate_projects: List[dict],
    candidate_experience: List[dict],
    job_title: str,
    job_department: str,
    job_description: str,
) -> Tuple[MatchLevel, List[str], List[str], str, List[str], Optional[str]]:
    """
    Evaluate candidate alignment against a job position using Google Gemini LLM.
    Determines match_level, matched_skills, missing_skills, explanation bullets, and a 1-2 sentence fit_summary.
    Gracefully falls back to rule-based matching if Gemini is unconfigured or encounters an error.
    """
    def _fallback() -> Tuple[MatchLevel, List[str], List[str], str, List[str], Optional[str]]:
        lvl, matched, missing, exp, expl = match_candidate_to_job(
            candidate_skills=candidate_skills,
            candidate_years_exp=candidate_years_exp,
            candidate_projects=candidate_projects,
            candidate_experience=candidate_experience,
            job_title=job_title,
            job_department=job_department,
            job_description=job_description,
        )
        fit_narrative = (
            f"{lvl.value}: Candidate brings {candidate_years_exp:.1f} years of experience with skills in "
            f"{', '.join(matched[:3]) if matched else 'core domain technologies'}."
        )
        return lvl, matched, missing, exp, expl, fit_narrative

    if not getattr(settings, "GEMINI_API_KEY", None):
        return _fallback()

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"timeout": 15000})

        # Format candidate experience summary for prompt
        exp_lines = []
        for exp in (candidate_experience or [])[:4]:
            title = exp.get("job_title") or "Role"
            company = exp.get("company") or "Company"
            dur = exp.get("duration") or ""
            resp = exp.get("responsibilities") or []
            resp_str = f" ({'; '.join(resp[:2])})" if resp else ""
            exp_lines.append(f"- {title} at {company} [{dur}]{resp_str}")
        exp_summary = "\n".join(exp_lines) if exp_lines else "None detailed"

        # Format candidate projects summary
        proj_lines = []
        for p in (candidate_projects or [])[:3]:
            p_name = p.get("name") or "Project"
            p_desc = p.get("description") or ""
            p_tech = p.get("technologies") or []
            tech_str = f" [Tech: {', '.join(p_tech[:4])}]" if p_tech else ""
            proj_lines.append(f"- {p_name}: {p_desc[:120]}{tech_str}")
        proj_summary = "\n".join(proj_lines) if proj_lines else "None detailed"

        skills_str = ", ".join(candidate_skills[:25]) if candidate_skills else "None explicitly listed"
        desc_clean = (job_description or "")[:2500]

        prompt = f"""You are a senior technical recruiter and talent advisor at Tangentia, a global enterprise technology solutions company.
Evaluate this candidate's fit against the target job requisition sourced from the Tangentia CATS Careers portal.

Target Job Opening:
- Position: {job_title}
- Department: {job_department}
- Job Description:
{desc_clean}

Candidate Profile:
- Total Experience: {candidate_years_exp:.1f} years
- Highlighted Skills: {skills_str}
- Career History:
{exp_summary}
- Notable Projects:
{proj_summary}

Task:
Evaluate the candidate and return a JSON object with EXACTLY this schema:
{{
  "match_level": "Strong Match" | "Good Match" | "Potential Match" | "Irrelevant",
  "matched_skills": ["Skill A", "Skill B"],
  "missing_skills": ["Gap 1", "Gap 2"],
  "experience_match": "X.X yrs (Meets requirement / target)",
  "explanation": [
    "✓ Point highlighting a top strength or alignment",
    "✓ Another relevant match point",
    "• Point noting any potential gap, requirement variance, or development area"
  ],
  "fit_summary": "A 1-2 sentence concise, professional narrative directly advising HR recruiters why this candidate is or isn't a great fit for this specific position at Tangentia."
}}

Criteria for match_level:
- "Strong Match": Candidate has direct domain experience and strongly covers required core skills.
- "Good Match": Candidate possesses foundational relevant skills and experience, with minor domain gaps easily bridgeable.
- "Potential Match": Candidate has adjacent technical or analytical background, or junior experience that could fit with mentoring.
- "Irrelevant": Candidate has no relevant skills, domain experience, background, or qualifications for this position.

Respond ONLY with valid JSON."""

        candidate_models = [
            # 1. Active Flash-Lite models (highest throughput, instant response, verified active)
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3.1-flash-lite",
            # 2. Configured model (if distinct)
            getattr(settings, "CV_LLM_MODEL", None),
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

        last_error = None
        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2,
                    ),
                )
                if response and response.text:
                    parsed = json.loads(response.text)
                    raw_level = parsed.get("match_level", "").strip()
                    raw_lower = raw_level.lower()
                    if "strong" in raw_lower:
                        match_level = MatchLevel.STRONG_MATCH
                    elif "good" in raw_lower:
                        match_level = MatchLevel.GOOD_MATCH
                    elif "potential" in raw_lower:
                        match_level = MatchLevel.POTENTIAL_MATCH
                    elif "irrelevant" in raw_lower or "not relevant" in raw_lower:
                        match_level = MatchLevel.IRRELEVANT
                    else:
                        match_level = MatchLevel.POTENTIAL_MATCH

                    matched_skills = [str(s).strip() for s in parsed.get("matched_skills", []) if str(s).strip()][:8]
                    missing_skills = [str(m).strip() for m in parsed.get("missing_skills", []) if str(m).strip()][:5]
                    exp_match = str(parsed.get("experience_match") or f"{candidate_years_exp:.1f} yrs experience").strip()
                    explanation = [str(e).strip() for e in parsed.get("explanation", []) if str(e).strip()][:5]
                    fit_summary = str(parsed.get("fit_summary", "")).strip() or None

                    if not explanation:
                        explanation = [f"✓ {s}" for s in matched_skills[:3]]

                    logger.info(f"Gemini LLM matched candidate for '{job_title}': {match_level.value} using {model_name}")
                    return match_level, matched_skills, missing_skills, exp_match, explanation, fit_summary
            except Exception as e:
                last_error = e
                is_exhausted = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
                log_fn = logger.warning if is_exhausted else logger.debug
                log_fn(
                    f"Gemini LLM matching attempt with '{model_name}' {'exhausted quota (429)' if is_exhausted else 'failed'}: {e}. "
                    "Falling back to next model..."
                )
                continue

        if last_error:
            logger.warning(f"Gemini LLM matching failed for '{job_title}', falling back to rule-based: {last_error}")
    except Exception as e:
        logger.warning(f"Error during Gemini LLM matching initialization: {e}")

    return _fallback()
