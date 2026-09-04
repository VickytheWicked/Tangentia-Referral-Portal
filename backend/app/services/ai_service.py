from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any


@dataclass
class ParsedResumeData:
    skills: List[str]
    education: List[str]
    experience_years: float
    summary: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


@dataclass
class JobMatchScore:
    match_score: int  # 0 to 100
    strengths: List[str]
    skill_gaps: List[str]
    recommendation_summary: str


class AIServiceInterface(ABC):
    """
    Extensible interface for AI enhancements (Azure OpenAI / Anthropic / LLMs).
    Ready for zero-downtime plug-in without modifying core portal workflows.
    """

    @abstractmethod
    async def parse_resume(self, cv_bytes: bytes, mime_type: str) -> ParsedResumeData:
        """Extract structured entities and skills from CV binary"""
        pass

    @abstractmethod
    async def score_job_match(
        self,
        resume_data: ParsedResumeData,
        job_description: str,
    ) -> JobMatchScore:
        """Evaluate candidate fit against job requirements"""
        pass

    @abstractmethod
    async def generate_recruiter_summary(
        self,
        resume_data: ParsedResumeData,
        referral_note: str,
    ) -> str:
        """Create a 3-bullet concise summary for HR review"""
        pass


class StubAIService(AIServiceInterface):
    """
    MVP Stub implementation demonstrating readiness for future LLM integration.
    """

    async def parse_resume(self, cv_bytes: bytes, mime_type: str) -> ParsedResumeData:
        return ParsedResumeData(
            skills=["Python", "FastAPI", "React", "PostgreSQL", "Cloud Architecture"],
            education=["B.S. in Computer Science"],
            experience_years=4.5,
            summary="Experienced full-stack engineer with strong background in enterprise cloud platforms.",
        )

    async def score_job_match(
        self,
        resume_data: ParsedResumeData,
        job_description: str,
    ) -> JobMatchScore:
        return JobMatchScore(
            match_score=88,
            strengths=["Strong backend API experience", "Relational database expertise", "React fundamentals"],
            skill_gaps=["SharePoint Graph SDK specific nuances"],
            recommendation_summary="High candidate alignment with opening technical requirements.",
        )

    async def generate_recruiter_summary(
        self,
        resume_data: ParsedResumeData,
        referral_note: str,
    ) -> str:
        return f"Referral Highlight: {referral_note}\nCore Qualifications: {', '.join(resume_data.skills[:4])} with {resume_data.experience_years} years experience."


# Service instance factory
def get_ai_service() -> AIServiceInterface:
    return StubAIService()
