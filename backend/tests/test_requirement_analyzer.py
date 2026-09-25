"""
Tests for the Evidence-Based CV Requirement Analysis Pipeline
=============================================================

Covers:
  - RequirementStatus / RequirementCategory Pydantic models
  - run_deterministic_checks() (pure Python, no mocking needed)
  - _build_fallback_analysis()
  - _validate_and_build_analysis()
  - generate_requirement_analysis() (Gemini mocked)
  - Idempotency of reprocessing
  - Gemini failure handling
  - Malformed LLM output handling
  - NOT_DEMONSTRATED vs NOT_MET distinction
  - Numeric experience requirements
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.cv_intelligence.requirement_analyzer import (
    RequirementStatus,
    RequirementCategory,
    RequirementAnalysisItem,
    OverallAnalysis,
    run_deterministic_checks,
    _build_fallback_analysis,
    _validate_and_build_analysis,
    generate_requirement_analysis,
    _merge_deterministic_into_analysis,
)
from app.cv_intelligence.schemas import (
    RequirementStatus as SchemaRequirementStatus,
    RequirementCategory as SchemaRequirementCategory,
    RequirementAnalysisItem as SchemaRequirementAnalysisItem,
    OverallAnalysis as SchemaOverallAnalysis,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_JOB_REQUIREMENTS = [
    {
        "requirement": "Total IT Experience",
        "category": "MANDATORY",
        "required_value": "10+ years",
    },
    {
        "requirement": "Business Architecture Experience",
        "category": "REQUIRED_ARCHITECTURE",
        "required_value": "5+ years",
    },
    {
        "requirement": "Zachman Framework",
        "category": "REQUIRED_FRAMEWORKS",
        "required_value": "Zachman Framework",
    },
    {
        "requirement": "Business Analysis",
        "category": "REQUIRED_SKILLS",
        "required_value": "Business Analysis",
    },
    {
        "requirement": "Ontario Government Experience",
        "category": "REQUIRED_DOMAIN",
        "required_value": "Ontario Government / OPS Experience",
    },
]

SAMPLE_CANDIDATE_EXPERIENCE = [
    {
        "company": "Acme Corp",
        "job_title": "Business Analyst",
        "duration": "2018-2025",
        "responsibilities": [
            "Requirements gathering and BRD documentation",
            "Process mapping (As-Is / To-Be)",
            "Stakeholder management",
        ],
    }
]


# ---------------------------------------------------------------------------
# 1. Pydantic schema validation
# ---------------------------------------------------------------------------

class TestRequirementSchemas:
    def test_requirement_status_values(self):
        assert RequirementStatus.SUPPORTED == "SUPPORTED"
        assert RequirementStatus.NOT_MET == "NOT_MET"
        assert RequirementStatus.NOT_DEMONSTRATED == "NOT_DEMONSTRATED"
        assert RequirementStatus.PARTIALLY_SUPPORTED == "PARTIALLY_SUPPORTED"

    def test_requirement_category_values(self):
        assert RequirementCategory.MANDATORY == "MANDATORY"
        assert RequirementCategory.REQUIRED_FRAMEWORKS == "REQUIRED_FRAMEWORKS"
        assert RequirementCategory.PREFERRED == "PREFERRED"

    def test_requirement_analysis_item_valid(self):
        item = RequirementAnalysisItem(
            requirement="Business Analysis",
            category=RequirementCategory.REQUIRED_SKILLS,
            required_value="Business Analysis experience",
            status=RequirementStatus.SUPPORTED,
            cv_evidence="Business Analysis, BRD, process mapping documented in CV.",
            reasoning="Candidate explicitly lists business analysis as a core skill.",
        )
        assert item.status == RequirementStatus.SUPPORTED
        assert item.category == RequirementCategory.REQUIRED_SKILLS

    def test_requirement_analysis_item_invalid_status(self):
        with pytest.raises(ValidationError):
            RequirementAnalysisItem(
                requirement="Test",
                category=RequirementCategory.MANDATORY,
                required_value="X",
                status="INVALID_STATUS",
                cv_evidence="N/A",
                reasoning="N/A",
            )

    def test_overall_analysis_defaults(self):
        analysis = OverallAnalysis(key_observations=["One observation."])
        assert len(analysis.mandatory_requirements) == 0
        assert len(analysis.supported_requirements) == 0
        assert len(analysis.partially_supported_requirements) == 0
        assert len(analysis.not_demonstrated_requirements) == 0

    def test_overall_analysis_serialization_roundtrip(self):
        item = RequirementAnalysisItem(
            requirement="Process Mapping",
            category=RequirementCategory.REQUIRED_SKILLS,
            required_value="Process mapping experience",
            status=RequirementStatus.SUPPORTED,
            cv_evidence="Process Mapping (As-Is / To-Be) listed in skills.",
            reasoning="Directly documented in CV.",
        )
        analysis = OverallAnalysis(
            key_observations=["Process mapping is documented."],
            supported_requirements=[item],
        )
        json_str = analysis.model_dump_json()
        restored = OverallAnalysis.model_validate_json(json_str)
        assert len(restored.supported_requirements) == 1
        assert restored.supported_requirements[0].requirement == "Process Mapping"

    def test_schema_pydantic_models_match_analyzer_models(self):
        """Ensure schemas.py and requirement_analyzer.py use compatible definitions."""
        assert SchemaRequirementStatus.SUPPORTED == RequirementStatus.SUPPORTED
        assert SchemaRequirementStatus.NOT_MET == RequirementStatus.NOT_MET
        assert SchemaRequirementCategory.MANDATORY == RequirementCategory.MANDATORY


# ---------------------------------------------------------------------------
# 2. Deterministic checks — pure Python, no mocks
# ---------------------------------------------------------------------------

class TestDeterministicChecks:
    def test_total_experience_not_met(self):
        """7 yrs documented when 10+ required → NOT_MET."""
        results = run_deterministic_checks(
            candidate_years_exp=7.0,
            candidate_experience=SAMPLE_CANDIDATE_EXPERIENCE,
            job_requirements=[
                {"requirement": "Total IT Experience", "category": "MANDATORY", "required_value": "10+ years"}
            ],
        )
        assert len(results) == 1
        assert results[0]["status"] == RequirementStatus.NOT_MET.value
        assert "7.0" in results[0]["cv_evidence"]
        assert results[0]["deterministic"] is True

    def test_total_experience_supported(self):
        """12 yrs documented when 10+ required → SUPPORTED."""
        results = run_deterministic_checks(
            candidate_years_exp=12.0,
            candidate_experience=SAMPLE_CANDIDATE_EXPERIENCE,
            job_requirements=[
                {"requirement": "Total IT Experience", "category": "MANDATORY", "required_value": "10+ years"}
            ],
        )
        assert len(results) == 1
        assert results[0]["status"] == RequirementStatus.SUPPORTED.value

    def test_exact_match_experience(self):
        """Exactly 10 yrs when 10+ required → SUPPORTED."""
        results = run_deterministic_checks(
            candidate_years_exp=10.0,
            candidate_experience=[],
            job_requirements=[
                {"requirement": "Total IT Experience", "category": "REQUIRED_EXPERIENCE", "required_value": "10+ years"}
            ],
        )
        assert results[0]["status"] == RequirementStatus.SUPPORTED.value

    def test_non_numeric_requirement_skipped(self):
        """Non-experience requirements are skipped by deterministic checks."""
        results = run_deterministic_checks(
            candidate_years_exp=7.0,
            candidate_experience=[],
            job_requirements=[
                {"requirement": "Zachman Framework", "category": "REQUIRED_FRAMEWORKS", "required_value": "Zachman Framework"}
            ],
        )
        # Should not appear in deterministic results — no years to evaluate
        assert len(results) == 0

    def test_multiple_requirements_mixed(self):
        """Only experience requirements are evaluated deterministically."""
        results = run_deterministic_checks(
            candidate_years_exp=5.0,
            candidate_experience=[],
            job_requirements=SAMPLE_JOB_REQUIREMENTS,
        )
        # Only "Total IT Experience" matches the pattern for total experience
        total_exp_results = [r for r in results if "Total" in r["requirement"]]
        assert len(total_exp_results) == 1
        assert total_exp_results[0]["status"] == RequirementStatus.NOT_MET.value

    def test_zero_experience_not_met(self):
        """0 yrs when 3+ required → NOT_MET."""
        results = run_deterministic_checks(
            candidate_years_exp=0.0,
            candidate_experience=[],
            job_requirements=[
                {"requirement": "Total Experience", "category": "REQUIRED_EXPERIENCE", "required_value": "3+ years"}
            ],
        )
        assert results[0]["status"] == RequirementStatus.NOT_MET.value


# ---------------------------------------------------------------------------
# 3. NOT_DEMONSTRATED vs NOT_MET distinction
# ---------------------------------------------------------------------------

class TestNotDemonstratedVsNotMet:
    def test_absent_requirement_is_not_demonstrated_not_not_met(self):
        """
        When CV is silent on a topic (e.g. Zachman Framework),
        the fallback system must use NOT_DEMONSTRATED — not NOT_MET.
        """
        analysis = _build_fallback_analysis(
            candidate_name="Test Candidate",
            candidate_years_exp=7.0,
            candidate_skills=["Business Analysis", "Process Mapping"],
            job_title="Business Architect",
            job_requirements=[
                {
                    "requirement": "Zachman Framework",
                    "category": "REQUIRED_FRAMEWORKS",
                    "required_value": "Zachman Framework",
                }
            ],
            deterministic_results=[],
        )
        # Zachman should be NOT_DEMONSTRATED (absent evidence), not NOT_MET
        zachman_items = [
            item for item in analysis.not_demonstrated_requirements
            if item.requirement == "Zachman Framework"
        ]
        assert len(zachman_items) == 1
        assert zachman_items[0].status == RequirementStatus.NOT_DEMONSTRATED

    def test_numeric_shortfall_is_not_met_not_not_demonstrated(self):
        """
        7 yrs documented against 10+ requirement → NOT_MET (explicit shortfall).
        This must NOT be classified as NOT_DEMONSTRATED.
        """
        det_results = run_deterministic_checks(
            candidate_years_exp=7.0,
            candidate_experience=[],
            job_requirements=[
                {"requirement": "Total IT Experience", "category": "MANDATORY", "required_value": "10+ years"}
            ],
        )
        assert det_results[0]["status"] == RequirementStatus.NOT_MET.value
        assert det_results[0]["status"] != RequirementStatus.NOT_DEMONSTRATED.value


# ---------------------------------------------------------------------------
# 4. Fallback analysis
# ---------------------------------------------------------------------------

class TestBuildFallbackAnalysis:
    def test_fallback_produces_valid_overall_analysis(self):
        analysis = _build_fallback_analysis(
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=["Business Analysis", "Agile"],
            job_title="Business Architect",
            job_requirements=SAMPLE_JOB_REQUIREMENTS,
            deterministic_results=[],
        )
        assert isinstance(analysis, OverallAnalysis)
        assert len(analysis.key_observations) >= 1
        # All non-deterministic requirements should be NOT_DEMONSTRATED
        for item in analysis.not_demonstrated_requirements:
            assert item.status == RequirementStatus.NOT_DEMONSTRATED

    def test_fallback_with_deterministic_results(self):
        det_results = [
            {
                "requirement": "Total IT Experience",
                "category": "MANDATORY",
                "required_value": "10+ years",
                "status": RequirementStatus.NOT_MET.value,
                "cv_evidence": "7.0 years documented",
                "reasoning": "Below 10 year threshold.",
                "deterministic": True,
            }
        ]
        analysis = _build_fallback_analysis(
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=[],
            job_title="Business Architect",
            job_requirements=SAMPLE_JOB_REQUIREMENTS,
            deterministic_results=det_results,
        )
        # Deterministic NOT_MET should be in mandatory
        mandatory_names = [i.requirement for i in analysis.mandatory_requirements]
        assert "Total IT Experience" in mandatory_names

    def test_fallback_does_not_generate_hiring_verdicts(self):
        analysis = _build_fallback_analysis(
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=[],
            job_title="Business Architect",
            job_requirements=SAMPLE_JOB_REQUIREMENTS,
            deterministic_results=[],
        )
        verdict_words = {"hire", "reject", "strong candidate", "weak candidate", "recommended"}
        for obs in analysis.key_observations:
            for word in verdict_words:
                assert word.lower() not in obs.lower(), \
                    f"Observation contains hiring verdict: '{obs}'"


# ---------------------------------------------------------------------------
# 5. Validate and build analysis from raw LLM output
# ---------------------------------------------------------------------------

class TestValidateAndBuildAnalysis:
    def _sample_raw(self):
        return {
            "key_observations": [
                "7+ years of experience documented.",
                "Business Analyst background with process mapping.",
            ],
            "mandatory_requirements": [
                {
                    "requirement": "Total IT Experience",
                    "category": "MANDATORY",
                    "required_value": "10+ years",
                    "status": "NOT_MET",
                    "cv_evidence": "7+ years of experience",
                    "reasoning": "CV documents 7 years, below 10+ requirement.",
                }
            ],
            "supported_requirements": [
                {
                    "requirement": "Business Analysis",
                    "category": "REQUIRED_SKILLS",
                    "required_value": "Business Analysis",
                    "status": "SUPPORTED",
                    "cv_evidence": "Business Analysis listed prominently.",
                    "reasoning": "Directly documented.",
                }
            ],
            "partially_supported_requirements": [],
            "not_demonstrated_requirements": [
                {
                    "requirement": "Zachman Framework",
                    "category": "REQUIRED_FRAMEWORKS",
                    "required_value": "Zachman Framework",
                    "status": "NOT_DEMONSTRATED",
                    "cv_evidence": "No explicit evidence found in CV.",
                    "reasoning": "Not mentioned in CV.",
                }
            ],
        }

    def test_valid_raw_builds_correctly(self):
        raw = self._sample_raw()
        analysis = _validate_and_build_analysis(raw, SAMPLE_JOB_REQUIREMENTS, [])
        assert isinstance(analysis, OverallAnalysis)
        assert len(analysis.mandatory_requirements) >= 1
        assert len(analysis.supported_requirements) >= 1
        assert len(analysis.not_demonstrated_requirements) >= 1

    def test_invalid_status_item_is_skipped(self):
        raw = self._sample_raw()
        raw["supported_requirements"].append({
            "requirement": "Bad Item",
            "category": "REQUIRED_SKILLS",
            "required_value": "Something",
            "status": "TOTALLY_INVALID",   # Invalid status
            "cv_evidence": "N/A",
            "reasoning": "N/A",
        })
        # Should skip the invalid item, not crash
        analysis = _validate_and_build_analysis(raw, SAMPLE_JOB_REQUIREMENTS, [])
        supported_names = [i.requirement for i in analysis.supported_requirements]
        assert "Bad Item" not in supported_names
        assert "Business Analysis" in supported_names

    def test_deterministic_results_are_merged_if_missing(self):
        """If Gemini drops a deterministic result, it should be re-injected."""
        raw = self._sample_raw()
        # Remove Total IT Experience from mandatory (simulate Gemini dropping it)
        raw["mandatory_requirements"] = []

        det_results = [
            {
                "requirement": "Total IT Experience",
                "category": "MANDATORY",
                "required_value": "10+ years",
                "status": RequirementStatus.NOT_MET.value,
                "cv_evidence": "7.0 years documented",
                "reasoning": "Below threshold.",
                "deterministic": True,
            }
        ]
        analysis = _validate_and_build_analysis(raw, SAMPLE_JOB_REQUIREMENTS, det_results)
        mandatory_names = [i.requirement for i in analysis.mandatory_requirements]
        assert "Total IT Experience" in mandatory_names

    def test_empty_observations_handled(self):
        raw = self._sample_raw()
        raw["key_observations"] = []
        analysis = _validate_and_build_analysis(raw, SAMPLE_JOB_REQUIREMENTS, [])
        assert isinstance(analysis.key_observations, list)


# ---------------------------------------------------------------------------
# 6. Full pipeline — Gemini mocked
# ---------------------------------------------------------------------------

class TestGenerateRequirementAnalysis:
    def _make_gemini_response(self, text: str):
        mock_resp = MagicMock()
        mock_resp.text = text
        return mock_resp

    def _sample_gemini_json(self):
        return json.dumps({
            "key_observations": ["7+ years documented.", "Business Analyst background."],
            "mandatory_requirements": [
                {
                    "requirement": "Total IT Experience",
                    "category": "MANDATORY",
                    "required_value": "10+ years",
                    "status": "NOT_MET",
                    "cv_evidence": "7+ years stated.",
                    "reasoning": "Below 10 year threshold.",
                }
            ],
            "supported_requirements": [
                {
                    "requirement": "Business Analysis",
                    "category": "REQUIRED_SKILLS",
                    "required_value": "Business Analysis",
                    "status": "SUPPORTED",
                    "cv_evidence": "Business Analysis listed.",
                    "reasoning": "Documented.",
                }
            ],
            "partially_supported_requirements": [],
            "not_demonstrated_requirements": [
                {
                    "requirement": "Zachman Framework",
                    "category": "REQUIRED_FRAMEWORKS",
                    "required_value": "Zachman Framework",
                    "status": "NOT_DEMONSTRATED",
                    "cv_evidence": "No explicit evidence found in CV.",
                    "reasoning": "Not mentioned.",
                }
            ],
        })

    @patch("app.cv_intelligence.requirement_analyzer.settings")
    def test_no_gemini_key_returns_fallback(self, mock_settings):
        """When GEMINI_API_KEY is absent, return a fallback analysis (not None)."""
        mock_settings.GEMINI_API_KEY = ""
        mock_settings.CV_LLM_MODEL = None

        result = generate_requirement_analysis(
            position_id="pos-001",
            job_title="Business Architect",
            department="IT",
            job_description="Requires 10+ years IT experience and Zachman Framework.",
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=["Business Analysis"],
            candidate_experience=SAMPLE_CANDIDATE_EXPERIENCE,
            cv_text="7+ years experience as Business Analyst.",
        )
        # Should return a fallback, not None
        assert result is not None
        assert isinstance(result, OverallAnalysis)

    @patch("app.cv_intelligence.requirement_analyzer.settings")
    @patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements")
    @patch("app.cv_intelligence.requirement_analyzer.run_semantic_analysis")
    def test_gemini_success_returns_structured_analysis(
        self, mock_semantic, mock_job_req, mock_settings
    ):
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.CV_LLM_MODEL = None

        mock_job_req.return_value = SAMPLE_JOB_REQUIREMENTS
        mock_semantic.return_value = json.loads(self._sample_gemini_json())

        result = generate_requirement_analysis(
            position_id="pos-001",
            job_title="Business Architect",
            department="IT",
            job_description="Requires 10+ years IT and Zachman.",
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=["Business Analysis"],
            candidate_experience=SAMPLE_CANDIDATE_EXPERIENCE,
            cv_text="7+ years experience as Business Analyst.",
        )
        assert result is not None
        assert isinstance(result, OverallAnalysis)
        assert len(result.key_observations) >= 1

    @patch("app.cv_intelligence.requirement_analyzer.settings")
    @patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements")
    @patch("app.cv_intelligence.requirement_analyzer.run_semantic_analysis")
    def test_gemini_failure_returns_fallback(
        self, mock_semantic, mock_job_req, mock_settings
    ):
        """Gemini semantic analysis failure → fallback OverallAnalysis, not exception."""
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.CV_LLM_MODEL = None

        mock_job_req.return_value = SAMPLE_JOB_REQUIREMENTS
        mock_semantic.return_value = None  # Simulate Gemini returning None

        result = generate_requirement_analysis(
            position_id="pos-001",
            job_title="Business Architect",
            department="IT",
            job_description="Requires 10+ years.",
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=[],
            candidate_experience=[],
            cv_text="",
        )
        assert result is not None
        assert isinstance(result, OverallAnalysis)

    @patch("app.cv_intelligence.requirement_analyzer.settings")
    @patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements")
    @patch("app.cv_intelligence.requirement_analyzer.run_semantic_analysis")
    def test_malformed_gemini_json_handled_safely(
        self, mock_semantic, mock_job_req, mock_settings
    ):
        """Malformed Gemini output → items with invalid schema are skipped, not crash."""
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.CV_LLM_MODEL = None

        mock_job_req.return_value = SAMPLE_JOB_REQUIREMENTS

        # Malformed: missing required fields, invalid status
        mock_semantic.return_value = {
            "key_observations": ["Some observation"],
            "mandatory_requirements": [
                {
                    "requirement": "Total IT Experience",
                    "category": "MANDATORY",
                    "required_value": "10+ years",
                    "status": "GARBAGE_VALUE",   # Invalid
                    "cv_evidence": "...",
                    "reasoning": "...",
                }
            ],
            "supported_requirements": [],
            "partially_supported_requirements": [],
            "not_demonstrated_requirements": [],
        }

        result = generate_requirement_analysis(
            position_id="pos-001",
            job_title="Business Architect",
            department="IT",
            job_description="Requires 10+ years.",
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=[],
            candidate_experience=[],
            cv_text="7 years experience.",
        )
        # Must not raise — invalid items skipped
        assert result is not None
        assert isinstance(result, OverallAnalysis)

    @patch("app.cv_intelligence.requirement_analyzer.settings")
    @patch("app.cv_intelligence.requirement_analyzer._gemini_extract_job_requirements")
    @patch("app.cv_intelligence.requirement_analyzer.run_semantic_analysis")
    def test_analysis_is_idempotent(self, mock_semantic, mock_job_req, mock_settings):
        """Running generate_requirement_analysis twice returns equivalent results."""
        mock_settings.GEMINI_API_KEY = "fake-key"
        mock_settings.CV_LLM_MODEL = None

        mock_job_req.return_value = SAMPLE_JOB_REQUIREMENTS
        gemini_output = json.loads(self._sample_gemini_json())
        mock_semantic.return_value = gemini_output

        kwargs = dict(
            position_id="pos-001",
            job_title="Business Architect",
            department="IT",
            job_description="Requires 10+ years.",
            candidate_name="Jane Doe",
            candidate_years_exp=7.0,
            candidate_skills=["Business Analysis"],
            candidate_experience=SAMPLE_CANDIDATE_EXPERIENCE,
            cv_text="7+ years experience.",
        )

        result1 = generate_requirement_analysis(**kwargs)
        result2 = generate_requirement_analysis(**kwargs)

        assert result1 is not None
        assert result2 is not None
        # Key structure must be identical
        assert len(result1.mandatory_requirements) == len(result2.mandatory_requirements)
        assert len(result1.supported_requirements) == len(result2.supported_requirements)


# ---------------------------------------------------------------------------
# 7. Merge deterministic helper
# ---------------------------------------------------------------------------

class TestMergeDeterministic:
    def test_already_present_items_not_duplicated(self):
        raw = {
            "key_observations": [],
            "mandatory_requirements": [
                {
                    "requirement": "Total IT Experience",
                    "category": "MANDATORY",
                    "required_value": "10+ years",
                    "status": "NOT_MET",
                    "cv_evidence": "7 years",
                    "reasoning": "Below threshold.",
                }
            ],
            "supported_requirements": [],
            "partially_supported_requirements": [],
            "not_demonstrated_requirements": [],
        }
        det = [
            {
                "requirement": "Total IT Experience",
                "category": "MANDATORY",
                "required_value": "10+ years",
                "status": RequirementStatus.NOT_MET.value,
                "cv_evidence": "7 years",
                "reasoning": "Below threshold.",
                "deterministic": True,
            }
        ]
        merged = _merge_deterministic_into_analysis(raw, det, SAMPLE_JOB_REQUIREMENTS)
        # Should not duplicate
        assert len(merged["mandatory_requirements"]) == 1
