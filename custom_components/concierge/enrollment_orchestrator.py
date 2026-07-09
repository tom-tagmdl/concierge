"""Enrollment orchestration layer for Concierge voice enrollment workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import voluptuous as vol

from homeassistant.core import HomeAssistant

from .archive_runtime import archive_options_from_entry, resolve_voice_enrollment_root
from .const import DOMAIN
from .const import VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE
from .const import VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_FAILED
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_TIMEOUT
from .const import VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN
from .const import VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED
from .const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED
from .const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE
from .const import VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP
from .const import VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE
from .const import VOICE_ENROLLMENT_STATE_CLEANUP_FAILED
from .const import VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP
from .const import VOICE_ENROLLMENT_STATE_CAPTURE_PENDING
from .const import VOICE_ENROLLMENT_STATE_CAPTURING
from .const import VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP
from .const import VOICE_ENROLLMENT_STATE_IDLE
from .const import VOICE_ENROLLMENT_STATE_PROCESSING
from .const import VOICE_ENROLLMENT_STATE_READY
from .const import VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED
from .const import VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP
from .enrollment_capture import BrowserMicCaptureProvider
from .enrollment_capture import CAPTURE_PROVIDER_PREFERENCE_AUTO
from .enrollment_capture import CAPTURE_PROVIDER_PREFERENCE_BROWSER
from .enrollment_capture import CAPTURE_PROVIDER_PREFERENCE_SATELLITE
from .enrollment_capture import CAPTURE_PROVIDER_STATUS_PROVIDER_NOT_SELECTED
from .enrollment_capture import CAPTURE_PROVIDER_STATUS_UNSUPPORTED
from .enrollment_capture import CAPTURE_PROVIDER_TYPE_BROWSER_MICROPHONE
from .enrollment_capture import SATELLITE_CAPTURE_POC_EXPECTED_CHANNELS
from .enrollment_capture import SATELLITE_CAPTURE_POC_EXPECTED_RATE
from .enrollment_capture import SATELLITE_CAPTURE_POC_EXPECTED_WIDTH
from .enrollment_capture import SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED
from .enrollment_capture import CaptureProviderCapability
from .enrollment_capture import CaptureSampleRequest
from .enrollment_capture import EnrollmentCaptureProvider
from .enrollment_capture import SatelliteCaptureProvider
from .enrollment_cleanup import EnrollmentCleanupManager, EnrollmentCleanupRequest
from .enrollment_session import build_enrollment_session_manifest_payload
from .enrollment_session import build_enrollment_session_progress_projection
from .enrollment_session import enrollment_session_for_start
from .enrollment_session import enrollment_session_mark_cleanup_complete
from .enrollment_session import enrollment_session_mark_cleanup_failed
from .enrollment_session import enrollment_session_mark_cleanup_pending
from .enrollment_session import enrollment_session_mark_cleanup_running
from .enrollment_session import enrollment_session_mark_profile_built
from .enrollment_session import enrollment_session_record_sample
from .enrollment_session import enrollment_session_remove_sample
from .enrollment_session import enrollment_session_reset
from .enrollment_session import legacy_voice_profile_enrollment_state
from .enrollment_session import resolve_manifest_target_sample_count
from .enrollment_storage import MountedPathEnrollmentStorageProvider
from .models import EnrollmentSession
from .models import PersonProfile
from .models import VoiceProfile
from .repairs import async_clear_cleanup_issue
from .repairs import async_clear_capture_provider_issue
from .repairs import async_clear_storage_issue
from .repairs import async_create_or_update_cleanup_issue
from .repairs import async_create_or_update_capture_provider_issue
from .repairs import async_create_or_update_storage_issue
from .storage import ConciergeStorage

DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT = 8


def resolve_enrollment_storage_provider_from_entry(
    hass: HomeAssistant,
    entry,
) -> MountedPathEnrollmentStorageProvider | None:
    """Return mounted-path provider from one config entry when configured."""
    archive_options = archive_options_from_entry(entry)
    destination_uri = str(archive_options.get("destination_uri", "") or "").strip()
    destination_configured = bool(archive_options.get("destination_configured", False))
    if not destination_configured or not destination_uri:
        return None

    try:
        root_path = resolve_voice_enrollment_root(destination_uri)
    except ValueError:
        return None

    return MountedPathEnrollmentStorageProvider(
        root_path=root_path,
        hass_config_path=Path(hass.config.path()),
    )


def resolve_enrollment_storage_provider_from_hass(
    hass: HomeAssistant,
) -> MountedPathEnrollmentStorageProvider | None:
    """Return mounted-path provider from the active Concierge config entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        return None
    return resolve_enrollment_storage_provider_from_entry(hass, entries[0])


def _voice_profile_id_for_person(person_id: str) -> str:
    normalized = str(person_id or "").strip().lower().replace(".", "_").replace(" ", "_")
    normalized = "".join(ch for ch in normalized if ch.isalnum() or ch in {"_", "-"})
    return f"{normalized or 'person'}_voice"


def _session_state_from_legacy_enrollment_state(enrollment_state: str, sample_count: int) -> str:
    value = str(enrollment_state or "").strip().lower()
    if value == "trained":
        return "completed_pending_cleanup"
    if value == "untrained":
        return "idle"
    if sample_count > 0:
        return "sample_received"
    return "ready"


def _project_voice_profile_from_session(
    *,
    existing_voice: VoiceProfile | None,
    voice_profile_id: str,
    name: str,
    session: EnrollmentSession,
    enrollment_source: str,
    speaker_embedding_id: str,
    attribution_confidence: float | None,
    disabled: bool,
    consent: dict[str, Any],
    tts_voice: str,
) -> VoiceProfile:
    return VoiceProfile(
        voice_profile_id=voice_profile_id,
        name=name,
        tts_voice=tts_voice,
        enrollment_state=legacy_voice_profile_enrollment_state(session),
        enrollment_source=enrollment_source,
        speaker_embedding_id=speaker_embedding_id,
        sample_count=session.sample_count,
        sample_items=list(session.sample_items),
        attribution_confidence=attribution_confidence,
        enrollment_started_at=session.enrollment_started_at,
        last_sample_at=session.last_sample_at,
        last_built_at=session.last_built_at,
        disabled=disabled,
        consent=dict(consent),
    )


def _voice_confidence_for_sample_count(sample_count: int) -> float:
    bounded = max(0, int(sample_count))
    return min(0.95, 0.55 + (0.05 * bounded))


def _sample_recording_paths(sample_items: list[dict[str, Any]]) -> list[str]:
    paths: list[str] = []
    for sample in sample_items:
        raw_path = str(sample.get("recording_path", "") or "").strip()
        if raw_path:
            paths.append(raw_path)
    return paths


class EnrollmentOrchestrator:
    """Coordinate enrollment workflows using existing Phase 0 authorities."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    @staticmethod
    def _normalize_capture_provider_preference(preferred_provider: str | None) -> str:
        normalized = str(preferred_provider or CAPTURE_PROVIDER_PREFERENCE_AUTO).strip().lower()
        if normalized in {
            CAPTURE_PROVIDER_PREFERENCE_AUTO,
            CAPTURE_PROVIDER_PREFERENCE_BROWSER,
            CAPTURE_PROVIDER_PREFERENCE_SATELLITE,
        }:
            return normalized
        if normalized in {"browser_microphone", "browser_mic", "browser"}:
            return CAPTURE_PROVIDER_PREFERENCE_BROWSER
        if normalized in {"assist_satellite", "satellite"}:
            return CAPTURE_PROVIDER_PREFERENCE_SATELLITE
        return CAPTURE_PROVIDER_PREFERENCE_AUTO

    async def choose_default_capture_provider(self) -> str:
        """Return default provider key for current production enrollment path."""
        return CAPTURE_PROVIDER_PREFERENCE_BROWSER

    async def resolve_capture_provider(
        self,
        preferred_provider: str | None = None,
    ) -> EnrollmentCaptureProvider:
        """Resolve provider instance from preference while keeping provider details encapsulated."""
        normalized = self._normalize_capture_provider_preference(preferred_provider)
        if normalized == CAPTURE_PROVIDER_PREFERENCE_SATELLITE:
            return SatelliteCaptureProvider(
                self.hass,
                capture_api_supported=True,
                provider_selected=True,
            )

        if normalized == CAPTURE_PROVIDER_PREFERENCE_AUTO:
            normalized = await self.choose_default_capture_provider()
            if normalized == CAPTURE_PROVIDER_PREFERENCE_SATELLITE:
                return SatelliteCaptureProvider(
                    self.hass,
                    capture_api_supported=True,
                    provider_selected=True,
                )

        return BrowserMicCaptureProvider(self.hass, self.require_storage_preflight)

    async def get_satellite_provider_status(
        self,
        *,
        provider_selected: bool,
    ) -> dict[str, Any]:
        """Return explicit satellite provider status for diagnostics and future UI wiring."""
        capability = await SatelliteCaptureProvider(
            self.hass,
            capture_api_supported=True,
            provider_selected=provider_selected,
        ).get_capability()
        payload = capability.as_public_dict()
        payload["satellite_capture_supported"] = bool(capability.capture_supported)
        payload["satellite_status_code"] = capability.reason_code
        return payload

    async def get_capture_provider_capabilities(
        self,
        preferred_provider: str | None = None,
    ) -> dict[str, Any]:
        """Return sanitized capability projection for provider selection and diagnostics use."""
        requested = self._normalize_capture_provider_preference(preferred_provider)
        default_provider = await self.choose_default_capture_provider()

        browser_provider = BrowserMicCaptureProvider(self.hass, self.require_storage_preflight)
        satellite_provider = SatelliteCaptureProvider(
            self.hass,
            capture_api_supported=True,
            provider_selected=(requested == CAPTURE_PROVIDER_PREFERENCE_SATELLITE),
        )

        browser_capability = await browser_provider.get_capability()
        satellite_capability = await satellite_provider.get_capability()

        selected_provider = await self.resolve_capture_provider(requested)
        selected_capability = await selected_provider.get_capability()

        return {
            "requested_provider": requested,
            "default_provider": default_provider,
            "selected_provider": selected_capability.provider_key,
            "provider_type": selected_capability.provider_type,
            "provider_available": selected_capability.available,
            "provider_supported": selected_capability.supported,
            "provider_status": selected_capability.status,
            "provider_status_summary": selected_capability.user_safe_status_summary,
            "capture_supported": selected_capability.capture_supported,
            "selection_supported": selected_capability.selection_supported,
            "reason_code": selected_capability.reason_code,
            "satellite_capture_supported": satellite_capability.capture_supported,
            "satellite_status_code": satellite_capability.reason_code,
            "providers": [
                browser_capability.as_public_dict(),
                satellite_capability.as_public_dict(),
            ],
        }

    async def require_capture_provider(
        self,
        preferred_provider: str | None = None,
        *,
        publish_repairs: bool = True,
    ) -> tuple[EnrollmentCaptureProvider, CaptureProviderCapability]:
        """Require a supported and available provider before capture begins."""
        provider = await self.resolve_capture_provider(preferred_provider)
        capability = await provider.get_capability()
        requested = self._normalize_capture_provider_preference(preferred_provider)
        satellite_selected = requested == CAPTURE_PROVIDER_PREFERENCE_SATELLITE

        if capability.supported and capability.available:
            if publish_repairs:
                await async_clear_capture_provider_issue(self.hass)
            return provider, capability

        should_publish_capture_issue = publish_repairs and (
            capability.provider_type != "satellite"
            or satellite_selected
        )
        if should_publish_capture_issue:
            await async_create_or_update_capture_provider_issue(
                self.hass,
                provider_type=capability.provider_type,
                provider_status=capability.status,
                reason_code=capability.reason_code,
                selected_provider=satellite_selected,
            )

        if capability.status == CAPTURE_PROVIDER_STATUS_PROVIDER_NOT_SELECTED:
            raise vol.Invalid("capture_provider_not_selected")

        if capability.status == CAPTURE_PROVIDER_STATUS_UNSUPPORTED or not capability.supported:
            raise vol.Invalid("capture_provider_unsupported")

        raise vol.Invalid("capture_provider_unavailable")

    def resolve_provider(self) -> MountedPathEnrollmentStorageProvider | None:
        return resolve_enrollment_storage_provider_from_hass(self.hass)

    async def require_storage_preflight(
        self,
        publish_repairs: bool = True,
    ) -> MountedPathEnrollmentStorageProvider:
        provider = self.resolve_provider()
        if provider is None:
            if publish_repairs:
                await async_create_or_update_storage_issue(
                    self.hass,
                    failure_code=VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED,
                )
            raise vol.Invalid(
                f"external enrollment storage preflight failed: {VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED}"
            )

        readiness = await self.hass.async_add_executor_job(provider.validate_ready)
        if readiness.ready:
            if publish_repairs:
                await async_clear_storage_issue(self.hass)
            return provider

        failure_code = str(readiness.failure_code or VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE)
        failure_message = str(readiness.failure_message_safe or "external enrollment storage preflight failed")
        if publish_repairs:
            await async_create_or_update_storage_issue(
                self.hass,
                failure_code=failure_code,
                provider_type=str(readiness.provider_type or "mounted_path"),
            )
        raise vol.Invalid(f"{failure_message}: {failure_code}")

    async def upload_browser_sample(
        self,
        *,
        person_id: str,
        voice_profile_id: str,
        phrase_index: int,
        audio_content_type: str,
        audio_bytes: bytes,
    ) -> dict[str, Any]:
        """Coordinate browser upload sequencing through preflight and provider write."""
        provider, _ = await self.require_capture_provider(
            CAPTURE_PROVIDER_PREFERENCE_BROWSER,
            publish_repairs=True,
        )
        capture_result = await provider.capture_sample(
            CaptureSampleRequest(
                person_id=person_id,
                voice_profile_id=voice_profile_id,
                phrase_index=int(phrase_index),
                audio_content_type=audio_content_type,
                audio_bytes=audio_bytes,
            )
        )
        return capture_result.as_payload()

    async def capture_browser_sample(
        self,
        *,
        person_id: str,
        voice_profile_id: str,
        phrase_index: int,
        speech_text: str,
        audio_content_type: str,
        audio_bytes: bytes,
        source: str = "guided_enrollment_dialog",
        recording_duration_ms: int | None = None,
    ) -> dict[str, Any]:
        """Coordinate browser upload and EnrollmentSession sample registration."""
        upload_payload = await self.upload_browser_sample(
            person_id=person_id,
            voice_profile_id=voice_profile_id,
            phrase_index=phrase_index,
            audio_content_type=audio_content_type,
            audio_bytes=audio_bytes,
        )

        registration_payload: dict[str, Any] = {
            "voice_profile_id": voice_profile_id,
            "speech_text": speech_text,
            "source": source,
            "phrase_index": int(phrase_index),
            "recording_path": upload_payload["recording_path"],
            "recording_mime_type": upload_payload["recording_mime_type"],
            "recording_size_bytes": int(upload_payload["recording_size_bytes"]),
        }
        if recording_duration_ms is not None:
            registration_payload["recording_duration_ms"] = max(0, int(recording_duration_ms))

        capture_payload = await self.record_sample(registration_payload)
        return {
            **upload_payload,
            **capture_payload,
        }

    async def run_satellite_capture_poc(
        self,
        call_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Run a bounded satellite capture POC through supported Assist pipeline command handling."""
        result: dict[str, Any] = {
            "provider_type": CAPTURE_PROVIDER_PREFERENCE_SATELLITE,
            "satellite_entity_available": False,
            "capture_command_available": False,
            "capture_started": False,
            "chunks_received": 0,
            "bytes_received": 0,
            "sample_written": False,
            "sample_registered": False,
            "audio_rate": None,
            "audio_width": None,
            "audio_channels": None,
            "failure_code": None,
            "failure_message_safe": None,
        }

        voice_profile_id = str(call_data.get("voice_profile_id", "") or "").strip()
        if not voice_profile_id:
            result["failure_code"] = "voice_profile_required"
            result["failure_message_safe"] = "voice_profile_id is required for satellite capture POC"
            return result

        timeout_seconds = float(call_data.get("timeout_seconds", 8.0) or 8.0)
        satellite_entity_id = str(call_data.get("satellite_entity_id", "") or "").strip() or None
        device_id = str(call_data.get("device_id", "") or "").strip() or None

        storage_provider = await self.require_storage_preflight()

        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            result["failure_code"] = "voice_profile_not_configured"
            result["failure_message_safe"] = "voice profile is not configured"
            return result
        if existing_voice.disabled:
            result["failure_code"] = "voice_profile_disabled"
            result["failure_message_safe"] = "voice profile is disabled"
            return result

        now_iso = datetime.now(timezone.utc).isoformat()
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = str(call_data.get("person_id", "") or "").strip()
            if not matched_person_id:
                for profile in state.person_profiles.values():
                    if profile.voice_profile_id == voice_profile_id:
                        matched_person_id = profile.person_id
                        break

            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        satellite_provider = SatelliteCaptureProvider(
            self.hass,
            capture_api_supported=True,
            provider_selected=True,
        )
        capture_result, captured_audio, content_type = await satellite_provider.run_satellite_capture_poc(
            timeout_seconds=timeout_seconds,
            satellite_entity_id=satellite_entity_id,
            device_id=device_id,
        )
        result.update(capture_result)

        failure_code = str(result.get("failure_code") or "").strip()
        if failure_code:
            return result

        expected_metadata = (
            int(result.get("audio_rate") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_RATE
            and int(result.get("audio_width") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_WIDTH
            and int(result.get("audio_channels") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_CHANNELS
        )
        if not expected_metadata:
            result["failure_code"] = "capture_metadata_mismatch"
            result["failure_message_safe"] = "satellite capture metadata does not match expected enrollment format"
            return result

        if not captured_audio:
            result["failure_code"] = "capture_no_chunks"
            result["failure_message_safe"] = "no satellite audio chunks were received during the POC window"
            return result

        session_id = enrollment_session.session_id
        sample_index = int(enrollment_session.sample_count)
        sample_content_type = str(content_type or "application/octet-stream")
        try:
            write_result = await self.hass.async_add_executor_job(
                lambda: storage_provider.write_sample(
                    session_id=session_id,
                    sample_index=sample_index,
                    content_type=sample_content_type,
                    data_bytes=captured_audio,
                )
            )
        except Exception:
            result["failure_code"] = "storage_write_failed"
            result["failure_message_safe"] = "satellite POC sample could not be written to enrollment storage"
            return result

        result["sample_written"] = True

        sample_id = f"sample_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}"
        sample_payload: dict[str, Any] = {
            "sample_id": sample_id,
            "speech_text": "satellite_capture_poc",
            "captured_at": now_iso,
            "source": "assist_pipeline_device_capture_poc",
            "phrase_index": sample_index,
            "recording_path": write_result.sample_path,
            "recording_mime_type": sample_content_type,
            "recording_size_bytes": int(len(captured_audio)),
        }

        try:
            enrollment_session = enrollment_session_record_sample(
                enrollment_session,
                sample_payload=sample_payload,
                captured_at=now_iso,
            )
            enrollment_session.capture_provider = CAPTURE_PROVIDER_PREFERENCE_SATELLITE
            enrollment_session = await storage.async_update_enrollment_session(
                session_id=enrollment_session.session_id,
                state_name=enrollment_session.state,
                sample_count=enrollment_session.sample_count,
                sample_items=list(enrollment_session.sample_items),
                enrollment_started_at=enrollment_session.enrollment_started_at,
                last_sample_at=enrollment_session.last_sample_at,
                last_built_at=enrollment_session.last_built_at,
                metadata={
                    **dict(enrollment_session.metadata),
                    "provider_type": CAPTURE_PROVIDER_PREFERENCE_SATELLITE,
                    "capture_provider_status": "poc_capture_complete",
                },
            )
            await self.sync_manifest(enrollment_session)
            updated_voice = _project_voice_profile_from_session(
                existing_voice=existing_voice,
                voice_profile_id=existing_voice.voice_profile_id,
                name=existing_voice.name,
                session=enrollment_session,
                enrollment_source=existing_voice.enrollment_source,
                speaker_embedding_id=existing_voice.speaker_embedding_id,
                attribution_confidence=existing_voice.attribution_confidence,
                disabled=existing_voice.disabled,
                consent=dict(existing_voice.consent),
                tts_voice=existing_voice.tts_voice,
            )
            await storage.async_update_voice_profile(updated_voice)
        except Exception:
            result["failure_code"] = "session_registration_failed"
            result["failure_message_safe"] = "satellite POC sample could not be registered with enrollment session"
            return result

        result["sample_registered"] = True
        return result

    async def capture_enrollment_sample(self, call_data: dict[str, Any]) -> dict[str, Any]:
        """Capture one enrollment sample through provider transport, then reuse common registration flow."""
        preferred_provider = self._normalize_capture_provider_preference(call_data.get("capture_provider"))
        if preferred_provider != CAPTURE_PROVIDER_PREFERENCE_SATELLITE:
            return await self.record_sample(call_data)

        result: dict[str, Any] = {
            "provider_type": CAPTURE_PROVIDER_PREFERENCE_SATELLITE,
            "satellite_entity_available": False,
            "capture_command_available": False,
            "capture_started": False,
            "chunks_received": 0,
            "bytes_received": 0,
            "sample_written": False,
            "sample_registered": False,
            "audio_rate": None,
            "audio_width": None,
            "audio_channels": None,
            "failure_code": None,
            "failure_message_safe": None,
        }

        voice_profile_id = str(call_data.get("voice_profile_id", "") or "").strip()
        if not voice_profile_id:
            result["failure_code"] = "voice_profile_required"
            result["failure_message_safe"] = "voice_profile_id is required for satellite enrollment capture"
            return result

        timeout_seconds = float(call_data.get("timeout_seconds", 8.0) or 8.0)
        satellite_entity_id = str(call_data.get("satellite_entity_id", "") or "").strip() or None
        device_id = str(call_data.get("device_id", "") or "").strip() or None
        preannounce = bool(call_data.get("preannounce", False))
        prompt_text = str(call_data.get("prompt_text", "") or "").strip() or "Please say your enrollment phrase now."
        speech_text = str(call_data.get("speech_text", "") or "").strip() or prompt_text

        storage_provider = await self.require_storage_preflight()
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            result["failure_code"] = "voice_profile_not_configured"
            result["failure_message_safe"] = "voice profile is not configured"
            return result
        if existing_voice.disabled:
            result["failure_code"] = "voice_profile_disabled"
            result["failure_message_safe"] = "voice profile is disabled"
            return result

        now_iso = datetime.now(timezone.utc).isoformat()
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = str(call_data.get("person_id", "") or "").strip()
            if not matched_person_id:
                for profile in state.person_profiles.values():
                    if profile.voice_profile_id == voice_profile_id:
                        matched_person_id = profile.person_id
                        break

            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        phrase_index_raw = call_data.get("phrase_index")
        try:
            phrase_index = int(phrase_index_raw) if phrase_index_raw is not None else int(enrollment_session.sample_count)
        except (TypeError, ValueError):
            phrase_index = int(enrollment_session.sample_count)

        satellite_provider = SatelliteCaptureProvider(
            self.hass,
            capture_api_supported=True,
            provider_selected=True,
        )
        capture_result, captured_audio, content_type = await satellite_provider.capture_satellite_audio(
            timeout_seconds=timeout_seconds,
            satellite_entity_id=satellite_entity_id,
            device_id=device_id,
            prompt_text=prompt_text,
            preannounce=preannounce,
        )
        result.update(capture_result)

        failure_code = str(result.get("failure_code") or "").strip()
        if failure_code:
            return result

        expected_metadata = (
            int(result.get("audio_rate") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_RATE
            and int(result.get("audio_width") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_WIDTH
            and int(result.get("audio_channels") or 0) == SATELLITE_CAPTURE_POC_EXPECTED_CHANNELS
        )
        if not expected_metadata:
            result["failure_code"] = "capture_metadata_mismatch"
            result["failure_message_safe"] = "satellite capture metadata does not match expected enrollment format"
            return result

        if not captured_audio:
            result["failure_code"] = "capture_no_chunks"
            result["failure_message_safe"] = "no satellite audio chunks were received during the capture window"
            return result

        sample_content_type = str(content_type or "application/octet-stream")
        try:
            write_result = await self.hass.async_add_executor_job(
                lambda: storage_provider.write_sample(
                    session_id=enrollment_session.session_id,
                    sample_index=phrase_index,
                    content_type=sample_content_type,
                    data_bytes=captured_audio,
                )
            )
        except Exception:
            result["failure_code"] = "storage_write_failed"
            result["failure_message_safe"] = "satellite sample could not be written to enrollment storage"
            return result

        result["sample_written"] = True

        try:
            registration_payload = {
                "voice_profile_id": voice_profile_id,
                "speech_text": speech_text,
                "source": "satellite_guided_phrase",
                "phrase_index": phrase_index,
                "recording_path": write_result.sample_path,
                "recording_mime_type": sample_content_type,
                "recording_size_bytes": int(len(captured_audio)),
                "capture_provider": CAPTURE_PROVIDER_PREFERENCE_SATELLITE,
                "skip_capture_provider_preflight": True,
                "skip_storage_preflight": True,
            }
            registered = await self.record_sample(registration_payload)
            result["sample_registered"] = bool(registered.get("captured", False))
            result["sample_id"] = registered.get("sample_id")
            result["sample_count"] = int(registered.get("sample_count", 0) or 0)
            result["recording_path"] = write_result.sample_path
            result["recording_mime_type"] = sample_content_type
            result["recording_size_bytes"] = int(len(captured_audio))
            return result
        except Exception as err:
            result["failure_code"] = "session_registration_failed"
            result["failure_message_safe"] = (
                f"satellite sample could not be registered with enrollment session: {str(err)[:160]}"
            )
            return result

    async def sync_manifest(
        self,
        session: EnrollmentSession,
        *,
        target_sample_count: int | None = None,
    ) -> None:
        provider = self.resolve_provider()
        if provider is None:
            return

        readiness = await self.hass.async_add_executor_job(provider.validate_ready)
        if not readiness.ready:
            return

        existing_manifest = await self.hass.async_add_executor_job(
            lambda: provider.read_session_manifest(session.session_id)
        )
        effective_target = resolve_manifest_target_sample_count(
            session,
            requested_target_sample_count=target_sample_count,
            existing_target_sample_count=(
                int(existing_manifest.target_sample_count)
                if existing_manifest is not None
                else None
            ),
            default_target_sample_count=DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT,
        )
        manifest_payload = build_enrollment_session_manifest_payload(
            session,
            target_sample_count=effective_target,
        )
        await self.hass.async_add_executor_job(lambda: provider.upsert_session_manifest(manifest_payload))

    async def get_session_progress(
        self,
        *,
        session: EnrollmentSession,
    ) -> dict[str, Any]:
        """Return privacy-safe progress projection for one session."""
        existing_target: int | None = None
        provider = self.resolve_provider()
        if provider is not None:
            readiness = await self.hass.async_add_executor_job(provider.validate_ready)
            if readiness.ready:
                manifest = await self.hass.async_add_executor_job(
                    lambda: provider.read_session_manifest(session.session_id)
                )
                if manifest is not None:
                    existing_target = int(manifest.target_sample_count)

        target_sample_count = resolve_manifest_target_sample_count(
            session,
            requested_target_sample_count=None,
            existing_target_sample_count=existing_target,
            default_target_sample_count=DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT,
        )
        return build_enrollment_session_progress_projection(
            session,
            target_sample_count=target_sample_count,
        )

    async def get_browser_enrollment_progress(
        self,
        *,
        person_id: str,
        voice_profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Return orchestrator-backed progress payload for browser enrollment clients."""
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()

        resolved_person_id = str(person_id or "").strip()
        resolved_voice_profile_id = str(voice_profile_id or "").strip()
        if not resolved_voice_profile_id and resolved_person_id:
            person_profile = state.person_profiles.get(resolved_person_id)
            if person_profile is not None:
                resolved_voice_profile_id = str(person_profile.voice_profile_id or "").strip()

        if not resolved_voice_profile_id:
            return {
                "found": False,
                "person_id": resolved_person_id,
                "voice_profile_id": "",
                "progress": None,
            }

        session = await storage.async_get_latest_enrollment_session_for_voice_profile(resolved_voice_profile_id)
        if session is None:
            return {
                "found": False,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "progress": None,
            }

        return {
            "found": True,
            "person_id": resolved_person_id,
            "voice_profile_id": resolved_voice_profile_id,
            "progress": await self.get_session_progress(session=session),
        }

    async def _resolve_enrollment_session(
        self,
        *,
        person_id: str | None = None,
        voice_profile_id: str | None = None,
    ) -> tuple[EnrollmentSession | None, str, str]:
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()

        resolved_person_id = str(person_id or "").strip()
        resolved_voice_profile_id = str(voice_profile_id or "").strip()

        if not resolved_voice_profile_id and resolved_person_id:
            person_profile = state.person_profiles.get(resolved_person_id)
            if person_profile is not None:
                resolved_voice_profile_id = str(person_profile.voice_profile_id or "").strip()

        if not resolved_voice_profile_id:
            return None, resolved_person_id, resolved_voice_profile_id

        session = await storage.async_get_latest_enrollment_session_for_voice_profile(resolved_voice_profile_id)
        return session, resolved_person_id, resolved_voice_profile_id

    async def cancel_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        session, resolved_person_id, resolved_voice_profile_id = await self._resolve_enrollment_session(
            person_id=call_data.get("person_id"),
            voice_profile_id=call_data.get("voice_profile_id"),
        )
        if session is None:
            return {
                "canceled": False,
                "already_terminal": False,
                "not_found": True,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "cleanup_result_code": "not_applicable",
            }

        terminal_states = {
            VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE,
            VOICE_ENROLLMENT_STATE_CLEANUP_FAILED,
            VOICE_ENROLLMENT_STATE_IDLE,
        }
        if session.state in terminal_states and session.cleanup_status in {
            VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE,
            VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED,
        }:
            return {
                "canceled": False,
                "already_terminal": True,
                "not_found": False,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "cleanup_result_code": str(session.metadata.get("cleanup_result_code", "not_started") or "not_started"),
            }

        storage = ConciergeStorage(self.hass)
        session = await storage.async_update_enrollment_session(
            session_id=session.session_id,
            state_name=VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
            sample_count=session.sample_count,
            sample_items=list(session.sample_items),
            enrollment_started_at=session.enrollment_started_at,
            last_sample_at=session.last_sample_at,
            last_built_at=session.last_built_at,
        )
        await self.sync_manifest(session)

        session, cleanup_summary = await self.execute_cleanup(
            storage,
            session,
            cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
        )
        return {
            "canceled": True,
            "already_terminal": False,
            "not_found": False,
            "person_id": resolved_person_id,
            "voice_profile_id": resolved_voice_profile_id,
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
            "session_id": session.session_id,
        }

    async def abandon_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "person_id": call_data.get("person_id"),
            "voice_profile_id": call_data.get("voice_profile_id"),
        }
        result = await self.cancel_enrollment(payload)
        return {
            "abandoned": bool(result.get("canceled", False)),
            "already_terminal": bool(result.get("already_terminal", False)),
            "not_found": bool(result.get("not_found", False)),
            "person_id": result.get("person_id"),
            "voice_profile_id": result.get("voice_profile_id"),
            "cleanup_result_code": result.get("cleanup_result_code"),
            "session_id": result.get("session_id"),
        }

    async def recover_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        session, resolved_person_id, resolved_voice_profile_id = await self._resolve_enrollment_session(
            person_id=call_data.get("person_id"),
            voice_profile_id=call_data.get("voice_profile_id"),
        )
        if session is None:
            return {
                "recoverable": False,
                "recovered": False,
                "not_found": True,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "recovery_state": "not_found",
                "progress": None,
            }

        terminal_states = {
            VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE,
            VOICE_ENROLLMENT_STATE_CLEANUP_FAILED,
        }
        if session.state in terminal_states or session.cleanup_status in {
            VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE,
            VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED,
        }:
            return {
                "recoverable": False,
                "recovered": False,
                "not_found": False,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "recovery_state": "terminal",
                "progress": await self.get_session_progress(session=session),
            }

        if session.state in {
            VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
            VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
        }:
            return {
                "recoverable": False,
                "recovered": False,
                "not_found": False,
                "person_id": resolved_person_id,
                "voice_profile_id": resolved_voice_profile_id,
                "recovery_state": "cleanup_pending",
                "progress": await self.get_session_progress(session=session),
            }

        return {
            "recoverable": True,
            "recovered": True,
            "not_found": False,
            "person_id": resolved_person_id,
            "voice_profile_id": resolved_voice_profile_id,
            "recovery_state": "resume_available",
            "progress": await self.get_session_progress(session=session),
        }

    async def resume_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        recovery = await self.recover_enrollment(call_data)
        if not bool(recovery.get("recoverable", False)):
            return {
                "resumed": False,
                "recoverable": bool(recovery.get("recoverable", False)),
                "recovery_state": recovery.get("recovery_state"),
                "person_id": recovery.get("person_id"),
                "voice_profile_id": recovery.get("voice_profile_id"),
                "progress": recovery.get("progress"),
            }

        return {
            "resumed": True,
            "recoverable": True,
            "recovery_state": recovery.get("recovery_state"),
            "person_id": recovery.get("person_id"),
            "voice_profile_id": recovery.get("voice_profile_id"),
            "progress": recovery.get("progress"),
        }

    async def get_completion_readiness(self, call_data: dict[str, Any]) -> dict[str, Any]:
        """Return deterministic completion readiness derived from authoritative session state."""
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = str(call_data.get("voice_profile_id", "") or "").strip()
        min_samples = max(1, int(call_data.get("min_samples", DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT)))

        if not voice_profile_id:
            return {
                "ready": False,
                "reason_code": "voice_profile_required",
                "voice_profile_id": "",
                "sample_count": 0,
                "min_samples": min_samples,
                "enrollment_state": "unknown",
                "user_safe_status_summary": "Voice profile is required before completion.",
            }

        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            return {
                "ready": False,
                "reason_code": "voice_profile_missing",
                "voice_profile_id": voice_profile_id,
                "sample_count": 0,
                "min_samples": min_samples,
                "enrollment_state": "unknown",
                "user_safe_status_summary": "Voice profile is not configured.",
            }
        if existing_voice.disabled:
            return {
                "ready": False,
                "reason_code": "voice_profile_disabled",
                "voice_profile_id": voice_profile_id,
                "sample_count": int(existing_voice.sample_count),
                "min_samples": min_samples,
                "enrollment_state": str(existing_voice.enrollment_state or "unknown"),
                "user_safe_status_summary": "Voice profile is disabled.",
            }

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            return {
                "ready": False,
                "reason_code": "session_missing",
                "voice_profile_id": voice_profile_id,
                "sample_count": int(existing_voice.sample_count),
                "min_samples": min_samples,
                "enrollment_state": str(existing_voice.enrollment_state or "unknown"),
                "user_safe_status_summary": "Enrollment session is unavailable.",
            }

        sample_count = len(enrollment_session.sample_items)
        enrollment_state = str(enrollment_session.state or "").strip()
        if sample_count < min_samples:
            return {
                "ready": False,
                "reason_code": "insufficient_samples",
                "voice_profile_id": voice_profile_id,
                "sample_count": sample_count,
                "min_samples": min_samples,
                "enrollment_state": enrollment_state or "unknown",
                "user_safe_status_summary": "More samples are required before completion.",
            }

        if enrollment_state and enrollment_state not in {
            VOICE_ENROLLMENT_STATE_READY,
            VOICE_ENROLLMENT_STATE_CAPTURE_PENDING,
            VOICE_ENROLLMENT_STATE_CAPTURING,
            VOICE_ENROLLMENT_STATE_SAMPLE_RECEIVED,
            VOICE_ENROLLMENT_STATE_PROCESSING,
        }:
            return {
                "ready": False,
                "reason_code": "invalid_state",
                "voice_profile_id": voice_profile_id,
                "sample_count": sample_count,
                "min_samples": min_samples,
                "enrollment_state": enrollment_state,
                "user_safe_status_summary": "Enrollment session is not in a buildable state.",
            }

        try:
            await self.require_storage_preflight()
        except vol.Invalid:
            return {
                "ready": True,
                "reason_code": "ready_storage_preflight_warning",
                "voice_profile_id": voice_profile_id,
                "sample_count": sample_count,
                "min_samples": min_samples,
                "enrollment_state": enrollment_state or "unknown",
                "user_safe_status_summary": "Enrollment is ready for profile completion; storage cleanup readiness will be rechecked during build.",
            }

        return {
            "ready": True,
            "reason_code": "ready",
            "voice_profile_id": voice_profile_id,
            "sample_count": sample_count,
            "min_samples": min_samples,
            "enrollment_state": enrollment_state or "unknown",
            "user_safe_status_summary": "Enrollment is ready for profile completion.",
        }

    async def complete_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        """Coordinate explicit enrollment completion using existing lifecycle/storage authorities."""
        readiness = await self.get_completion_readiness(call_data)
        if not bool(readiness.get("ready", False)):
            reason = str(readiness.get("reason_code", "not_ready") or "not_ready")
            raise vol.Invalid(f"completion_not_ready: {reason}")

        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = str(call_data["voice_profile_id"])
        min_samples = max(1, int(call_data.get("min_samples", DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT)))
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            raise vol.Invalid("enrollment_session is not configured")

        person_id = str(call_data.get("person_id") or "").strip()
        person_profile = state.person_profiles.get(person_id) if person_id else None
        if person_id and person_profile is None:
            session_person_id = str(enrollment_session.person_id or "").strip()
            # Allow completion to proceed when the session is already bound to the
            # requested person_id, even if person profile records were cleared.
            if session_person_id != person_id:
                raise vol.Invalid("person_id is not configured")
            person_id = session_person_id

        sample_count = len(enrollment_session.sample_items)
        retained_sample_items = [
            {
                key: value
                for key, value in sample.items()
                if key not in {"recording_path", "recording_mime_type", "recording_size_bytes", "recording_duration_ms"}
            }
            for sample in list(enrollment_session.sample_items)
        ]

        now_iso = datetime.now(timezone.utc).isoformat()
        embedding_id = f"spk_{uuid4().hex}"
        confidence = _voice_confidence_for_sample_count(sample_count)

        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            sample_count=sample_count,
            sample_items=retained_sample_items,
        )
        enrollment_session = enrollment_session_mark_profile_built(enrollment_session, built_at=now_iso)
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await self.sync_manifest(enrollment_session, target_sample_count=min_samples)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=embedding_id,
            attribution_confidence=confidence,
            disabled=False,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        enrollment_session, cleanup_summary = await self.execute_cleanup(
            storage,
            enrollment_session,
            cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED,
        )

        if person_id and person_profile is not None:
            person_profile.voice_profile_id = voice_profile_id
            await storage.async_update_person_profile(
                person_profile,
                set_as_default=(
                    state.default_person_profile is not None
                    and state.default_person_profile.person_id == person_id
                ),
            )

        return {
            "completed": True,
            "voice_profile_id": voice_profile_id,
            "sample_count": sample_count,
            "person_id": person_id or None,
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
            "completion_state": str(enrollment_session.state),
            "ready_for_recovery": False,
        }

    async def execute_cleanup(
        self,
        storage: ConciergeStorage,
        session: EnrollmentSession,
        *,
        cleanup_reason: str,
    ) -> tuple[EnrollmentSession, dict[str, Any]]:
        reason_value = str(cleanup_reason or VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN).strip().lower()
        if reason_value not in {
            VOICE_ENROLLMENT_CLEANUP_REASON_COMPLETED,
            VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
            VOICE_ENROLLMENT_CLEANUP_REASON_FAILED,
            VOICE_ENROLLMENT_CLEANUP_REASON_TIMEOUT,
            VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL,
            VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN,
        }:
            reason_value = VOICE_ENROLLMENT_CLEANUP_REASON_UNKNOWN

        pending = enrollment_session_mark_cleanup_pending(session, cleanup_reason=reason_value)
        pending = await storage.async_update_enrollment_session(
            session_id=pending.session_id,
            state_name=pending.state,
            sample_count=pending.sample_count,
            sample_items=list(pending.sample_items),
            enrollment_started_at=pending.enrollment_started_at,
            last_sample_at=pending.last_sample_at,
            last_built_at=pending.last_built_at,
            cleanup_status=pending.cleanup_status,
            metadata=dict(pending.metadata),
        )
        await self.sync_manifest(pending)

        running_started_at = datetime.now(timezone.utc).isoformat()
        running = enrollment_session_mark_cleanup_running(
            pending,
            cleanup_reason=reason_value,
            cleanup_started_at=running_started_at,
        )
        running = await storage.async_update_enrollment_session(
            session_id=running.session_id,
            state_name=running.state,
            sample_count=running.sample_count,
            sample_items=list(running.sample_items),
            enrollment_started_at=running.enrollment_started_at,
            last_sample_at=running.last_sample_at,
            last_built_at=running.last_built_at,
            cleanup_status=running.cleanup_status,
            metadata=dict(running.metadata),
        )
        await self.sync_manifest(running)

        provider = self.resolve_provider()
        if provider is None:
            completed_at = datetime.now(timezone.utc).isoformat()
            await async_create_or_update_cleanup_issue(
                self.hass,
                cleanup_result_code=VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
                cleanup_reason=reason_value,
            )
            failed = enrollment_session_mark_cleanup_failed(
                running,
                cleanup_reason=reason_value,
                cleanup_result_code=VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
                cleanup_started_at=running_started_at,
                cleanup_completed_at=completed_at,
                artifacts_seen_count=0,
                artifacts_deleted_count=0,
                artifacts_missing_count=0,
                error_count=1,
            )
            failed = await storage.async_update_enrollment_session(
                session_id=failed.session_id,
                state_name=failed.state,
                sample_count=failed.sample_count,
                sample_items=list(failed.sample_items),
                enrollment_started_at=failed.enrollment_started_at,
                last_sample_at=failed.last_sample_at,
                last_built_at=failed.last_built_at,
                cleanup_status=failed.cleanup_status,
                metadata=dict(failed.metadata),
            )
            await self.sync_manifest(failed)
            return failed, {
                "cleanup_reason": reason_value,
                "cleanup_result_code": VOICE_ENROLLMENT_CLEANUP_RESULT_FAILED,
                "artifacts_seen_count": 0,
                "artifacts_deleted_count": 0,
                "artifacts_missing_count": 0,
                "errors_redacted_or_sanitized": ["provider_unavailable"],
                "cleanup_started_at": running_started_at,
                "cleanup_completed_at": completed_at,
            }

        manager = EnrollmentCleanupManager(provider)
        cleanup_result = await self.hass.async_add_executor_job(
            lambda: manager.cleanup(
                EnrollmentCleanupRequest(
                    session=running,
                    cleanup_reason=reason_value,
                )
            )
        )

        if cleanup_result.cleanup_result_code in {"failed", "partial"}:
            await async_create_or_update_cleanup_issue(
                self.hass,
                cleanup_result_code=cleanup_result.cleanup_result_code,
                cleanup_reason=cleanup_result.cleanup_reason,
            )
            finalized = enrollment_session_mark_cleanup_failed(
                running,
                cleanup_reason=cleanup_result.cleanup_reason,
                cleanup_result_code=cleanup_result.cleanup_result_code,
                cleanup_started_at=cleanup_result.cleanup_started_at,
                cleanup_completed_at=cleanup_result.cleanup_completed_at,
                artifacts_seen_count=cleanup_result.artifacts_seen_count,
                artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
                artifacts_missing_count=cleanup_result.artifacts_missing_count,
                error_count=len(cleanup_result.errors_redacted_or_sanitized),
            )
        else:
            await async_clear_cleanup_issue(self.hass)
            finalized = enrollment_session_mark_cleanup_complete(
                running,
                cleanup_reason=cleanup_result.cleanup_reason,
                cleanup_result_code=cleanup_result.cleanup_result_code,
                cleanup_started_at=cleanup_result.cleanup_started_at,
                cleanup_completed_at=cleanup_result.cleanup_completed_at,
                artifacts_seen_count=cleanup_result.artifacts_seen_count,
                artifacts_deleted_count=cleanup_result.artifacts_deleted_count,
                artifacts_missing_count=cleanup_result.artifacts_missing_count,
            )

        finalized = await storage.async_update_enrollment_session(
            session_id=finalized.session_id,
            state_name=finalized.state,
            sample_count=finalized.sample_count,
            sample_items=list(finalized.sample_items),
            enrollment_started_at=finalized.enrollment_started_at,
            last_sample_at=finalized.last_sample_at,
            last_built_at=finalized.last_built_at,
            cleanup_status=finalized.cleanup_status,
            metadata=dict(finalized.metadata),
        )
        await self.sync_manifest(finalized)

        return finalized, {
            "cleanup_reason": cleanup_result.cleanup_reason,
            "cleanup_result_code": cleanup_result.cleanup_result_code,
            "artifacts_seen_count": cleanup_result.artifacts_seen_count,
            "artifacts_deleted_count": cleanup_result.artifacts_deleted_count,
            "artifacts_missing_count": cleanup_result.artifacts_missing_count,
            "errors_redacted_or_sanitized": list(cleanup_result.errors_redacted_or_sanitized),
            "cleanup_started_at": cleanup_result.cleanup_started_at,
            "cleanup_completed_at": cleanup_result.cleanup_completed_at,
        }

    async def update_voice_profile(self, call_data: dict[str, Any]) -> dict[str, Any]:
        await self.require_storage_preflight()

        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = call_data["voice_profile_id"]
        existing_voice = state.voice_profiles.get(voice_profile_id)

        requested_sample_items = list(call_data.get("sample_items", []))
        requested_sample_count = int(call_data.get("sample_count", len(requested_sample_items)))
        if requested_sample_count != len(requested_sample_items) and requested_sample_items:
            requested_sample_count = len(requested_sample_items)

        session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if session is None:
            now_iso = datetime.now(timezone.utc).isoformat()
            session = await storage.async_create_enrollment_session(
                session_id=f"session_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}",
                person_id="",
                voice_profile_id=voice_profile_id,
                state_name=_session_state_from_legacy_enrollment_state(
                    call_data.get("enrollment_state", "untrained"),
                    requested_sample_count,
                ),
                sample_count=requested_sample_count,
                sample_items=requested_sample_items,
                enrollment_started_at=call_data.get("enrollment_started_at", now_iso),
                last_sample_at=call_data.get("last_sample_at", ""),
                last_built_at=call_data.get("last_built_at", ""),
            )
        else:
            session = await storage.async_update_enrollment_session(
                session_id=session.session_id,
                state_name=_session_state_from_legacy_enrollment_state(
                    call_data.get("enrollment_state", legacy_voice_profile_enrollment_state(session)),
                    requested_sample_count,
                ),
                sample_count=requested_sample_count,
                sample_items=requested_sample_items,
                enrollment_started_at=call_data.get("enrollment_started_at", session.enrollment_started_at),
                last_sample_at=call_data.get("last_sample_at", session.last_sample_at),
                last_built_at=call_data.get("last_built_at", session.last_built_at),
            )

        await self.sync_manifest(
            session,
            target_sample_count=max(1, requested_sample_count or DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT),
        )

        profile = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=voice_profile_id,
            name=call_data["name"],
            session=session,
            enrollment_source=call_data.get("enrollment_source", ""),
            speaker_embedding_id=call_data.get("speaker_embedding_id", ""),
            attribution_confidence=(
                float(call_data["attribution_confidence"])
                if call_data.get("attribution_confidence") is not None
                else None
            ),
            disabled=bool(call_data.get("disabled", False)),
            consent=dict(call_data.get("consent", {})),
            tts_voice=call_data.get("tts_voice", ""),
        )
        state = await storage.async_update_voice_profile(
            profile,
            set_as_default=bool(call_data.get("set_as_default", False)),
        )
        return {
            "voice_profile_count": len(state.voice_profiles),
            "default_voice_profile_id": (
                state.default_voice_profile.voice_profile_id if state.default_voice_profile is not None else None
            ),
        }

    async def start_enrollment(self, call_data: dict[str, Any]) -> dict[str, Any]:
        preferred_provider = call_data.get("capture_provider")
        _, capture_capability = await self.require_capture_provider(
            preferred_provider,
            publish_repairs=True,
        )

        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        person_id = call_data["person_id"]
        existing_person = state.person_profiles.get(person_id)
        person_name = existing_person.name if existing_person is not None else str(call_data.get("voice_name") or person_id)
        voice_profile_id = (
            str(call_data.get("voice_profile_id") or "").strip()
            or (str(existing_person.voice_profile_id or "").strip() if existing_person is not None else "")
        )
        if not voice_profile_id:
            voice_profile_id = _voice_profile_id_for_person(person_id)

        existing_voice = state.voice_profiles.get(voice_profile_id)
        now_iso = datetime.now(timezone.utc).isoformat()
        existing_consent = dict(existing_voice.consent) if existing_voice is not None else {}
        voice_consent = dict(existing_consent.get("voice_enrollment", {}))
        local_only = bool(call_data.get("local_only", True))
        voice_consent.update(
            {
                "enabled": True,
                "local_only": local_only,
                "consent_acknowledged": True,
                "consent_acknowledged_at": now_iso,
            }
        )
        merged_consent = {**existing_consent, "voice_enrollment": voice_consent}

        existing_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        reusable_session = (
            existing_session is not None
            and existing_session.cleanup_status not in {
                VOICE_ENROLLMENT_CLEANUP_STATUS_COMPLETE,
                VOICE_ENROLLMENT_CLEANUP_STATUS_FAILED,
            }
            and existing_session.state not in {
                VOICE_ENROLLMENT_STATE_CANCELLED_PENDING_CLEANUP,
                VOICE_ENROLLMENT_STATE_COMPLETED_PENDING_CLEANUP,
                VOICE_ENROLLMENT_STATE_FAILED_PENDING_CLEANUP,
                VOICE_ENROLLMENT_STATE_TIMEOUT_PENDING_CLEANUP,
                VOICE_ENROLLMENT_STATE_CLEANUP_COMPLETE,
                VOICE_ENROLLMENT_STATE_CLEANUP_FAILED,
            }
        )

        if reusable_session:
            session = await storage.async_update_enrollment_session(
                session_id=existing_session.session_id,
                state_name=existing_session.state,
                sample_count=existing_session.sample_count,
                sample_items=list(existing_session.sample_items),
                enrollment_started_at=(
                    existing_session.enrollment_started_at
                    or (existing_voice.enrollment_started_at if existing_voice and existing_voice.enrollment_started_at else now_iso)
                ),
                last_sample_at=existing_session.last_sample_at,
                last_built_at=existing_session.last_built_at,
                cleanup_status=existing_session.cleanup_status,
                metadata={
                    **dict(existing_session.metadata),
                    "provider_type": capture_capability.provider_type,
                    "capture_provider_status": capture_capability.status,
                },
            )
            session.capture_provider = capture_capability.provider_type
        else:
            session = enrollment_session_for_start(
                person_id=person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items) if existing_voice is not None else [],
                enrollment_started_at=(existing_voice.enrollment_started_at if existing_voice and existing_voice.enrollment_started_at else now_iso),
            )
            session.capture_provider = capture_capability.provider_type
            session.metadata.update(
                {
                    "provider_type": capture_capability.provider_type,
                    "capture_provider_status": capture_capability.status,
                }
            )
            await storage.async_upsert_enrollment_session(session)
        await self.sync_manifest(session, target_sample_count=DEFAULT_ENROLLMENT_TARGET_SAMPLE_COUNT)

        profile = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=voice_profile_id,
            name=str(call_data.get("voice_name") or person_name),
            session=session,
            enrollment_source=(existing_voice.enrollment_source if existing_voice is not None else "people_setup") or "people_setup",
            speaker_embedding_id=existing_voice.speaker_embedding_id if existing_voice is not None else "",
            attribution_confidence=existing_voice.attribution_confidence if existing_voice is not None else None,
            disabled=False,
            consent=merged_consent,
            tts_voice=existing_voice.tts_voice if existing_voice is not None else "",
        )
        await storage.async_update_voice_profile(profile)

        if existing_person is not None:
            person_profile = PersonProfile(
                person_id=existing_person.person_id,
                name=existing_person.name,
                linked_area_id=existing_person.linked_area_id,
                ble_device_ids=list(existing_person.ble_device_ids),
                aqara_presence_entity_ids=list(existing_person.aqara_presence_entity_ids),
                voice_profile_id=voice_profile_id,
                consent=dict(existing_person.consent),
                mobile_notify_targets=list(existing_person.mobile_notify_targets),
                preferred_mobile_target=existing_person.preferred_mobile_target,
                mobile_voice_endpoint_enabled=existing_person.mobile_voice_endpoint_enabled,
                is_minor=existing_person.is_minor,
                guardian_controls_required=existing_person.guardian_controls_required,
                minor_allow_general_qna=existing_person.minor_allow_general_qna,
                minor_allowed_intent_classes=list(existing_person.minor_allowed_intent_classes),
                minor_content_filter_level=existing_person.minor_content_filter_level,
                notes=existing_person.notes,
            )
            await storage.async_update_person_profile(
                person_profile,
                set_as_default=(
                    state.default_person_profile is not None
                    and state.default_person_profile.person_id == person_profile.person_id
                ),
            )

        return {
            "started": True,
            "person_id": person_id,
            "voice_profile_id": voice_profile_id,
            "enrollment_session_id": session.session_id,
            "enrollment_state": profile.enrollment_state,
            "sample_count": profile.sample_count,
            "local_only": local_only,
            "capture_provider": capture_capability.provider_type,
        }

    async def record_sample(self, call_data: dict[str, Any]) -> dict[str, Any]:
        skip_storage_preflight = bool(call_data.get("skip_storage_preflight", False))
        storage_provider = None
        if not skip_storage_preflight:
            storage_provider = await self.require_storage_preflight()

        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = call_data["voice_profile_id"]
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")
        if existing_voice.disabled:
            raise vol.Invalid("voice profile is disabled")

        now_iso = datetime.now(timezone.utc).isoformat()
        sample_id = f"sample_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}"
        sample_payload: dict[str, Any] = {
            "sample_id": sample_id,
            "speech_text": str(call_data.get("speech_text", "")).strip(),
            "captured_at": now_iso,
            "source": str(call_data.get("source", "guided_phrase") or "guided_phrase"),
        }
        if call_data.get("quality_score") is not None:
            sample_payload["quality_score"] = float(call_data["quality_score"])
        if call_data.get("recording_duration_ms") is not None:
            sample_payload["recording_duration_ms"] = int(call_data["recording_duration_ms"])
        if call_data.get("phrase_index") is not None:
            sample_payload["phrase_index"] = int(call_data["phrase_index"])
        if call_data.get("recording_mime_type"):
            sample_payload["recording_mime_type"] = str(call_data["recording_mime_type"])
        if call_data.get("recording_size_bytes") is not None:
            sample_payload["recording_size_bytes"] = int(call_data["recording_size_bytes"])

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        preferred_provider = call_data.get("capture_provider")
        if not str(preferred_provider or "").strip() and enrollment_session is not None:
            preferred_provider = enrollment_session.capture_provider
        skip_capture_provider_preflight = bool(call_data.get("skip_capture_provider_preflight", False))
        if skip_capture_provider_preflight:
            normalized_provider = self._normalize_capture_provider_preference(preferred_provider)
            provider_type_for_metadata = (
                CAPTURE_PROVIDER_PREFERENCE_SATELLITE
                if normalized_provider == CAPTURE_PROVIDER_PREFERENCE_SATELLITE
                else CAPTURE_PROVIDER_TYPE_BROWSER_MICROPHONE
            )
            provider_status_for_metadata = "ready"
        else:
            _, capture_capability = await self.require_capture_provider(
                preferred_provider,
                publish_repairs=True,
            )
            provider_type_for_metadata = capture_capability.provider_type
            provider_status_for_metadata = capture_capability.status

        phrase_index = call_data.get("phrase_index")
        try:
            phrase_index_value = int(phrase_index) if phrase_index is not None else None
        except (TypeError, ValueError):
            phrase_index_value = None

        preferred_path = str(call_data.get("recording_path", "") or "").strip() or None
        if skip_storage_preflight:
            if preferred_path:
                sample_payload["recording_path"] = preferred_path
        else:
            resolved_path = await self.hass.async_add_executor_job(
                lambda: storage_provider.resolve_recording_path(
                    session_id=enrollment_session.session_id,
                    preferred_path=preferred_path,
                    phrase_index=phrase_index_value,
                )
            )

            if resolved_path:
                sample_payload["recording_path"] = resolved_path
                artifacts = await self.hass.async_add_executor_job(
                    lambda: storage_provider.list_session_artifacts(enrollment_session.session_id)
                )
                matching = next((artifact for artifact in artifacts if artifact.artifact_path == resolved_path), None)
                if matching is not None:
                    sample_payload["recording_size_bytes"] = int(matching.bytes_size)

        enrollment_session = enrollment_session_record_sample(
            enrollment_session,
            sample_payload=sample_payload,
            captured_at=now_iso,
        )
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
            metadata={
                **dict(enrollment_session.metadata),
                "last_sample_id": sample_id,
                "last_sample_at": now_iso,
                "provider_type": provider_type_for_metadata,
                "capture_provider_status": provider_status_for_metadata,
            },
        )
        await self.sync_manifest(enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=existing_voice.speaker_embedding_id,
            attribution_confidence=existing_voice.attribution_confidence,
            disabled=existing_voice.disabled,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)

        return {
            "captured": True,
            "voice_profile_id": voice_profile_id,
            "sample_id": sample_id,
            "sample_count": updated.sample_count,
        }

    async def remove_sample(self, call_data: dict[str, Any]) -> dict[str, Any]:
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = call_data["voice_profile_id"]
        sample_id = call_data["sample_id"]
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")
        now_iso = datetime.now(timezone.utc).isoformat()
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or now_iso,
            )

        enrollment_session, removed_items = enrollment_session_remove_sample(
            enrollment_session,
            sample_id=sample_id,
            now_iso=now_iso,
        )
        if not removed_items:
            raise vol.Invalid("sample_id not found")

        provider = self.resolve_provider()
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await self.sync_manifest(enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id=(existing_voice.speaker_embedding_id if enrollment_session.sample_count > 0 else ""),
            attribution_confidence=(existing_voice.attribution_confidence if enrollment_session.sample_count > 0 else None),
            disabled=existing_voice.disabled,
            consent=dict(existing_voice.consent),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        if provider is not None:
            recording_paths = _sample_recording_paths(removed_items)
            if recording_paths:
                await self.hass.async_add_executor_job(
                    lambda: provider.delete_recording_artifacts(
                        session_id=enrollment_session.session_id,
                        artifact_paths=recording_paths,
                    )
                )

        return {
            "removed": True,
            "voice_profile_id": voice_profile_id,
            "sample_count": updated.sample_count,
        }

    async def build_voice_profile(self, call_data: dict[str, Any]) -> dict[str, Any]:
        completion = await self.complete_enrollment(call_data)
        return {
            "built": bool(completion.get("completed", False)),
            "voice_profile_id": completion.get("voice_profile_id"),
            "sample_count": completion.get("sample_count"),
            "person_id": completion.get("person_id"),
            "cleanup_result_code": completion.get("cleanup_result_code"),
            "completion_state": completion.get("completion_state"),
        }

    async def reset_voice_profile(self, call_data: dict[str, Any]) -> dict[str, Any]:
        storage = ConciergeStorage(self.hass)
        state = await storage.async_load_state()
        voice_profile_id = call_data["voice_profile_id"]
        preserve_consent = bool(call_data.get("preserve_consent", True))
        existing_voice = state.voice_profiles.get(voice_profile_id)
        if existing_voice is None:
            raise vol.Invalid("voice_profile_id is not configured")

        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)
        if enrollment_session is None:
            matched_person_id = ""
            for profile in state.person_profiles.values():
                if profile.voice_profile_id == voice_profile_id:
                    matched_person_id = profile.person_id
                    break
            enrollment_session = enrollment_session_for_start(
                person_id=matched_person_id,
                voice_profile_id=voice_profile_id,
                existing_sample_items=list(existing_voice.sample_items),
                enrollment_started_at=existing_voice.enrollment_started_at or datetime.now(timezone.utc).isoformat(),
            )

        enrollment_session = enrollment_session_reset(enrollment_session)
        enrollment_session = await storage.async_update_enrollment_session(
            session_id=enrollment_session.session_id,
            state_name=enrollment_session.state,
            sample_count=enrollment_session.sample_count,
            sample_items=list(enrollment_session.sample_items),
            enrollment_started_at=enrollment_session.enrollment_started_at,
            last_sample_at=enrollment_session.last_sample_at,
            last_built_at=enrollment_session.last_built_at,
        )
        await self.sync_manifest(enrollment_session)

        updated = _project_voice_profile_from_session(
            existing_voice=existing_voice,
            voice_profile_id=existing_voice.voice_profile_id,
            name=existing_voice.name,
            session=enrollment_session,
            enrollment_source=existing_voice.enrollment_source,
            speaker_embedding_id="",
            attribution_confidence=None,
            disabled=False,
            consent=(dict(existing_voice.consent) if preserve_consent else {}),
            tts_voice=existing_voice.tts_voice,
        )
        await storage.async_update_voice_profile(updated)
        enrollment_session, cleanup_summary = await self.execute_cleanup(
            storage,
            enrollment_session,
            cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_MANUAL,
        )

        return {
            "reset": True,
            "voice_profile_id": voice_profile_id,
            "preserve_consent": preserve_consent,
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
        }

    async def delete_voice_profile(self, call_data: dict[str, Any]) -> dict[str, Any]:
        storage = ConciergeStorage(self.hass)
        current_state = await storage.async_load_state()
        voice_profile_id = call_data["voice_profile_id"]
        unlink_from_people = bool(call_data.get("unlink_from_people", True))
        existing_voice = current_state.voice_profiles.get(voice_profile_id)
        enrollment_session = await storage.async_get_latest_enrollment_session_for_voice_profile(voice_profile_id)

        cleanup_summary = {
            "cleanup_result_code": "not_started",
            "artifacts_seen_count": 0,
            "artifacts_deleted_count": 0,
            "artifacts_missing_count": 0,
            "errors_redacted_or_sanitized": [],
        }
        if enrollment_session is not None:
            enrollment_session, cleanup_summary = await self.execute_cleanup(
                storage,
                enrollment_session,
                cleanup_reason=VOICE_ENROLLMENT_CLEANUP_REASON_CANCELLED,
            )

        state = await storage.async_delete_voice_profile(
            voice_profile_id,
            unlink_from_people=unlink_from_people,
        )

        if enrollment_session is None and existing_voice is not None:
            provider = self.resolve_provider()
            if provider is not None:
                recording_paths = _sample_recording_paths(list(existing_voice.sample_items))
                if recording_paths:
                    await self.hass.async_add_executor_job(lambda: provider.delete_owned_artifacts(recording_paths))

        return {
            "deleted": True,
            "voice_profile_id": voice_profile_id,
            "unlink_from_people": unlink_from_people,
            "voice_profile_count": len(state.voice_profiles),
            "cleanup_result_code": cleanup_summary["cleanup_result_code"],
        }