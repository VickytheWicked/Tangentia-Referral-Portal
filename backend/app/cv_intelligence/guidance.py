import os
import re
import json
import logging
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger("cv_intelligence")

_GUIDANCE_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "hr_guidance_cache.json",
)

# In-memory cache for generated guidance per role to keep page loads fast
_GUIDANCE_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_guidance_cache():
    if os.path.exists(_GUIDANCE_CACHE_FILE):
        try:
            with open(_GUIDANCE_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    _GUIDANCE_CACHE.update(data)
                    logger.info(f"Loaded {len(_GUIDANCE_CACHE)} cached HR guidance entries from {_GUIDANCE_CACHE_FILE}")
        except Exception as e:
            logger.warning(f"Failed to read guidance cache file: {e}")


def _save_guidance_cache():
    try:
        os.makedirs(os.path.dirname(_GUIDANCE_CACHE_FILE), exist_ok=True)
        with open(_GUIDANCE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_GUIDANCE_CACHE, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to persist guidance cache file: {e}")


_load_guidance_cache()

ROLE_KNOWLEDGE_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "business architect": {
        "hiring_guidance": "Prioritize candidates who demonstrate proven capability in translating complex enterprise business challenges into structured architecture models (BPMN, BRD, user stories) and aligning technical solutions with executive strategic goals.",
        "selection_criteria": [
            "Verify hands-on experience developing conceptual, logical, and business functional architecture models (BPMN / Zachman framework).",
            "Assess ability to lead stakeholder consensus workshops across business executives and engineering squads.",
            "Check practical experience authoring Epics, Features, and prioritized Product Backlogs within Agile/Scrum delivery models.",
            "Evaluate familiarity with change governance, business impact analysis, and enterprise system integration."
        ],
        "key_qualities": [
            "Strategic Systems Thinking",
            "Stakeholder Consensus Building",
            "Enterprise Architecture Rigor",
            "Agile Governance & Leadership"
        ]
    },
    "rpa": {
        "hiring_guidance": "Focus on candidates with demonstrable end-to-end bot deployment experience in production enterprise environments, emphasizing robust exception handling and unattended bot stability over classroom knowledge.",
        "selection_criteria": [
            "Verify hands-on expertise building and deploying automated workflows in Automation Anywhere (A360) or Power Automate.",
            "Assess proficiency in writing modular script logic (Python/VBScript) with resilient error handling and audit logging.",
            "Check experience integrating with enterprise APIs, databases, and Intelligent Document Processing (IQ Bot / OCR).",
            "Evaluate ability to participate in process discovery, calculate automation ROI, and support client UAT."
        ],
        "key_qualities": [
            "Process Optimization Mindset",
            "Autonomous Bot Troubleshooting",
            "Production Stability & Security Focus",
            "Cross-Functional Collaboration"
        ]
    },
    "cloud": {
        "hiring_guidance": "Seek architects who combine hands-on multi-cloud engineering (AWS/Azure) with high-level system design, cost governance, and security posture across enterprise microservices.",
        "selection_criteria": [
            "Assess proven track record in designing resilient, highly available multi-region microservices on AWS or Azure.",
            "Verify depth in container orchestration (Kubernetes, Docker), CI/CD pipelines, and Infrastructure as Code.",
            "Check practical implementation of Zero-Trust security, IAM policies, and cloud cost governance.",
            "Evaluate experience communicating architectural decisions and trade-offs to senior leadership."
        ],
        "key_qualities": [
            "Visionary System Design",
            "Cost & Performance Governance",
            "Technical Mentorship",
            "Pragmatic Engineering Trade-Offs"
        ]
    },
    "ai & machine learning": {
        "hiring_guidance": "Prioritize candidates with practical deployment experience in Generative AI, RAG pipelines, and LLM applications who understand hallucination mitigation and latency optimization in production.",
        "selection_criteria": [
            "Evaluate hands-on experience building RAG architectures, vector search integrations, and agentic workflows (LangChain / LlamaIndex).",
            "Assess understanding of prompt engineering patterns, few-shot techniques, and structured JSON output validation.",
            "Check proficiency in Python backend frameworks, API integration, and model performance benchmarking.",
            "Verify awareness of AI safety, hallucination reduction, and cost-effective token management."
        ],
        "key_qualities": [
            "Experimental Scientific Rigor",
            "Agentic AI & Prompt Craftsmanship",
            "Product-Centric Engineering",
            "Curiosity & Rapid Continuous Learning"
        ]
    },
    "qa": {
        "hiring_guidance": "Look for QA professionals who combine automated test framework development with strong exploratory testing acumen, ensuring quality is baked into the CI/CD pipeline from day one.",
        "selection_criteria": [
            "Verify experience architecting scalable test automation suites using Selenium, Cypress, or Playwright.",
            "Check depth in API testing (Postman, REST), performance benchmarking, and automated regression suites.",
            "Assess ability to write concise, reproducible bug reports and manage defect lifecycles in Jira.",
            "Evaluate collaboration with developers during sprint planning and acceptance criteria definition."
        ],
        "key_qualities": [
            "Meticulous Eye for Edge Cases",
            "Defect Prevention Mindset",
            "Collaborative Quality Advocacy",
            "Automation-First Engineering"
        ]
    },
    "it support": {
        "hiring_guidance": "Select professionals who combine structured hardware/networking troubleshooting with proactive customer empathy and SLA discipline across Windows Server and cloud services.",
        "selection_criteria": [
            "Assess hands-on troubleshooting across Windows Server, Active Directory, VPN, and enterprise networking.",
            "Verify foundational cloud administration in AWS or Microsoft 365 and endpoint security.",
            "Check experience with ITIL incident management, RCA documentation, and strict SLA compliance.",
            "Evaluate clear communication and patience when assisting non-technical business users."
        ],
        "key_qualities": [
            "User Empathy & Calm Composure",
            "Methodical Diagnostic Thinking",
            "SLA Discipline & Ownership",
            "Infrastructure Security Awareness"
        ]
    },
    "sales": {
        "hiring_guidance": "Look for high-impact commercial leaders with a verified record of driving multi-million-dollar B2B enterprise tech sales, pre-sales solutioning, and executive C-suite client relationships.",
        "selection_criteria": [
            "Verify consistent history of closing enterprise technology contracts and exceeding revenue targets.",
            "Assess ability to architect high-value commercial proposals, pricing models, and contract negotiations.",
            "Check experience leading pre-sales technical solutioning and articulating complex ROI to C-level executives.",
            "Evaluate leadership track record in mentoring sales teams and managing global partner pipelines."
        ],
        "key_qualities": [
            "Strategic Commercial Acumen",
            "C-Suite Relationship Building",
            "Inspiring Sales Leadership",
            "Value-Driven Solution Selling"
        ]
    },
    "backend": {
        "hiring_guidance": "Prioritize developers who write clean, maintainable, and high-performance Python/FastAPI code with a deep focus on API design, asynchronous processing, and database optimization.",
        "selection_criteria": [
            "Assess expertise in Python, FastAPI/Django, asynchronous programming, and RESTful API architecture.",
            "Verify practical database optimization skills (PostgreSQL/SQL query tuning, indexing, and migrations).",
            "Check experience containerizing services with Docker and deploying via automated CI/CD pipelines.",
            "Evaluate adherence to clean code principles, unit testing, and architectural documentation."
        ],
        "key_qualities": [
            "Clean Code & Modularity",
            "Performance Optimization Mindset",
            "API Architecture Clarity",
            "Dependability & Ownership"
        ]
    },
    "frontend": {
        "hiring_guidance": "Select frontend engineers who combine pixel-perfect visual craft and design system empathy with robust TypeScript/React architecture and smooth web performance.",
        "selection_criteria": [
            "Assess mastery of modern React, TypeScript, responsive layout design, and state management.",
            "Evaluate precision in translating Figma/UI-UX designs into accessible, responsive web interfaces.",
            "Check experience building reusable design system components and optimizing web vitals/page load speed.",
            "Verify understanding of frontend testing, build tooling (Vite/Webpack), and API integration."
        ],
        "key_qualities": [
            "Visual Craft & User Empathy",
            "Architectural Modularity",
            "Performance & Accessibility Focus",
            "Design-to-Code Precision"
        ]
    },
    "databricks": {
        "hiring_guidance": "Look for data architects with proven experience designing scalable enterprise lakehouses on Databricks and Spark, with strong data modeling and governance practices.",
        "selection_criteria": [
            "Verify experience architecting end-to-end data pipelines using Databricks, Apache Spark, and PySpark.",
            "Assess understanding of Medallion Architecture (Bronze/Silver/Gold), Delta Lake, and data quality checks.",
            "Check proficiency in cloud storage integrations (AWS S3, Azure Data Lake) and SQL performance tuning.",
            "Evaluate experience establishing data governance, lineage, and enterprise security policies."
        ],
        "key_qualities": [
            "Data Pipeline Scalability",
            "Lakehouse Architectural Vision",
            "Data Governance Discipline",
            "Analytical Precision"
        ]
    },
    "devops": {
        "hiring_guidance": "Seek engineers who treat infrastructure as code and champion site reliability, automated observability, and zero-downtime deployment pipelines.",
        "selection_criteria": [
            "Assess experience designing CI/CD pipelines (GitHub Actions, GitLab CI) and Kubernetes/Docker orchestration.",
            "Verify depth in Infrastructure as Code using Terraform or CloudFormation across AWS/Azure.",
            "Check implementation of monitoring, alerting, and log aggregation (Prometheus, Grafana, ELK).",
            "Evaluate disaster recovery planning, incident response readiness, and security hardening."
        ],
        "key_qualities": [
            "Automate-Everything Mindset",
            "Incident Resilience & SRE Discipline",
            "Security-First Engineering",
            "Collaborative Operations Culture"
        ]
    }
}


def _generate_gemini_guidance(
    job_title: str,
    department: str,
    description: str,
    min_exp_years: float = 0.0,
    expected_skills: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Call Google Gemini to generate structured HR advisory guidance from the CATS job description.
    Provides consultative screening guidance for HR recruiters who may not have domain expertise.
    """
    if not settings.GEMINI_API_KEY:
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.GEMINI_API_KEY, http_options={"timeout": 12000})

        desc_text = description.strip() if description else ""
        if len(desc_text) > 3500:
            desc_text = desc_text[:3500] + "..."

        skills_str = ", ".join(expected_skills) if expected_skills else "Not specified"
        exp_str = f"{min_exp_years:g}+ years" if min_exp_years > 0 else "Not specified"

        prompt = f"""You are an expert HR hiring advisor for Tangentia, a global enterprise technology company.
The HR recruitment team is evaluating candidates for the job opening below (sourced from Tangentia's CATS Careers portal: https://tangentia.catsone.com/careers/9463).
HR recruiters may not have deep technical knowledge for every specialized role. Provide clear, practical, consultative guidance to help HR evaluate and screen candidates effectively.

Return a JSON object with EXACTLY these three fields:
- "hiring_guidance": (string) A concise 2-3 sentence strategic recommendation for HR. Clearly explain what core competency matters most, how to distinguish a genuinely capable practitioner from a superficial one, and what critical signal or red flag HR should look for.
- "selection_criteria": (array of 3 to 4 strings) Concrete, actionable screening questions or verification criteria HR can evaluate from the resume or introductory phone screen.
- "key_qualities": (array of 4 short strings, 2-4 words each) Key qualities, traits, or domain competencies that define an ideal candidate for this role.

Job Title: {job_title}
Department: {department}
Target Experience: {exp_str}
Key Skills: {skills_str}

Job Description:
{desc_text or "No detailed description provided; generate based on role title and department."}

Respond ONLY with valid JSON conforming to the schema above.
"""

        candidate_models = [
            "gemini-3.6-flash",
            "gemini-flash-latest",
            "gemini-3.5-flash-lite",
        ]
        if settings.CV_LLM_MODEL and settings.CV_LLM_MODEL not in candidate_models:
            candidate_models.append(settings.CV_LLM_MODEL)

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
                    guidance = parsed.get("hiring_guidance", "").strip()
                    criteria = parsed.get("selection_criteria", [])
                    qualities = parsed.get("key_qualities", [])

                    if (
                        guidance
                        and isinstance(criteria, list)
                        and len(criteria) >= 2
                        and isinstance(qualities, list)
                        and len(qualities) >= 2
                    ):
                        logger.info(f"Generated Gemini HR guidance for '{job_title}' using model '{model_name}'")
                        return {
                            "hiring_guidance": guidance,
                            "selection_criteria": [str(c).strip() for c in criteria if str(c).strip()][:4],
                            "key_qualities": [str(q).strip() for q in qualities if str(q).strip()][:4],
                        }
            except Exception as e:
                last_error = e
                logger.debug(f"Gemini guidance attempt with model '{model_name}' failed: {e}")
                continue

        if last_error:
            logger.warning(f"Gemini HR guidance generation failed for '{job_title}': {last_error}")
    except Exception as e:
        logger.warning(f"Error initializing Gemini client for HR guidance: {e}")

    return None


def get_hr_decision_guidance(
    position_id: str,
    job_title: str,
    department: str,
    description: str,
    min_exp_years: float = 0.0,
    expected_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate or retrieve AI-suggested candidate selection criteria and evaluation qualities for HR.
    Provides consultative guidance to help HR evaluate and decide on candidates for this opening.
    """
    cache_key = f"{position_id}:{job_title.lower()}"
    if cache_key in _GUIDANCE_CACHE:
        return _GUIDANCE_CACHE[cache_key]

    # 1. Attempt Gemini-powered dynamic guidance based on the CATS job description
    ai_guidance = _generate_gemini_guidance(
        job_title=job_title,
        department=department,
        description=description,
        min_exp_years=min_exp_years,
        expected_skills=expected_skills,
    )
    if ai_guidance:
        _GUIDANCE_CACHE[cache_key] = ai_guidance
        _save_guidance_cache()
        return ai_guidance

    # 2. Fallback to curated role knowledge templates if Gemini is unavailable
    title_lower = job_title.lower()
    desc_lower = (description or "").lower()

    # Match best knowledge template based on title keywords
    matched_template = None
    for key, template in ROLE_KNOWLEDGE_TEMPLATES.items():
        if key in title_lower:
            matched_template = template
            break

    # Secondary check in description if not in title
    if not matched_template:
        for key, template in ROLE_KNOWLEDGE_TEMPLATES.items():
            if key in desc_lower:
                matched_template = template
                break

    # Default template if completely novel role
    if not matched_template:
        exp_mention = f"with at least {min_exp_years:g}+ years of experience " if min_exp_years > 0 else ""
        matched_template = {
            "hiring_guidance": f"Evaluate candidates {exp_mention}based on practical track record, domain execution quality, and alignment with {department} goals.",
            "selection_criteria": [
                f"Verify verifiable hands-on delivery in core competencies required for {job_title}.",
                "Assess ability to independently problem-solve and adapt to project requirements.",
                "Check past experience collaborating cross-functionally across engineering and business teams.",
                "Evaluate communication clarity, professional ownership, and initiative."
            ],
            "key_qualities": [
                "Domain Execution Mastery",
                "Proactive Problem Solving",
                "Cross-Functional Teamwork",
                "Professional Ownership"
            ]
        }

    # Format result
    result = {
        "hiring_guidance": matched_template["hiring_guidance"],
        "selection_criteria": matched_template["selection_criteria"],
        "key_qualities": matched_template["key_qualities"],
    }

    _GUIDANCE_CACHE[cache_key] = result
    _save_guidance_cache()
    return result
