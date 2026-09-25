"""
Requirement Analyzer — Evidence-Based CV Requirement Analysis
=============================================================

This module transforms the free-form LLM job-match into a structured,
evidence-grounded requirement matrix that HR can audit and trust.

Pipeline:
  1. extract_structured_job_requirements()  — parse job description into
     structured RequirementSpec list, cached per position_id.
  2. run_deterministic_checks()             — pure-Python evaluation of
     numeric/experience requirements that do NOT need LLM interpretation.
  3. run_semantic_analysis()               — Gemini call that semantically
     evaluates non-numeric requirements, with deterministic facts pre-loaded
     so the model cannot contradict them.
  4. generate_requirement_analysis()       — orchestrates 1-3, validates
     output strictly via Pydantic, returns OverallAnalysis.

CRITICAL RULES enforced in this module:
  - NOT_DEMONSTRATED means "CV does not provide enough evidence."
  - NOT_MET means "CV contains explicit evidence that the requirement is
    NOT satisfied (e.g. 7 yrs documented when 10+ required)."
  - Gemini MUST NOT fabricate CV quotes or skills.
  - Deterministic results (numeric checks) cannot be overridden by Gemini.
  - AI must NOT produce hiring verdicts or hiring recommendations.
"""

import json
import logging
import re
import os
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, ValidationError

from app.config import settings

logger = logging.getLogger("cv_intelligence")

# ---------------------------------------------------------------------------
# In-process cache for structured job requirements (keyed by position_id)
# This avoids repeated Gemini calls for the same job across multiple candidates.
# ---------------------------------------------------------------------------
_JOB_REQUIREMENTS_CACHE: Dict[str, List[Dict[str, Any]]] = {}

_JOB_REQUIREMENTS_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "job_requirements_cache.json",
)


def _load_job_requirements_cache() -> None:
    """Load persisted job requirements cache from disk."""
    global _JOB_REQUIREMENTS_CACHE
    if os.path.exists(_JOB_REQUIREMENTS_CACHE_FILE):
        try:
            with open(_JOB_REQUIREMENTS_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _JOB_REQUIREMENTS_CACHE.update(data)
                    logger.info(
                        f"Loaded {len(_JOB_REQUIREMENTS_CACHE)} cached job requirement entries."
                    )
        except Exception as e:
            logger.warning(f"Failed to load job requirements cache: {e}")


def _save_job_requirements_cache() -> None:
    """Persist job requirements cache to disk."""
    try:
        os.makedirs(os.path.dirname(_JOB_REQUIREMENTS_CACHE_FILE), exist_ok=True)
        with open(_JOB_REQUIREMENTS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_JOB_REQUIREMENTS_CACHE, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to save job requirements cache: {e}")


_load_job_requirements_cache()


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class RequirementStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    NOT_MET = "NOT_MET"
    NOT_DEMONSTRATED = "NOT_DEMONSTRATED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"


class RequirementCategory(str, Enum):
    MANDATORY = "MANDATORY"
    REQUIRED_EXPERIENCE = "REQUIRED_EXPERIENCE"
    REQUIRED_SKILLS = "REQUIRED_SKILLS"
    REQUIRED_DOMAIN = "REQUIRED_DOMAIN"
    REQUIRED_FRAMEWORKS = "REQUIRED_FRAMEWORKS"
    REQUIRED_ARCHITECTURE = "REQUIRED_ARCHITECTURE"
    PREFERRED = "PREFERRED"
    OTHER = "OTHER"


class RequirementAnalysisItem(BaseModel):
    """A single job requirement with its evidence-based evaluation."""

    requirement: str = Field(description="Short name of the requirement")
    category: RequirementCategory
    required_value: str = Field(description="What the job requires (e.g. '10+ years')")
    status: RequirementStatus
    cv_evidence: str = Field(
        description="Direct quote or summary from CV, or 'No explicit evidence found in CV.'"
    )
    reasoning: str = Field(description="Brief explanation of the classification")


class OverallAnalysis(BaseModel):
    """Complete evidence-based analysis of a candidate against a job."""

    key_observations: List[str] = Field(
        description="3-6 factual observations grounded in the requirement matrix"
    )
    mandatory_requirements: List[RequirementAnalysisItem] = Field(default_factory=list)
    supported_requirements: List[RequirementAnalysisItem] = Field(default_factory=list)
    partially_supported_requirements: List[RequirementAnalysisItem] = Field(
        default_factory=list
    )
    not_demonstrated_requirements: List[RequirementAnalysisItem] = Field(
        default_factory=list
    )
    analyzed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Step 1 — Structured Job Requirement Extraction (Gemini, cached per position)
# ---------------------------------------------------------------------------

_JOB_REQUIREMENT_EXTRACTION_PROMPT = """You are an expert HR analyst extracting structured job requirements from a job description.

Decompose the job description into a list of discrete, specific requirements.

For each requirement return an object with EXACTLY these fields:
- "requirement": Short name of the requirement (e.g. "Total IT Experience", "Business Architecture Experience", "Zachman Framework", "Ontario Government Experience")
- "category": One of: "MANDATORY", "REQUIRED_EXPERIENCE", "REQUIRED_SKILLS", "REQUIRED_DOMAIN", "REQUIRED_FRAMEWORKS", "REQUIRED_ARCHITECTURE", "PREFERRED", "OTHER"
  Categories:
  - MANDATORY: Must-have requirements explicitly stated as mandatory/essential
  - REQUIRED_EXPERIENCE: Years of experience requirements (total or domain-specific)
  - REQUIRED_SKILLS: Technical or business skills that are required
  - REQUIRED_DOMAIN: Domain/industry knowledge requirements
  - REQUIRED_FRAMEWORKS: Specific frameworks, standards, or methodologies required
  - REQUIRED_ARCHITECTURE: Architecture-specific experience requirements
  - PREFERRED: Nice-to-have, preferred, or an asset
  - OTHER: Any other requirement
- "required_value": The specific value or description from the job posting (e.g. "10+ years", "Zachman Framework", "Ontario Government / OPS experience")

CRITICAL RULES:
- Extract requirements explicitly stated or indicated in the job description.
- PRIORITY ORDERING:
  1. The FIRST requirement MUST be "Total Professional Experience" stating the required years of experience (e.g. "8+ years of total professional experience" or derived from seniority).
  2. The SECOND requirement MUST be "Education & Academic Qualifications" (e.g. "Degree or Diploma in Computer Science, Engineering, Business, or related discipline").
  3. The THIRD requirement should be Core Role / Domain Alignment.
  4. Followed by key technical skills, tools, and methodologies.
- Use the job posting's exact terminology for required_value where possible.
- If years are mentioned (e.g. "10+ years total IT experience"), include exact figure in required_value.
- Return a JSON array of requirement objects.

Job Title: {job_title}
Department: {department}

Job Description:
{description}

Return ONLY a valid JSON array. No explanation, no markdown."""


def _ensure_core_baseline_requirements(
    job_title: str,
    department: str,
    description: str,
    requirements: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Ensure the requirement list begins with fundamental recruitment gates:
    1. Total Professional Experience (numeric threshold)
    2. Education & Academic Qualifications
    Followed by core domain alignment and specialized skills.
    """
    if not requirements:
        requirements = []

    combined = f"{job_title} {department} {description}".lower()

    # 1. Total Professional Experience
    exp_idx = -1
    for i, r in enumerate(requirements):
        req_name = r.get("requirement", "").lower()
        cat = r.get("category", "").upper()
        if (
            any(kw in req_name for kw in ["total", "overall", "work experience", "it experience", "professional experience", "years of experience"])
            or cat == "REQUIRED_EXPERIENCE"
        ):
            exp_idx = i
            break

    if exp_idx >= 0:
        exp_item = requirements.pop(exp_idx)
        if exp_item.get("category") not in ("MANDATORY", "REQUIRED_EXPERIENCE"):
            exp_item["category"] = "MANDATORY"
        requirements.insert(0, exp_item)
    else:
        year_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?", combined)
        if year_match:
            exp_years = float(year_match.group(1))
        elif any(kw in job_title.lower() for kw in ["senior", "lead", "architect", "principal", "manager"]):
            exp_years = 8.0
        elif any(kw in job_title.lower() for kw in ["junior", "associate", "entry", "intern"]):
            exp_years = 2.0
        else:
            exp_years = 5.0

        requirements.insert(0, {
            "requirement": "Total Professional Experience",
            "category": "MANDATORY",
            "required_value": f"{exp_years:g}+ years of professional experience in software / IT delivery",
        })

    # 2. Education & Academic Qualifications
    edu_idx = -1
    for i, r in enumerate(requirements[1:], start=1):
        req_name = r.get("requirement", "").lower()
        if any(kw in req_name for kw in ["education", "degree", "academic", "diploma", "qualification", "bachelor", "master"]):
            edu_idx = i
            break

    if edu_idx >= 0:
        edu_item = requirements.pop(edu_idx)
        requirements.insert(1, edu_item)
    else:
        requirements.insert(1, {
            "requirement": "Education & Academic Qualifications",
            "category": "MANDATORY",
            "required_value": "Degree or Diploma in Computer Engineering, Computer Science, IT, Business, or related discipline",
        })

    return requirements


def extract_structured_job_requirements(
    position_id: str,
    job_title: str,
    department: str,
    description: str,
    force_refresh: bool = False,
) -> List[Dict[str, Any]]:
    """
    Parse a job description into a structured list of requirements using Gemini.
    Results are cached in memory and persisted to disk per position_id.
    Falls back to a minimal heuristic extraction if Gemini is unavailable.
    Guarantees REQ #1 is Total Professional Experience and REQ #2 is Education.
    """
    cache_key = f"{position_id}:{job_title.lower()}"

    if not force_refresh and cache_key in _JOB_REQUIREMENTS_CACHE:
        logger.debug(f"Using cached job requirements for '{job_title}'")
        cached = _JOB_REQUIREMENTS_CACHE[cache_key]
        return _ensure_core_baseline_requirements(job_title, department, description, list(cached))

    requirements: List[Dict[str, Any]] = []

    if settings.GEMINI_API_KEY:
        requirements = _gemini_extract_job_requirements(job_title, department, description)

    if not requirements:
        requirements = _heuristic_extract_job_requirements(job_title, department, description)

    requirements = _ensure_core_baseline_requirements(job_title, department, description, requirements)

    _JOB_REQUIREMENTS_CACHE[cache_key] = requirements
    _save_job_requirements_cache()
    logger.info(
        f"Extracted {len(requirements)} structured requirements for '{job_title}' (position {position_id})"
    )
    return requirements


def _gemini_extract_job_requirements(
    job_title: str, department: str, description: str
) -> List[Dict[str, Any]]:
    """Call Gemini to extract structured job requirements from the job description."""
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY, http_options={"timeout": 15000}
        )
        desc_truncated = (description or "")[:3500]
        prompt = _JOB_REQUIREMENT_EXTRACTION_PROMPT.format(
            job_title=job_title,
            department=department,
            description=desc_truncated or "No description provided.",
        )

        candidate_models = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
        if getattr(settings, "CV_LLM_MODEL", None) and settings.CV_LLM_MODEL not in candidate_models:
            candidate_models.insert(0, settings.CV_LLM_MODEL)

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.1,
                    ),
                )
                if response and response.text:
                    raw = json.loads(response.text)
                    if isinstance(raw, list) and len(raw) > 0:
                        logger.info(
                            f"Gemini extracted {len(raw)} job requirements for '{job_title}' using {model_name}"
                        )
                        return [r for r in raw if isinstance(r, dict) and r.get("requirement")]
            except Exception as e:
                logger.debug(f"Gemini job requirement extraction failed with {model_name}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Gemini job requirement extraction initialization error: {e}")

    return []


def _heuristic_extract_job_requirements(
    job_title: str, department: str, description: str
) -> List[Dict[str, Any]]:
    """
    Minimal heuristic extraction when Gemini is unavailable.
    Extracts experience requirements from common patterns.
    """
    requirements = []
    combined = f"{job_title} {department} {description}".lower()

    # Pattern: X+ years of [domain] experience
    exp_patterns = [
        (r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:total\s+)?it\s+experience", "Total IT Experience", "REQUIRED_EXPERIENCE"),
        (r"(\d+)\+?\s*years?\s+(?:of\s+)?(?:total\s+)?(?:relevant\s+|work\s+|professional\s+)?experience", "Total Experience", "REQUIRED_EXPERIENCE"),
        (r"(\d+)\+?\s*years?\s+(?:of\s+)?business\s+arch", "Business Architecture Experience", "REQUIRED_ARCHITECTURE"),
        (r"(\d+)\+?\s*years?\s+(?:of\s+)?business\s+anal", "Business Analysis Experience", "REQUIRED_EXPERIENCE"),
    ]
    seen_requirements = set()
    for pattern, req_name, category in exp_patterns:
        m = re.search(pattern, combined)
        if m and req_name not in seen_requirements:
            requirements.append({
                "requirement": req_name,
                "category": category,
                "required_value": f"{m.group(1)}+ years",
            })
            seen_requirements.add(req_name)

    # Common framework mentions
    framework_keywords = [
        ("zachman", "Zachman Framework", "REQUIRED_FRAMEWORKS"),
        ("bpmn", "BPMN", "REQUIRED_FRAMEWORKS"),
        ("togaf", "TOGAF", "REQUIRED_FRAMEWORKS"),
        ("itil", "ITIL", "REQUIRED_FRAMEWORKS"),
        ("agile", "Agile / Scrum", "REQUIRED_SKILLS"),
        ("scrum", "Scrum", "REQUIRED_SKILLS"),
    ]
    for keyword, req_name, category in framework_keywords:
        if keyword in combined and req_name not in seen_requirements:
            requirements.append({
                "requirement": req_name,
                "category": category,
                "required_value": req_name,
            })
            seen_requirements.add(req_name)

    # Government/public sector
    if any(kw in combined for kw in ["ontario government", "ops experience", "public sector", "government experience"]):
        if "Government / Public Sector Experience" not in seen_requirements:
            requirements.append({
                "requirement": "Government / Public Sector Experience",
                "category": "REQUIRED_DOMAIN",
                "required_value": "Government / Public Sector Experience",
            })

    logger.info(f"Heuristic extracted {len(requirements)} job requirements for '{job_title}'")
    return requirements


# ---------------------------------------------------------------------------
# Step 2 — Deterministic Checks (pure Python, no LLM)
# ---------------------------------------------------------------------------


def run_deterministic_checks(
    candidate_years_exp: float,
    candidate_experience: List[Dict[str, Any]],
    job_requirements: List[Dict[str, Any]],
    candidate_education: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Evaluate requirements that can be assessed deterministically (no LLM).
    Returns a list of pre-evaluated results to pass into the LLM prompt,
    so the model cannot override numeric facts or verified credentials.

    Evaluates:
    - Experience year requirements (numeric comparison against CV roles)
    - Education / academic degree requirements (when candidate_education is provided)
    """
    pre_evaluated: List[Dict[str, Any]] = []

    for req in job_requirements:
        req_name = req.get("requirement", "")
        category = req.get("category", "")
        required_value = req.get("required_value", "")
        req_lower = req_name.lower()

        # 1. Total Experience Check
        is_total_exp = (
            any(kw in req_lower for kw in ["total", "overall", "work experience", "it experience", "professional experience", "years of experience"])
            or category == "REQUIRED_EXPERIENCE"
        )

        year_match = re.search(r"(\d+(?:\.\d+)?)\+?\s*years?", required_value.lower())
        if is_total_exp and year_match:
            required_years = float(year_match.group(1))
            actual_years = candidate_years_exp

            # Rich CV evidence citing companies and roles
            role_summaries = []
            for e in (candidate_experience or [])[:4]:
                t = e.get("job_title", "").strip()
                c = e.get("company", "").strip()
                if t and c:
                    role_summaries.append(f"{t} ({c})")
                elif t:
                    role_summaries.append(t)
            role_text = f" across {len(candidate_experience)} roles: " + ", ".join(role_summaries) if role_summaries else ""
            cv_evidence = f"{candidate_years_exp:.1f} years of professional experience documented in CV{role_text}."

            if actual_years >= required_years:
                status = RequirementStatus.SUPPORTED.value
                reasoning = (
                    f"CV documents {actual_years:.1f} years, meeting and exceeding the {required_years:g}+ year requirement."
                )
            elif actual_years >= required_years * 0.8:
                status = RequirementStatus.PARTIALLY_SUPPORTED.value
                shortfall = required_years - actual_years
                reasoning = (
                    f"CV documents {actual_years:.1f} years against the {required_years:g}+ year target ({shortfall:.1f} yr gap, near senior threshold)."
                )
            else:
                status = RequirementStatus.NOT_MET.value
                shortfall = required_years - actual_years
                reasoning = (
                    f"CV documents {actual_years:.1f} years, which is {shortfall:.1f} years below "
                    f"the {required_years:g}+ year requirement. This is a documented shortfall, not merely absent evidence."
                )

            pre_evaluated.append({
                "requirement": req_name,
                "category": category if category in ("MANDATORY", "REQUIRED_EXPERIENCE") else "MANDATORY",
                "required_value": required_value,
                "status": status,
                "cv_evidence": cv_evidence,
                "reasoning": reasoning,
                "deterministic": True,
            })
            continue

        # 2. Education & Academic Qualifications Check
        is_edu = any(kw in req_lower for kw in ["education", "academic", "degree", "diploma", "qualification"])
        if is_edu and candidate_education is not None:
            edu_details = []
            for ed in (candidate_education or []):
                deg = ed.get("degree", "").strip()
                inst = ed.get("institution", "").strip()
                yr = ed.get("graduation_year", "").strip() if ed.get("graduation_year") else ""
                if deg and inst:
                    edu_details.append(f"{deg} from {inst}" + (f" ({yr})" if yr else ""))
                elif deg:
                    edu_details.append(deg + (f" ({yr})" if yr else ""))

            if edu_details:
                status = RequirementStatus.SUPPORTED.value
                cv_evidence = f"Documented academic qualification: {', '.join(edu_details)}."
                reasoning = f"Candidate holds {', '.join(edu_details)}, satisfying educational criteria."
            else:
                status = RequirementStatus.NOT_DEMONSTRATED.value
                cv_evidence = "No explicit degree or diploma documented in CV."
                reasoning = "Academic credentials were not explicitly identified in the CV."

            pre_evaluated.append({
                "requirement": req_name,
                "category": category if category in ("MANDATORY", "REQUIRED_EXPERIENCE") else "MANDATORY",
                "required_value": required_value,
                "status": status,
                "cv_evidence": cv_evidence,
                "reasoning": reasoning,
                "deterministic": True,
            })

    return pre_evaluated


# ---------------------------------------------------------------------------
# Step 3 — Semantic Analysis (Gemini with pre-evaluated facts)
# ---------------------------------------------------------------------------

_SEMANTIC_ANALYSIS_PROMPT = """You are an expert HR analyst performing evidence-based CV requirement analysis.

Your task is to evaluate a candidate's CV against a job's structured requirements and produce
a detailed, evidence-grounded analysis that HR can use to understand the candidate.

CRITICAL RULES — READ CAREFULLY:
1. NOT_DEMONSTRATED means: The CV does not provide sufficient evidence that the requirement is satisfied.
   Use this when the CV is simply SILENT on a topic.
   Example: Job requires Zachman Framework. CV never mentions Zachman → NOT_DEMONSTRATED.

2. NOT_MET means: The CV contains EXPLICIT evidence that the requirement is NOT satisfied.
   Use this ONLY when there is a clear documented gap (e.g., documented years below requirement).
   Example: Required 10+ years. CV explicitly states 7+ years → NOT_MET.

3. SUPPORTED means: The CV contains clear evidence satisfying the requirement.

4. PARTIALLY_SUPPORTED means: The CV shows related experience but does not fully establish the requirement.
   Example: Job requires "Business Architect experience". CV shows Business Analyst experience
   and process mapping, but no explicit Business Architect title or architecture deliverables.

5. DO NOT fabricate CV quotes or skills not present in the CV text.
6. DO NOT infer government experience from geography alone.
7. DO NOT treat related skills as identical without explicit evidence.
8. DO NOT make a hiring verdict, recommendation, or decision.
9. DO NOT use the words "Hire", "Reject", "Strong Candidate", or "Weak Candidate".
10. Pre-evaluated requirements (marked as deterministic=true) have FIXED status values. You must include
    them unchanged in your output — do NOT reassign their status.

For each requirement, provide:
- requirement: exact name from the requirement list
- category: same category from the requirement list
- required_value: same required_value from the requirement list
- status: SUPPORTED | NOT_MET | NOT_DEMONSTRATED | PARTIALLY_SUPPORTED
- cv_evidence: Either a direct quote/summary from the CV proving the status, OR
  "No explicit evidence found in CV." if NOT_DEMONSTRATED
- reasoning: One concise sentence explaining the classification

---

Job Title: {job_title}
Department: {department}

Structured Job Requirements:
{requirements_json}

Pre-Evaluated Requirements (FIXED — do not change their status):
{deterministic_json}

Candidate Profile:
- Name: {candidate_name}
- Total Years of Experience: {years_exp}
- Skills: {skills_list}
- Education:
{education_summary}
- Employment History:
{experience_summary}

CV Text (first 3000 chars):
---
{cv_text_excerpt}
---

Return ONLY a valid JSON object with EXACTLY this schema:
{{
  "mandatory_requirements": [
    {{
      "requirement": "...",
      "category": "MANDATORY",
      "required_value": "...",
      "status": "SUPPORTED|NOT_MET|NOT_DEMONSTRATED|PARTIALLY_SUPPORTED",
      "cv_evidence": "...",
      "reasoning": "..."
    }}
  ],
  "supported_requirements": [ ... ],
  "partially_supported_requirements": [ ... ],
  "not_demonstrated_requirements": [ ... ]
}}

Place each evaluated requirement in the correct bucket based on its status:
- MANDATORY category requirements → mandatory_requirements list
- SUPPORTED → supported_requirements
- PARTIALLY_SUPPORTED → partially_supported_requirements
- NOT_DEMONSTRATED or NOT_MET (non-mandatory) → not_demonstrated_requirements

Exception: A MANDATORY requirement that is NOT_MET or NOT_DEMONSTRATED still goes in mandatory_requirements.
"""


def run_semantic_analysis(
    candidate_name: str,
    candidate_years_exp: float,
    candidate_skills: List[str],
    candidate_experience: List[Dict[str, Any]],
    cv_text: str,
    job_title: str,
    department: str,
    job_requirements: List[Dict[str, Any]],
    deterministic_results: List[Dict[str, Any]],
    candidate_education: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Call Gemini to perform semantic requirement evaluation.
    Deterministic results are included as immutable pre-evaluated facts.
    Returns raw parsed dict or None if Gemini fails.
    """
    if not settings.GEMINI_API_KEY:
        logger.info("Gemini API key not configured — skipping semantic analysis.")
        return None

    # Separate requirements not already deterministically evaluated
    det_requirement_names = {d["requirement"].lower() for d in deterministic_results}
    remaining_requirements = [
        r for r in job_requirements
        if r.get("requirement", "").lower() not in det_requirement_names
    ]

    # Format experience summary
    exp_lines = []
    for exp in (candidate_experience or [])[:5]:
        title = exp.get("job_title") or "Role"
        company = exp.get("company") or "Company"
        duration = exp.get("duration") or ""
        resp = exp.get("responsibilities") or []
        resp_str = "; ".join(resp[:2]) if resp else ""
        line = f"  • {title} at {company} [{duration}]"
        if resp_str:
            line += f" — {resp_str}"
        exp_lines.append(line)
    experience_summary = "\n".join(exp_lines) if exp_lines else "  • No detailed employment history available."

    # Format education summary
    edu_lines = []
    for ed in (candidate_education or []):
        deg = ed.get("degree") or "Degree"
        inst = ed.get("institution") or "Institution"
        yr = ed.get("graduation_year") or ""
        edu_lines.append(f"  • {deg} from {inst}" + (f" [{yr}]" if yr else ""))
    education_summary = "\n".join(edu_lines) if edu_lines else "  • No formal education explicitly listed."

    skills_str = ", ".join(candidate_skills[:30]) if candidate_skills else "None explicitly listed"
    cv_excerpt = (cv_text or "")[:3000]

    # Build deterministic results for prompt (stripped of internal flag)
    deterministic_for_prompt = [
        {k: v for k, v in d.items() if k != "deterministic"}
        for d in deterministic_results
    ]

    prompt = _SEMANTIC_ANALYSIS_PROMPT.format(
        job_title=job_title,
        department=department,
        requirements_json=json.dumps(remaining_requirements, indent=2),
        deterministic_json=json.dumps(deterministic_for_prompt, indent=2),
        candidate_name=candidate_name or "Candidate",
        years_exp=f"{candidate_years_exp:.1f}",
        skills_list=skills_str,
        education_summary=education_summary,
        experience_summary=experience_summary,
        cv_text_excerpt=cv_excerpt,
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=settings.GEMINI_API_KEY, http_options={"timeout": 20000}
        )

        candidate_models = ["gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]
        if getattr(settings, "CV_LLM_MODEL", None) and settings.CV_LLM_MODEL not in candidate_models:
            candidate_models.insert(0, settings.CV_LLM_MODEL)

        for model_name in candidate_models:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.15,
                    ),
                )
                if response and response.text:
                    parsed = json.loads(response.text)
                    if isinstance(parsed, dict) and (
                        "mandatory_requirements" in parsed
                        or "supported_requirements" in parsed
                        or "key_observations" in parsed
                    ):
                        logger.info(
                            f"Semantic requirement analysis completed for '{candidate_name}' "
                            f"vs '{job_title}' using {model_name}"
                        )
                        return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"Gemini semantic analysis returned invalid JSON ({model_name}): {e}")
                continue
            except Exception as e:
                logger.debug(f"Gemini semantic analysis failed with {model_name}: {e}")
                continue

    except Exception as e:
        logger.warning(f"Gemini semantic analysis initialization error: {e}")

    return None


# ---------------------------------------------------------------------------
# Step 4 — Orchestrator: generate_requirement_analysis()
# ---------------------------------------------------------------------------


def _merge_deterministic_into_analysis(
    analysis_dict: Dict[str, Any],
    deterministic_results: List[Dict[str, Any]],
    job_requirements: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Ensure all deterministic results are present in the analysis dict,
    and enforce their status and evidence so LLM cannot override them.
    Guarantees Total Professional Experience is placed at index 0 of mandatory_requirements,
    followed by Education.
    """
    det_map = {d["requirement"].lower(): d for d in deterministic_results}

    # Clean existing occurrences from all buckets so we can place deterministic items cleanly
    for bucket in ("mandatory_requirements", "supported_requirements",
                   "partially_supported_requirements", "not_demonstrated_requirements"):
        filtered = []
        for item in analysis_dict.get(bucket, []):
            if isinstance(item, dict):
                req_lower = item.get("requirement", "").lower()
                if req_lower in det_map:
                    continue  # We will re-inject the exact deterministic fact
            filtered.append(item)
        analysis_dict[bucket] = filtered

    # Re-inject deterministic items at the TOP of mandatory_requirements
    # Order: Experience first, then Education
    sorted_dets = sorted(
        deterministic_results,
        key=lambda d: 0 if any(kw in d["requirement"].lower() for kw in ["total", "experience", "years"]) else 1
    )

    injected = []
    for det in sorted_dets:
        item = {k: v for k, v in det.items() if k != "deterministic"}
        injected.append(item)

    analysis_dict["mandatory_requirements"] = injected + analysis_dict.get("mandatory_requirements", [])
    return analysis_dict


def _build_fallback_analysis(
    candidate_name: str,
    candidate_years_exp: float,
    candidate_skills: List[str],
    job_title: str,
    job_requirements: List[Dict[str, Any]],
    deterministic_results: List[Dict[str, Any]],
    candidate_experience: Optional[List[Dict[str, Any]]] = None,
    candidate_education: Optional[List[Dict[str, Any]]] = None,
) -> OverallAnalysis:
    """
    Build an evidence-grounded OverallAnalysis when Gemini is unavailable or fails.
    Uses deterministic checks for Experience & Education, and checks candidate skills
    and work experience against requirement keywords to produce true match data.
    """
    mandatory_items: List[RequirementAnalysisItem] = []
    supported_items: List[RequirementAnalysisItem] = []
    partial_items: List[RequirementAnalysisItem] = []
    not_demonstrated: List[RequirementAnalysisItem] = []

    # 1. Include deterministic results
    det_names = set()
    for det in deterministic_results:
        try:
            item = RequirementAnalysisItem(
                requirement=det["requirement"],
                category=RequirementCategory(det.get("category", "MANDATORY")),
                required_value=det["required_value"],
                status=RequirementStatus(det["status"]),
                cv_evidence=det["cv_evidence"],
                reasoning=det["reasoning"],
            )
            mandatory_items.append(item)
            det_names.add(det["requirement"].lower())
        except Exception:
            pass

    # Sort mandatory so Experience is 0, Education is 1
    def _priority_score(item: RequirementAnalysisItem) -> int:
        req_lower = item.requirement.lower()
        if any(kw in req_lower for kw in ["total", "years of experience", "professional experience", "it experience"]):
            return 0
        if any(kw in req_lower for kw in ["education", "academic", "degree", "diploma"]):
            return 1
        return 2

    mandatory_items.sort(key=_priority_score)

    # 2. Match remaining requirements against candidate skills and experience text
    lower_skills = {s.lower(): s for s in candidate_skills}
    all_exp_text = " ".join(
        f"{e.get('job_title', '')} {e.get('company', '')} "
        + " ".join(e.get("responsibilities", [])[:3])
        for e in (candidate_experience or [])
    ).lower()

    for req in job_requirements:
        req_name = req.get("requirement", "")
        if req_name.lower() in det_names:
            continue

        req_lower = req_name.lower()
        req_category = req.get("category", "OTHER")
        try:
            cat_enum = RequirementCategory(req_category)
        except Exception:
            cat_enum = RequirementCategory.OTHER

        # Check for direct or partial skill matches
        matched_skills = [
            orig for l_s, orig in lower_skills.items()
            if l_s in req_lower or any(word in l_s for word in req_lower.split() if len(word) > 3)
        ]

        if matched_skills:
            item = RequirementAnalysisItem(
                requirement=req_name,
                category=cat_enum,
                required_value=req.get("required_value", req_name),
                status=RequirementStatus.SUPPORTED,
                cv_evidence=f"Explicitly documented in candidate skills: {', '.join(matched_skills[:3])}.",
                reasoning=f"Candidate's documented profile includes {', '.join(matched_skills[:2])}, aligning with this requirement.",
            )
            if cat_enum == RequirementCategory.MANDATORY:
                mandatory_items.append(item)
            else:
                supported_items.append(item)
        elif any(term in all_exp_text for term in req_lower.split() if len(term) > 4):
            item = RequirementAnalysisItem(
                requirement=req_name,
                category=cat_enum,
                required_value=req.get("required_value", req_name),
                status=RequirementStatus.PARTIALLY_SUPPORTED,
                cv_evidence="Related responsibilities and project experience documented in employment history.",
                reasoning=f"Candidate has related background in {req_name} based on documented work history.",
            )
            partial_items.append(item)
        else:
            item = RequirementAnalysisItem(
                requirement=req_name,
                category=cat_enum,
                required_value=req.get("required_value", req_name),
                status=RequirementStatus.NOT_DEMONSTRATED,
                cv_evidence=f"No explicit mention of '{req_name}' identified in CV.",
                reasoning=f"Candidate CV does not explicitly demonstrate {req_name}.",
            )
            not_demonstrated.append(item)

    return OverallAnalysis(
        key_observations=[],
        mandatory_requirements=mandatory_items,
        supported_requirements=supported_items,
        partially_supported_requirements=partial_items,
        not_demonstrated_requirements=not_demonstrated,
    )


def _validate_and_build_analysis(
    raw: Dict[str, Any],
    job_requirements: List[Dict[str, Any]],
    deterministic_results: List[Dict[str, Any]],
) -> OverallAnalysis:
    """
    Validate Gemini output strictly via Pydantic.
    Invalid individual items are skipped (not silently accepted).
    Guarantees Total Professional Experience is placed at index 0 and Education at index 1.
    """
    def _parse_items(raw_list: Any) -> List[RequirementAnalysisItem]:
        items = []
        if not isinstance(raw_list, list):
            return items
        for entry in raw_list:
            if not isinstance(entry, dict):
                continue
            try:
                # Normalize status/category to uppercase for enum safety
                if "status" in entry:
                    entry["status"] = str(entry["status"]).upper()
                if "category" in entry:
                    entry["category"] = str(entry["category"]).upper()
                items.append(RequirementAnalysisItem(**entry))
            except (ValidationError, ValueError) as e:
                logger.debug(f"Skipping invalid requirement item: {entry} — {e}")
        return items

    # Ensure deterministic results are present and prioritized
    raw = _merge_deterministic_into_analysis(raw, deterministic_results, job_requirements)

    mandatory = _parse_items(raw.get("mandatory_requirements", []))
    supported = _parse_items(raw.get("supported_requirements", []))
    partially_supported = _parse_items(raw.get("partially_supported_requirements", []))
    not_demonstrated = _parse_items(raw.get("not_demonstrated_requirements", []))

    # Guarantee priority sorting in mandatory:
    # 1. Total Professional Experience
    # 2. Education & Academic Qualifications
    def _priority_score(item: RequirementAnalysisItem) -> int:
        req_lower = item.requirement.lower()
        if any(kw in req_lower for kw in ["total", "years of experience", "professional experience", "it experience"]):
            return 0
        if any(kw in req_lower for kw in ["education", "academic", "degree", "diploma"]):
            return 1
        return 2

    mandatory.sort(key=_priority_score)

    return OverallAnalysis(
        key_observations=[],
        mandatory_requirements=mandatory,
        supported_requirements=supported,
        partially_supported_requirements=partially_supported,
        not_demonstrated_requirements=not_demonstrated,
    )


def generate_requirement_analysis(
    position_id: str,
    job_title: str,
    department: str,
    job_description: str,
    candidate_name: str,
    candidate_years_exp: float,
    candidate_skills: List[str],
    candidate_experience: List[Dict[str, Any]],
    cv_text: str,
    candidate_education: Optional[List[Dict[str, Any]]] = None,
) -> Optional[OverallAnalysis]:
    """
    Orchestrate the full evidence-based requirement analysis pipeline.

    Returns an OverallAnalysis Pydantic model, or None if a critical failure
    prevents even a minimal fallback from being produced.

    This function is SAFE to call multiple times (idempotent):
    - Job requirements are cached per position_id.
    - Results must be stored by the caller (service.py).
    """
    try:
        # 1. Extract structured job requirements (Gemini, cached)
        # Guarantees REQ #1 is Total Professional Experience and REQ #2 is Education
        job_requirements = extract_structured_job_requirements(
            position_id=position_id,
            job_title=job_title,
            department=department,
            description=job_description,
        )

        if not job_requirements:
            logger.warning(
                f"No job requirements could be extracted for '{job_title}' (position {position_id}). "
                "Requirement analysis will be minimal."
            )

        # 2. Deterministic checks (pure Python, no LLM)
        deterministic_results = run_deterministic_checks(
            candidate_years_exp=candidate_years_exp,
            candidate_experience=candidate_experience,
            job_requirements=job_requirements,
            candidate_education=candidate_education,
        )
        logger.debug(
            f"Deterministic checks produced {len(deterministic_results)} pre-evaluated requirements."
        )

        # 3. Semantic analysis (Gemini with pre-evaluated facts)
        raw_analysis = run_semantic_analysis(
            candidate_name=candidate_name,
            candidate_years_exp=candidate_years_exp,
            candidate_skills=candidate_skills,
            candidate_experience=candidate_experience,
            cv_text=cv_text,
            job_title=job_title,
            department=department,
            job_requirements=job_requirements,
            deterministic_results=deterministic_results,
            candidate_education=candidate_education,
        )

        if raw_analysis is None:
            logger.warning(
                f"Semantic analysis unavailable for '{candidate_name}' vs '{job_title}'. "
                "Using evidence-based fallback analysis."
            )
            return _build_fallback_analysis(
                candidate_name=candidate_name,
                candidate_years_exp=candidate_years_exp,
                candidate_skills=candidate_skills,
                job_title=job_title,
                job_requirements=job_requirements,
                deterministic_results=deterministic_results,
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
            )

        # 4. Validate and build final OverallAnalysis
        analysis = _validate_and_build_analysis(raw_analysis, job_requirements, deterministic_results)
        logger.info(
            f"Requirement analysis complete for '{candidate_name}' vs '{job_title}': "
            f"{len(analysis.mandatory_requirements)} mandatory, "
            f"{len(analysis.supported_requirements)} supported, "
            f"{len(analysis.partially_supported_requirements)} partial, "
            f"{len(analysis.not_demonstrated_requirements)} not demonstrated."
        )
        return analysis

    except Exception as e:
        logger.error(
            f"generate_requirement_analysis() failed for '{candidate_name}' vs '{job_title}': {e}",
            exc_info=True,
        )
        # Return a safe fallback rather than propagating the exception
        try:
            return _build_fallback_analysis(
                candidate_name=candidate_name or "Candidate",
                candidate_years_exp=candidate_years_exp,
                candidate_skills=candidate_skills or [],
                job_title=job_title,
                job_requirements=job_requirements if 'job_requirements' in locals() else [],
                deterministic_results=deterministic_results if 'deterministic_results' in locals() else [],
                candidate_experience=candidate_experience,
                candidate_education=candidate_education,
            )
        except Exception:
            return None
