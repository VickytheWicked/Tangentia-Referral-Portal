from datetime import datetime
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, field_validator


# -------------------------------------------------------------------------
# Pydantic schemas for Gemini structured output extraction
# -------------------------------------------------------------------------

class EducationItem(BaseModel):
    degree: Optional[str] = Field(default=None, description="Degree or qualification name")
    institution: Optional[str] = Field(default=None, description="College, university or school name")
    graduation_year: Optional[Union[str, int]] = Field(default=None, description="Graduation year if specified")
    field_of_study: Optional[str] = Field(default=None, description="Specialization, major or branch if specified")
    grade_or_score: Optional[str] = Field(default=None, description="CGPA, percentage, or honors grade if specified")

    @field_validator("graduation_year", mode="before")
    def coerce_graduation_year(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class ExperienceItem(BaseModel):
    company: Optional[str] = Field(default=None, description="Employer or organization name")
    job_title: Optional[str] = Field(default=None, description="Role or job title held")
    duration: Optional[str] = Field(default=None, description="Employment dates or duration")
    responsibilities: List[str] = Field(default_factory=list, description="Key responsibilities or accomplishments")


class ProjectItem(BaseModel):
    name: Optional[str] = Field(default=None, description="Project title")
    description: Optional[str] = Field(default=None, description="Project summary")
    technologies: List[str] = Field(default_factory=list, description="Technologies / tools used")


class CertificationItem(BaseModel):
    name: Optional[str] = Field(default=None, description="Certification name")
    issuer: Optional[str] = Field(default=None, description="Issuing organization")
    year: Optional[Union[str, int]] = Field(default=None, description="Year earned if available")

    @field_validator("year", mode="before")
    def coerce_year(cls, v: Any) -> Optional[str]:
        if v is None:
            return None
        return str(v).strip()


class CandidateProfileExtraction(BaseModel):
    candidate_name: Optional[str] = Field(default=None, description="Full candidate name")
    email: Optional[str] = Field(default=None, description="Contact email address")
    phone: Optional[str] = Field(default=None, description="Contact phone number")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    github_url: Optional[str] = Field(default=None, description="GitHub profile URL")
    years_of_experience: float = Field(default=0.0, description="Total years of professional experience")
    skills: List[str] = Field(default_factory=list, description="List of technical and professional skills")
    education: List[EducationItem] = Field(default_factory=list, description="Educational background")
    experience: List[ExperienceItem] = Field(default_factory=list, description="Work experience history")
    projects: List[ProjectItem] = Field(default_factory=list, description="Key projects")
    certifications: List[CertificationItem] = Field(default_factory=list, description="Professional certifications")

    @field_validator("years_of_experience", mode="before")
    def coerce_years(cls, v: Any) -> float:
        if v is None:
            return 0.0
        if isinstance(v, (int, float)):
            return float(v)
        try:
            import re
            m = re.search(r"(\d+(\.\d+)?)", str(v))
            return float(m.group(1)) if m else 0.0
        except Exception:
            return 0.0


# -------------------------------------------------------------------------
# API Response Schemas for HR Suggestions UI
# -------------------------------------------------------------------------

class JobMatchItem(BaseModel):
    id: str
    position_id: str
    match_level: str
    matched_skills: List[str]
    missing_skills: List[str]
    experience_match: Optional[str] = None
    explanation: List[str]
    fit_summary: Optional[str] = None


class SuggestedCandidateSummary(BaseModel):
    referral_id: str
    candidate_name: str
    candidate_email: str
    original_filename: str
    extraction_status: str
    match_level: Optional[str] = None
    years_of_experience: float = 0.0
    matched_skills: List[str] = Field(default_factory=list)
    missing_skills: List[str] = Field(default_factory=list)
    explanation: List[str] = Field(default_factory=list)
    fit_summary: Optional[str] = None
    referral_status: str
    referred_at: datetime
    priority_score: int = 0


class OpeningSuggestionsResponse(BaseModel):
    position_id: str
    title: str
    department: str
    location: str
    employment_type: str
    description: Optional[str] = None
    expected_skills: List[str] = Field(default_factory=list)
    min_experience_years: float = 0.0
    selection_criteria: List[str] = Field(default_factory=list)
    key_qualities: List[str] = Field(default_factory=list)
    hiring_guidance: Optional[str] = None
    strong_matches: List[SuggestedCandidateSummary]
    good_matches: List[SuggestedCandidateSummary]
    potential_matches: List[SuggestedCandidateSummary]
    pending_extraction: List[SuggestedCandidateSummary]
    failed_extraction: List[SuggestedCandidateSummary]
    total_candidates: int


class CandidateProfileDetailResponse(BaseModel):
    id: Optional[str] = None
    referral_id: str
    referral_number: Optional[str] = None
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    years_of_experience: float = 0.0
    skills: List[str] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)
    extraction_status: str
    extraction_error: Optional[str] = None
    extracted_at: Optional[datetime] = None
    match: Optional[JobMatchItem] = None
    original_filename: str
    position_title: str
    position_id: str
    referral_status: str
    referred_by_name: Optional[str] = None
    referred_by_email: Optional[str] = None
    relationship: Optional[str] = None
    referral_note: Optional[str] = None
    created_at: Optional[datetime] = None
