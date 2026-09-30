import sys
from types import ModuleType
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException

from app.cv_intelligence.jev_relevance import check_cv_relevance, RelevanceResult
from app.config import settings


def test_jev_relevance_no_api_key():
    """When API key is empty, check_cv_relevance returns safe neutral result without calling API."""
    result = check_cv_relevance(
        cv_snippet="Experienced Python backend engineer with FastAPI and PostgreSQL.",
        position_title="Senior Python Developer",
        position_department="Engineering",
        position_description="Looking for senior Python developer",
        candidate_years_exp=5.0,
        referral_note="Great fit",
        api_key="",
    )
    assert isinstance(result, RelevanceResult)
    assert result.score == 0.5
    assert result.label == "unknown"
    assert result.jev_available is False


def test_jev_relevance_missing_sdk_fallback():
    """When typesafe_sdk is not installed or import fails, check_cv_relevance safely returns neutral."""
    # Ensure typesafe_sdk is treated as unimportable
    with patch.dict(sys.modules, {"typesafe_sdk": None}):
        result = check_cv_relevance(
            cv_snippet="Python developer with 5 years experience.",
            position_title="Senior Python Developer",
            api_key="mock-key",
        )
        assert result.score == 0.5
        assert result.label == "unknown"
        assert result.jev_available is False


def test_jev_relevance_sdk_runtime_exception_fallback():
    """When SDK raises any runtime exception, check_cv_relevance catches it and returns neutral."""
    mock_mod = ModuleType("typesafe_sdk")
    mock_client_class = MagicMock(side_effect=RuntimeError("TypeSafe API connection timeout"))
    mock_mod.TypeSafeClient = mock_client_class
    mock_mod.Noul = MagicMock()

    with patch.dict(sys.modules, {"typesafe_sdk": mock_mod}):
        result = check_cv_relevance(
            cv_snippet="Experienced Python backend engineer.",
            position_title="Senior Python Developer",
            api_key="mock-typesafe-key",
        )
        assert result.score == 0.5
        assert result.label == "unknown"
        assert result.jev_available is False


def test_jev_relevance_success_high_score():
    """When Jev returns a high score (>= 0.65), label is 'high'."""
    mock_answer = MagicMock()
    mock_answer.noul = 0.85
    mock_response = MagicMock()
    mock_response.nouls = {"is_relevant": mock_answer}

    mock_client = MagicMock()
    mock_client.system_one.return_value = mock_response

    mock_mod = ModuleType("typesafe_sdk")
    mock_mod.TypeSafeClient = MagicMock(return_value=mock_client)
    mock_mod.Noul = MagicMock()

    with patch.dict(sys.modules, {"typesafe_sdk": mock_mod}):
        result = check_cv_relevance(
            cv_snippet="5 years Python, Docker, Kubernetes, AWS.",
            position_title="Senior Cloud Engineer",
            position_department="Cloud & Infrastructure",
            position_description="Cloud architect needed",
            candidate_years_exp=5.0,
            referral_note="Colleague",
            api_key="mock-typesafe-key",
        )
        assert result.score == 0.85
        assert result.label == "high"
        assert result.jev_available is True


def test_jev_relevance_success_low_score():
    """When Jev returns a low score (< 0.40), label is 'low'."""
    mock_answer = MagicMock()
    mock_answer.noul = 0.15
    mock_response = MagicMock()
    mock_response.nouls = {"is_relevant": mock_answer}

    mock_client = MagicMock()
    mock_client.system_one.return_value = mock_response

    mock_mod = ModuleType("typesafe_sdk")
    mock_mod.TypeSafeClient = MagicMock(return_value=mock_client)
    mock_mod.Noul = MagicMock()

    with patch.dict(sys.modules, {"typesafe_sdk": mock_mod}):
        result = check_cv_relevance(
            cv_snippet="Kindergarten art teacher with 10 years experience in painting.",
            position_title="Senior DevOps Engineer",
            position_department="Engineering",
            position_description="DevOps engineer for cloud infra",
            candidate_years_exp=10.0,
            referral_note="Friend",
            api_key="mock-typesafe-key",
        )
        assert result.score == 0.15
        assert result.label == "low"
        assert result.jev_available is True


@pytest.mark.asyncio
async def test_referral_submission_with_jev_disabled(db_session, seeded_job, seeded_users, tmp_path):
    """When CV_RELEVANCE_CHECK_ENABLED=False (default), submission runs normally with zero overhead."""
    from app.services.referral_service import create_referral_with_cv
    from app.schemas.referral import ReferralCreateForm
    from app.services.storage.local_service import LocalStorageService
    from unittest.mock import AsyncMock

    mock_file = MagicMock()
    mock_file.filename = "resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.read = AsyncMock(return_value=b"%PDF-1.4 minimal test content")

    form_data = ReferralCreateForm(
        candidate_name="Alice Smith",
        candidate_email="alice.smith@example.com",
        candidate_phone="+1 555-0199",
        years_of_experience=4.0,
        relationship="Former Colleague",
        referral_note="Strong engineer",
        position_id=seeded_job.id,
        candidate_consent=True,
    )

    storage_service = LocalStorageService(storage_dir=str(tmp_path / "storage"))

    referral = await create_referral_with_cv(
        db=db_session,
        form_data=form_data,
        file=mock_file,
        current_user=seeded_users["emp1"],
        storage_service=storage_service,
    )
    assert referral.candidate_name == "Alice Smith"
    assert referral.referral_number.startswith("REF-")


@pytest.mark.asyncio
async def test_referral_submission_with_jev_failure_does_not_crash(db_session, seeded_job, seeded_users, tmp_path, monkeypatch):
    """When Jev check fails or raises an error, submission still proceeds smoothly without crashing."""
    monkeypatch.setattr(settings, "CV_RELEVANCE_CHECK_ENABLED", True)
    monkeypatch.setattr(settings, "TYPESAFE_API_KEY", "dummy-key")

    from app.services.referral_service import create_referral_with_cv
    from app.schemas.referral import ReferralCreateForm
    from app.services.storage.local_service import LocalStorageService
    from unittest.mock import AsyncMock

    mock_file = MagicMock()
    mock_file.filename = "resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.read = AsyncMock(return_value=b"%PDF-1.4 minimal test content")

    form_data = ReferralCreateForm(
        candidate_name="Bob Jones",
        candidate_email="bob.jones@example.com",
        candidate_phone="+1 555-0200",
        years_of_experience=3.0,
        relationship="Former Colleague",
        referral_note="Good candidate",
        position_id=seeded_job.id,
        candidate_consent=True,
    )

    storage_service = LocalStorageService(storage_dir=str(tmp_path / "storage"))

    # Simulate Jev failing completely
    with patch("app.cv_intelligence.jev_relevance.check_cv_relevance", side_effect=Exception("Jev network timeout")):
        with patch("app.cv_intelligence.text_extractor.extract_cv_text", return_value="Some resume text"):
            referral = await create_referral_with_cv(
                db=db_session,
                form_data=form_data,
                file=mock_file,
                current_user=seeded_users["emp1"],
                storage_service=storage_service,
            )
            assert referral.candidate_name == "Bob Jones"


@pytest.mark.asyncio
async def test_referral_submission_with_low_relevance_blocking_enabled(db_session, seeded_job, seeded_users, monkeypatch):
    """When CV_RELEVANCE_BLOCK_ENABLED=True and Jev score < threshold, HTTP 422 is raised."""
    monkeypatch.setattr(settings, "CV_RELEVANCE_CHECK_ENABLED", True)
    monkeypatch.setattr(settings, "CV_RELEVANCE_BLOCK_ENABLED", True)
    monkeypatch.setattr(settings, "CV_RELEVANCE_BLOCK_THRESHOLD", 0.30)
    monkeypatch.setattr(settings, "TYPESAFE_API_KEY", "dummy-key")

    from app.services.referral_service import create_referral_with_cv
    from app.schemas.referral import ReferralCreateForm
    from unittest.mock import AsyncMock

    mock_file = MagicMock()
    mock_file.filename = "resume.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.read = AsyncMock(return_value=b"%PDF-1.4 minimal test content")

    form_data = ReferralCreateForm(
        candidate_name="Irrelevant Candidate",
        candidate_email="irrelevant@example.com",
        candidate_phone="+1 555-0201",
        years_of_experience=1.0,
        relationship="Acquaintance",
        referral_note="Random person",
        position_id=seeded_job.id,
        candidate_consent=True,
    )

    mock_sp = MagicMock()
    mock_sp.upload_cv = AsyncMock()

    low_relevance = RelevanceResult(score=0.15, label="low", jev_available=True)

    with patch("app.cv_intelligence.jev_relevance.check_cv_relevance", return_value=low_relevance):
        with patch("app.cv_intelligence.text_extractor.extract_cv_text", return_value="Unrelated background"):
            with pytest.raises(HTTPException) as exc_info:
                await create_referral_with_cv(
                    db=db_session,
                    form_data=form_data,
                    file=mock_file,
                    current_user=seeded_users["emp1"],
                    storage_service=mock_sp,
                )
            assert exc_info.value.status_code == 422
            assert "does not appear to match" in exc_info.value.detail
            # Ensure storage upload was never called since submission was blocked before upload
            mock_sp.upload_cv.assert_not_called()
