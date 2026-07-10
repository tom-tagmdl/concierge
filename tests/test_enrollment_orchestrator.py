"""Architecture protection tests for the enrollment orchestrator foundation."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from homeassistant.core import HomeAssistant

from custom_components.concierge.enrollment_capture import BrowserMicCaptureProvider
from custom_components.concierge.enrollment_capture import CaptureSampleResult
from custom_components.concierge.enrollment_capture import SatelliteCaptureProvider
from custom_components.concierge.enrollment_orchestrator import EnrollmentOrchestrator
from custom_components.concierge.enrollment_orchestrator import resolve_enrollment_storage_provider_from_hass
from custom_components.concierge.enrollment_session import enrollment_session_for_start
from custom_components.concierge.models import PersonProfile
from custom_components.concierge.models import VoiceProfile
from custom_components.concierge.storage import ConciergeStorage


async def test_orchestrator_preflight_is_fail_closed(hass: HomeAssistant, monkeypatch) -> None:
    """Orchestrator should block enrollment when provider readiness fails."""
    fake_provider = SimpleNamespace(
        validate_ready=lambda: SimpleNamespace(
            ready=False,
            failure_code="storage_unavailable",
            failure_message_safe="external enrollment storage is unavailable",
            provider_type="mounted_path",
        )
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_orchestrator.resolve_enrollment_storage_provider_from_hass",
        lambda hass: fake_provider,
    )
    monkeypatch.setattr(
        "custom_components.concierge.enrollment_orchestrator.async_create_or_update_storage_issue",
        AsyncMock(),
    )

    with pytest.raises(Exception, match="storage_unavailable"):
        await EnrollmentOrchestrator(hass).require_storage_preflight()


async def test_orchestrator_sync_manifest_uses_provider_projection_only(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Orchestrator should synchronize manifest from session authority, not ad hoc payloads."""
    orchestrator = EnrollmentOrchestrator(hass)
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )

    await ConciergeStorage(hass).async_upsert_enrollment_session(session)
    await orchestrator.sync_manifest(session, target_sample_count=3)

    provider = resolve_enrollment_storage_provider_from_hass(hass)
    assert provider is not None
    manifest = provider.read_session_manifest(session.session_id)
    assert manifest is not None
    assert manifest.session_id == session.session_id
    assert manifest.sample_count == session.sample_count
    assert manifest.target_sample_count == 3
    assert not hasattr(manifest, "sample_items")


async def test_orchestrator_cleanup_updates_session_but_does_not_own_lifecycle(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Orchestrator should coordinate cleanup without changing lifecycle authority boundaries."""
    orchestrator = EnrollmentOrchestrator(hass)
    storage = ConciergeStorage(hass)
    session = enrollment_session_for_start(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        existing_sample_items=[],
        enrollment_started_at="2026-07-08T11:00:00+00:00",
    )
    session.metadata["provider_type"] = "browser_microphone"
    await storage.async_upsert_enrollment_session(session)
    await orchestrator.sync_manifest(session, target_sample_count=3)

    provider = resolve_enrollment_storage_provider_from_hass(hass)
    assert provider is not None
    provider.write_sample(session.session_id, 0, "audio/wav", b"sample")

    updated_session, cleanup_summary = await orchestrator.execute_cleanup(
        storage,
        session,
        cleanup_reason="manual",
    )

    assert updated_session.state == session.state
    assert updated_session.cleanup_status == "cleanup_complete"
    assert cleanup_summary["cleanup_result_code"] in {"complete", "already_clean"}


async def test_orchestrator_browser_capture_coordinates_upload_and_registration(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Browser capture should stay orchestration-driven and fail-closed on preflight."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    calls = {"record_sample": 0}

    original_record_sample = EnrollmentOrchestrator.record_sample

    async def _counted_record_sample(self, call_data):
        calls["record_sample"] += 1
        return await original_record_sample(self, call_data)

    monkeypatch.setattr(EnrollmentOrchestrator, "record_sample", _counted_record_sample)

    result = await orchestrator.capture_browser_sample(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        phrase_index=0,
        speech_text="Hello Concierge test phrase",
        audio_content_type="audio/wav",
        audio_bytes=b"audio",
        recording_duration_ms=900,
    )

    assert calls["record_sample"] == 1
    assert result["saved"] is True
    assert result["captured"] is True
    assert result["voice_profile_id"] == "tom_voice"
    assert result["phrase_index"] == 0


async def test_orchestrator_browser_progress_projection_is_session_derived(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Browser progress should be projected from EnrollmentSession without sensitive fields."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Hello Concierge test phrase",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
        }
    )

    result = await orchestrator.get_browser_enrollment_progress(person_id="person.tom")

    assert result["found"] is True
    assert result["voice_profile_id"] == "tom_voice"
    progress = result["progress"]
    assert progress is not None
    assert progress["sample_count"] == 1
    assert progress["target_sample_count"] >= 1
    assert 0 <= progress["completion_percentage"] <= 100
    assert "sample_items" not in progress
    assert "recording_path" not in str(progress)
    assert "speech_text" not in str(progress)
    assert "speaker_embedding_id" not in str(progress)


async def test_orchestrator_cancel_enrollment_is_deterministic_and_idempotent(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Cancel should be deterministic and idempotent for active/terminal session paths."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )

    first = await orchestrator.cancel_enrollment({"person_id": "person.tom", "voice_profile_id": "tom_voice"})
    second = await orchestrator.cancel_enrollment({"person_id": "person.tom", "voice_profile_id": "tom_voice"})

    assert first["canceled"] is True
    assert second["already_terminal"] is True
    assert second["not_found"] is False


async def test_orchestrator_recover_and_resume_are_session_authoritative(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Recovery and resume should use authoritative session projection decisions only."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )

    recovered = await orchestrator.recover_enrollment({"person_id": "person.tom"})
    resumed = await orchestrator.resume_enrollment({"person_id": "person.tom"})

    assert recovered["recoverable"] is True
    assert recovered["recovery_state"] == "resume_available"
    assert resumed["resumed"] is True
    assert resumed["recovery_state"] == "resume_available"
    assert "recording_path" not in str(recovered)
    assert "speech_text" not in str(recovered)


async def test_orchestrator_completion_readiness_is_deterministic(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Completion readiness should be deterministic from session authority and preflight."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    not_ready = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )
    assert not_ready["ready"] is False
    assert not_ready["reason_code"] == "insufficient_samples"

    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    ready = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )
    assert ready["ready"] is True
    assert ready["reason_code"] == "ready"

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is not None
    await storage.async_update_enrollment_session(
        session_id=session.session_id,
        cleanup_status="cleanup_complete",
    )

    ready_with_cleanup_flag = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )
    assert ready_with_cleanup_flag["ready"] is True


async def test_orchestrator_completion_readiness_blocks_when_duration_is_too_short(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Readiness should require minimum usable duration even when sample count is complete."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 700,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 700,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 700,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    readiness = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
            "min_total_duration_ms": 5000,
        }
    )

    assert readiness["ready"] is False
    assert readiness["reason_code"] == "insufficient_duration"
    assert int(readiness["total_duration_ms"]) < int(readiness["min_total_duration_ms"])
    assert any(item.get("reason") == "insufficient_duration" for item in readiness["retry_recommendations"])


async def test_orchestrator_completion_readiness_blocks_when_prompt_categories_lack_diversity(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Readiness should report missing phrase categories with explicit retry guidance."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    for index in range(3):
        await orchestrator.record_sample(
            {
                "voice_profile_id": "tom_voice",
                "speech_text": f"Phrase {index + 1}",
                "phrase_index": index,
                "source": "guided_enrollment_dialog",
                "recording_duration_ms": 12000,
                "prompt_category": "command",
                "capture_distance": "near_field" if index % 2 == 0 else "mid_field",
                "capture_noise": "quiet",
                "quality_pass": True,
            }
        )

    readiness = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )

    assert readiness["ready"] is False
    assert readiness["reason_code"] == "missing_category_coverage"
    assert "question" in readiness["missing_prompt_categories"]
    assert "conversational" in readiness["missing_prompt_categories"]
    assert any(item.get("reason") == "missing_category_coverage" for item in readiness["retry_recommendations"])


async def test_orchestrator_completion_readiness_reports_missing_mid_field_retry_reason(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Readiness should emit explicit mid-field retry taxonomy when coverage is missing."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    readiness = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )

    assert readiness["ready"] is False
    assert readiness["reason_code"] == "missing_mid_field_sample"
    assert any(item.get("reason") == "missing_mid_field_sample" for item in readiness["retry_recommendations"])


async def test_orchestrator_complete_enrollment_uses_voice_identity_generation_result(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Completion should invoke Voice Identity generation and use returned voiceprint ID."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    for index, category in enumerate(("command", "question", "conversational")):
        await orchestrator.record_sample(
            {
                "voice_profile_id": "tom_voice",
                "speech_text": f"Phrase {index + 1}",
                "phrase_index": index,
                "source": "guided_enrollment_dialog",
                "recording_duration_ms": 10000,
                "prompt_category": category,
                "capture_distance": "near_field" if index != 1 else "mid_field",
                "capture_noise": "quiet",
                "quality_pass": True,
            }
        )

    generate_called = {"count": 0}

    async def _fake_generate(self, **kwargs):
        generate_called["count"] += 1
        return {
            "success": True,
            "reason_code": "ready",
            "failure_category": "",
            "voiceprint_id": "vp_generated_001",
            "revision": 4,
        }

    async def _fake_status(self, voiceprint_id):
        return {
            "success": True,
            "voiceprint_id": voiceprint_id,
            "revision": 4,
            "status_summary": "voiceprint_active",
            "lifecycle_status": "active",
            "active": True,
        }

    monkeypatch.setattr(EnrollmentOrchestrator, "_async_generate_voiceprint", _fake_generate)
    monkeypatch.setattr(EnrollmentOrchestrator, "_async_get_voiceprint_status", _fake_status)

    completion = await orchestrator.complete_enrollment(
        {
            "voice_profile_id": "tom_voice",
            "person_id": "person.tom",
            "min_samples": 3,
        }
    )

    assert completion["completed"] is True
    assert completion["voiceprint_id"] == "vp_generated_001"
    assert completion["voiceprint_revision"] == 4
    assert generate_called["count"] == 1

    state = await storage.async_load_state()
    assert state.voice_profiles["tom_voice"].speaker_embedding_id == "vp_generated_001"


async def test_orchestrator_complete_enrollment_generation_failure_preserves_profile(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Generation failure should not mutate existing voiceprint metadata fields."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
            speaker_embedding_id="vp_existing_001",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    for index, category in enumerate(("command", "question", "conversational")):
        await orchestrator.record_sample(
            {
                "voice_profile_id": "tom_voice",
                "speech_text": f"Phrase {index + 1}",
                "phrase_index": index,
                "source": "guided_enrollment_dialog",
                "recording_duration_ms": 10000,
                "prompt_category": category,
                "capture_distance": "near_field" if index != 1 else "mid_field",
                "capture_noise": "quiet",
                "quality_pass": True,
            }
        )

    async def _fake_generate_failure(self, **kwargs):
        _ = kwargs
        return {
            "success": False,
            "reason_code": "generation_failed",
            "failure_category": "operation_failed",
            "voiceprint_id": "",
            "revision": None,
        }

    monkeypatch.setattr(EnrollmentOrchestrator, "_async_generate_voiceprint", _fake_generate_failure)

    with pytest.raises(Exception, match="generation_failed"):
        await orchestrator.complete_enrollment(
            {
                "voice_profile_id": "tom_voice",
                "person_id": "person.tom",
                "min_samples": 3,
            }
        )

    state = await storage.async_load_state()
    assert state.voice_profiles["tom_voice"].speaker_embedding_id == "vp_existing_001"


async def test_orchestrator_complete_enrollment_integrates_with_recovery_terminal_state(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Completed enrollment should not return to recoverable collection states."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    completion = await orchestrator.complete_enrollment(
        {
            "voice_profile_id": "tom_voice",
            "person_id": "person.tom",
            "min_samples": 2,
        }
    )
    assert completion["completed"] is True
    assert completion["cleanup_result_code"] in {"complete", "already_clean"}
    assert "speaker_embedding_id" not in completion

    recovery = await orchestrator.recover_enrollment({"person_id": "person.tom"})
    assert recovery["recoverable"] is False
    assert recovery["recovery_state"] == "terminal"


async def test_orchestrator_complete_enrollment_invalid_person_fails_before_session_mutation(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Invalid person_id should fail fast before completion mutates session into terminal state."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    with pytest.raises(Exception, match="person_id is not configured"):
        await orchestrator.complete_enrollment(
            {
                "voice_profile_id": "tom_voice",
                "person_id": "person.tom",
                "min_samples": 2,
            }
        )

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is not None
    assert session.state in {"sample_received", "capturing", "capture_pending", "ready", "processing"}


async def test_orchestrator_complete_enrollment_allows_session_bound_person_without_profile_record(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Completion should succeed when session person_id matches request even if person profiles are absent."""
    storage = ConciergeStorage(hass)
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    # Simulate drift/reset where person profiles were cleared after enrollment session was created.
    state = await storage.async_load_state()
    state.person_profiles = {}
    await storage.async_save_state(state)

    completion = await orchestrator.complete_enrollment(
        {
            "voice_profile_id": "tom_voice",
            "person_id": "person.tom",
            "min_samples": 3,
        }
    )

    assert completion["completed"] is True

async def test_orchestrator_completion_readiness_treats_storage_preflight_failure_as_warning(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Sample-complete sessions should remain buildable when storage preflight check is transiently unavailable."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    async def _raise_preflight():
        raise ValueError("storage probe failed")

    monkeypatch.setattr(orchestrator, "require_storage_preflight", _raise_preflight)

    readiness = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )

    assert readiness["ready"] is True
    assert readiness["reason_code"] == "ready_storage_preflight_warning"


async def test_orchestrator_completion_readiness_allows_blank_session_state_when_samples_sufficient(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Readiness should stay buildable when legacy/drifted session state is blank but samples are complete."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    orchestrator = EnrollmentOrchestrator(hass)
    await orchestrator.start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase one",
            "phrase_index": 0,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 11000,
            "prompt_category": "command",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase two",
            "phrase_index": 1,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "question",
            "capture_distance": "mid_field",
            "capture_noise": "moderate",
            "quality_pass": True,
        }
    )
    await orchestrator.record_sample(
        {
            "voice_profile_id": "tom_voice",
            "speech_text": "Phrase three",
            "phrase_index": 2,
            "source": "guided_enrollment_dialog",
            "recording_duration_ms": 10000,
            "prompt_category": "conversational",
            "capture_distance": "near_field",
            "capture_noise": "quiet",
            "quality_pass": True,
        }
    )

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is not None
    await storage.async_update_enrollment_session(session_id=session.session_id, state_name="")

    readiness = await orchestrator.get_completion_readiness(
        {
            "voice_profile_id": "tom_voice",
            "min_samples": 3,
        }
    )

    assert readiness["ready"] is True
    assert readiness["reason_code"] == "ready"


async def test_orchestrator_capture_provider_capabilities_are_sanitized(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Provider capability projection should be sanitized and browser-default."""
    orchestrator = EnrollmentOrchestrator(hass)

    capabilities = await orchestrator.get_capture_provider_capabilities()

    assert capabilities["default_provider"] == "browser"
    assert capabilities["selected_provider"] == "browser"
    assert capabilities["provider_type"] == "browser_microphone"
    assert capabilities["provider_available"] is True
    assert capabilities["provider_supported"] is True
    assert capabilities["capture_supported"] is True
    assert capabilities["selection_supported"] is True
    assert capabilities["reason_code"] == "ready"
    assert capabilities["satellite_capture_supported"] is False
    assert capabilities["satellite_status_code"] == "provider_not_selected"
    providers = {item["provider_key"]: item for item in capabilities["providers"]}
    assert providers["satellite"]["provider_supported"] is False
    assert providers["satellite"]["provider_status"] == "provider_not_selected"
    assert "recording_path" not in str(capabilities)
    assert "provider_device_id" not in str(capabilities)
    assert "person_ref" not in str(capabilities)


async def test_orchestrator_upload_browser_sample_routes_through_capture_provider(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Browser upload must be routed through BrowserMicCaptureProvider handoff."""
    called = {"count": 0}

    async def _fake_capture_sample(self, request):
        called["count"] += 1
        return CaptureSampleResult(
            saved=True,
            recording_path="/safe/session/sample_0.wav",
            recording_mime_type=request.audio_content_type,
            recording_size_bytes=len(request.audio_bytes),
            phrase_index=request.phrase_index,
        )

    monkeypatch.setattr(BrowserMicCaptureProvider, "capture_sample", _fake_capture_sample)

    payload = await EnrollmentOrchestrator(hass).upload_browser_sample(
        person_id="person.tom",
        voice_profile_id="tom_voice",
        phrase_index=0,
        audio_content_type="audio/wav",
        audio_bytes=b"sample",
    )

    assert called["count"] == 1
    assert payload["saved"] is True
    assert payload["recording_mime_type"] == "audio/wav"


async def test_orchestrator_satellite_provider_is_modeled_as_unsupported_future(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Satellite provider should be modeled as unconfigured/unsupported without fake capture."""
    orchestrator = EnrollmentOrchestrator(hass)

    capabilities = await orchestrator.get_capture_provider_capabilities("satellite")

    assert capabilities["selected_provider"] == "satellite"
    assert capabilities["provider_type"] == "satellite"
    assert capabilities["provider_supported"] is False
    assert capabilities["provider_available"] is False
    assert capabilities["provider_status"] == "not_configured"
    assert capabilities["capture_supported"] is False
    assert capabilities["selection_supported"] is True
    assert capabilities["reason_code"] == "satellite_provider_not_configured"
    assert capabilities["satellite_status_code"] == "satellite_provider_not_configured"

    with pytest.raises(Exception, match="capture_provider_unsupported"):
        await orchestrator.require_capture_provider("satellite", publish_repairs=False)


async def test_orchestrator_get_satellite_provider_status_is_sanitized(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Satellite status projection should be explicit and privacy-safe."""
    status = await EnrollmentOrchestrator(hass).get_satellite_provider_status(provider_selected=True)

    assert status["provider_type"] == "satellite"
    assert status["provider_supported"] is False
    assert status["provider_available"] is False
    assert status["selection_supported"] is True
    assert status["capture_supported"] is False
    assert status["satellite_capture_supported"] is False
    assert status["satellite_status_code"] == "satellite_provider_not_configured"
    assert "recording_path" not in str(status)
    assert "provider_device_id" not in str(status)


async def test_orchestrator_satellite_capture_poc_routes_through_storage_and_session(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Satellite capture POC must write via storage provider and register via EnrollmentSession authority."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    async def _fake_satellite_poc(self, **kwargs):
        del self, kwargs
        return (
            {
                "provider_type": "satellite",
                "satellite_entity_available": True,
                "capture_command_available": True,
                "capture_started": True,
                "chunks_received": 4,
                "bytes_received": 24,
                "audio_rate": 16000,
                "audio_width": 2,
                "audio_channels": 1,
                "failure_code": None,
                "failure_message_safe": None,
            },
            b"\x00\x01" * 12,
            "audio/L16; rate=16000; channels=1",
        )

    monkeypatch.setattr(SatelliteCaptureProvider, "run_satellite_capture_poc", _fake_satellite_poc)

    result = await EnrollmentOrchestrator(hass).run_satellite_capture_poc(
        {
            "voice_profile_id": "tom_voice",
            "timeout_seconds": 5.0,
            "satellite_entity_id": "assist_satellite.home_assistant_voice_0a87d9_assist_satellite",
        }
    )

    assert result["provider_type"] == "satellite"
    assert result["capture_command_available"] is True
    assert result["chunks_received"] == 4
    assert result["bytes_received"] == 24
    assert result["sample_written"] is True
    assert result["sample_registered"] is True
    assert result["failure_code"] is None
    assert "recording_path" not in str(result)
    assert "device_id" not in str(result)

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is not None
    assert session.sample_count == 1
    assert session.capture_provider == "satellite"


async def test_orchestrator_satellite_capture_poc_fails_honestly_without_chunks(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Satellite POC must not fake success when no chunks are returned by capture command."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    async def _fake_satellite_poc(self, **kwargs):
        del self, kwargs
        return (
            {
                "provider_type": "satellite",
                "satellite_entity_available": True,
                "capture_command_available": True,
                "capture_started": True,
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": 16000,
                "audio_width": 2,
                "audio_channels": 1,
                "failure_code": None,
                "failure_message_safe": None,
            },
            b"",
            "audio/L16; rate=16000; channels=1",
        )

    monkeypatch.setattr(SatelliteCaptureProvider, "run_satellite_capture_poc", _fake_satellite_poc)

    result = await EnrollmentOrchestrator(hass).run_satellite_capture_poc(
        {
            "voice_profile_id": "tom_voice",
            "timeout_seconds": 5.0,
        }
    )

    assert result["sample_written"] is False
    assert result["sample_registered"] is False
    assert result["failure_code"] == "capture_no_chunks"

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is None or session.sample_count == 0


async def test_orchestrator_satellite_capture_poc_propagates_capture_failure(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Satellite POC should surface websocket command failures without fallback/fake capture."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    async def _fake_satellite_poc(self, **kwargs):
        del self, kwargs
        return (
            {
                "provider_type": "satellite",
                "satellite_entity_available": True,
                "capture_command_available": True,
                "capture_started": False,
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": "capture_command_failed",
                "failure_message_safe": "assist_pipeline/device/capture invocation failed",
            },
            None,
            None,
        )

    monkeypatch.setattr(SatelliteCaptureProvider, "run_satellite_capture_poc", _fake_satellite_poc)

    result = await EnrollmentOrchestrator(hass).run_satellite_capture_poc(
        {
            "voice_profile_id": "tom_voice",
            "timeout_seconds": 5.0,
        }
    )

    assert result["failure_code"] == "capture_command_failed"
    assert result["sample_written"] is False
    assert result["sample_registered"] is False


async def test_orchestrator_start_enrollment_satellite_provider_sets_satellite_provider(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    """Shared start enrollment path should persist satellite provider selection."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    result = await EnrollmentOrchestrator(hass).start_enrollment(
        {
            "person_id": "person.tom",
            "voice_profile_id": "tom_voice",
            "voice_name": "Tom Voice",
            "local_only": True,
            "capture_provider": "satellite",
        }
    )

    assert result["started"] is True
    assert result["capture_provider"] == "satellite"

    session = await storage.async_get_latest_enrollment_session_for_voice_profile("tom_voice")
    assert session is not None
    assert session.capture_provider == "satellite"


async def test_orchestrator_capture_enrollment_sample_satellite_routes_through_record_sample(
    hass: HomeAssistant,
    setup_integration,
    monkeypatch,
) -> None:
    """Production satellite capture should write audio then register sample through record_sample authority."""
    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="tom_voice"),
        set_as_default=True,
    )
    await storage.async_update_voice_profile(
        VoiceProfile(
            voice_profile_id="tom_voice",
            name="Tom Voice",
            enrollment_state="capturing",
            enrollment_source="people_setup",
        )
    )

    recorded_payload: dict[str, object] = {}

    async def _fake_satellite_capture(self, **kwargs):
        del self
        return (
            {
                "provider_type": "satellite",
                "satellite_entity_available": True,
                "capture_command_available": True,
                "capture_started": True,
                "chunks_received": 4,
                "bytes_received": 24,
                "audio_rate": 16000,
                "audio_width": 2,
                "audio_channels": 1,
                "failure_code": None,
                "failure_message_safe": None,
            },
            b"\x00\x01" * 12,
            "audio/L16; rate=16000; channels=1",
        )

    async def _fake_record_sample(self, call_data):
        del self
        recorded_payload.update(call_data)
        return {
            "captured": True,
            "voice_profile_id": call_data["voice_profile_id"],
            "sample_id": "sample_satellite_1",
            "sample_count": 1,
        }

    monkeypatch.setattr(SatelliteCaptureProvider, "run_satellite_capture_poc", _fake_satellite_capture)
    monkeypatch.setattr(SatelliteCaptureProvider, "capture_satellite_audio", _fake_satellite_capture)
    monkeypatch.setattr(EnrollmentOrchestrator, "record_sample", _fake_record_sample)

    result = await EnrollmentOrchestrator(hass).capture_enrollment_sample(
        {
            "voice_profile_id": "tom_voice",
            "person_id": "person.tom",
            "capture_provider": "satellite",
            "prompt_text": "Please say phrase one now",
            "speech_text": "Phrase one",
            "timeout_seconds": 5.0,
        }
    )

    assert result["sample_written"] is True
    assert result["sample_registered"] is True
    assert result["sample_count"] == 1
    assert recorded_payload["voice_profile_id"] == "tom_voice"
    assert recorded_payload["capture_provider"] == "satellite"
