from __future__ import annotations

from types import SimpleNamespace

import pytest
import voluptuous as vol
from aiohttp import web
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, CONNECTION_NETWORK_MAC

from custom_components.concierge import panel as panel_module
from custom_components.concierge.panel import ConciergeVoiceEnrollmentCaptureView
from custom_components.concierge.panel import ConciergeVoiceEnrollmentProgressView
from custom_components.concierge.panel import ConciergeVoiceEnrollmentRecoveryView
from custom_components.concierge.panel import ConciergeVoiceEnrollmentUploadView
from custom_components.concierge.panel import _person_ble_suggestions


def test_person_ble_suggestions_use_attached_tracker_devices() -> None:
    """BLE suggestions should come from attached tracker device connections."""
    person = SimpleNamespace(
        attributes={
            "device_trackers": [
                "device_tracker.phone",
                "device_tracker.watch",
                "device_tracker.orphan",
            ]
        }
    )
    entity_registry = SimpleNamespace(
        entities={
            "device_tracker.phone": SimpleNamespace(device_id="device_phone"),
            "device_tracker.watch": SimpleNamespace(device_id="device_watch"),
            "device_tracker.orphan": SimpleNamespace(device_id=None),
        }
    )
    device_registry = SimpleNamespace(
        devices={
            "device_phone": SimpleNamespace(
                connections={
                    (CONNECTION_BLUETOOTH, "AA:BB:CC:DD:EE:FF"),
                    (CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF"),
                }
            ),
            "device_watch": SimpleNamespace(
                connections={
                    (CONNECTION_BLUETOOTH, "11:22:33:44:55:66"),
                }
            ),
        }
    )

    suggestions, sources = _person_ble_suggestions(person, entity_registry, device_registry)

    assert suggestions == ["11:22:33:44:55:66", "AA:BB:CC:DD:EE:FF"]
    assert sources == {
        "11:22:33:44:55:66": ["device_tracker.watch"],
        "AA:BB:CC:DD:EE:FF": ["device_tracker.phone"],
    }


async def test_voice_upload_rejects_when_storage_preflight_fails(hass, monkeypatch) -> None:
    """Upload endpoint should delegate to orchestrator and surface preflight failures."""

    class _FakePart:
        def __init__(self, name: str, *, text_value: str = "", data_value: bytes = b"", headers=None):
            self.name = name
            self._text_value = text_value
            self._data_value = data_value
            self.headers = headers or {}

        async def text(self):
            return self._text_value

        async def read(self, decode=False):
            return self._data_value

    class _FakeReader:
        def __init__(self, parts):
            self._parts = iter(parts)

        async def next(self):
            return next(self._parts, None)

    class _FakeRequest:
        def __init__(self, hass, reader):
            self.app = {"hass": hass}
            self._reader = reader

        async def multipart(self):
            return self._reader

    delegated = {}

    async def _fake_upload(self, *, person_id, voice_profile_id, phrase_index, audio_content_type, audio_bytes):
        delegated.update(
            {
                "person_id": person_id,
                "voice_profile_id": voice_profile_id,
                "phrase_index": phrase_index,
                "audio_content_type": audio_content_type,
                "audio_size": len(audio_bytes),
            }
        )
        raise vol.Invalid("external enrollment storage preflight failed: storage_unavailable")

    monkeypatch.setattr(panel_module.EnrollmentOrchestrator, "upload_browser_sample", _fake_upload)

    reader = _FakeReader(
        [
            _FakePart("person_id", text_value="tom"),
            _FakePart("voice_profile_id", text_value="tom_voice"),
            _FakePart("phrase_index", text_value="0"),
            _FakePart(
                "audio",
                data_value=b"audio-bytes",
                headers={"Content-Type": "audio/wav"},
            ),
        ]
    )

    with pytest.raises(web.HTTPPreconditionFailed, match="storage_unavailable"):
        await ConciergeVoiceEnrollmentUploadView().post(_FakeRequest(hass, reader))

    assert delegated["person_id"] == "tom"
    assert delegated["voice_profile_id"] == "tom_voice"
    assert delegated["phrase_index"] == 0
    assert delegated["audio_content_type"] == "audio/wav"
    assert delegated["audio_size"] == len(b"audio-bytes")


async def test_voice_capture_routes_sample_registration_through_orchestrator(hass, monkeypatch) -> None:
    """Capture endpoint should delegate upload and registration sequencing to orchestrator."""

    class _FakePart:
        def __init__(self, name: str, *, text_value: str = "", data_value: bytes = b"", headers=None):
            self.name = name
            self._text_value = text_value
            self._data_value = data_value
            self.headers = headers or {}

        async def text(self):
            return self._text_value

        async def read(self, decode=False):
            return self._data_value

    class _FakeReader:
        def __init__(self, parts):
            self._parts = iter(parts)

        async def next(self):
            return next(self._parts, None)

    class _FakeRequest:
        def __init__(self, hass, reader):
            self.app = {"hass": hass}
            self._reader = reader

        async def multipart(self):
            return self._reader

    delegated = {}

    async def _fake_capture(self, **kwargs):
        delegated.update(kwargs)
        return {
            "saved": True,
            "captured": True,
            "voice_profile_id": kwargs["voice_profile_id"],
            "sample_id": "sample-1",
            "sample_count": 1,
            "recording_path": "external_enrollment_root/session/sample.wav",
            "recording_mime_type": kwargs["audio_content_type"],
            "recording_size_bytes": len(kwargs["audio_bytes"]),
            "phrase_index": kwargs["phrase_index"],
        }

    monkeypatch.setattr(panel_module.EnrollmentOrchestrator, "capture_browser_sample", _fake_capture)

    reader = _FakeReader(
        [
            _FakePart("person_id", text_value="tom"),
            _FakePart("voice_profile_id", text_value="tom_voice"),
            _FakePart("phrase_index", text_value="1"),
            _FakePart("speech_text", text_value="Hello Concierge test phrase"),
            _FakePart("source", text_value="guided_enrollment_dialog"),
            _FakePart("recording_duration_ms", text_value="1450"),
            _FakePart(
                "audio",
                data_value=b"audio-bytes",
                headers={"Content-Type": "audio/webm"},
            ),
        ]
    )

    response = await ConciergeVoiceEnrollmentCaptureView().post(_FakeRequest(hass, reader))
    payload = response.text

    assert delegated["person_id"] == "tom"
    assert delegated["voice_profile_id"] == "tom_voice"
    assert delegated["phrase_index"] == 1
    assert delegated["speech_text"] == "Hello Concierge test phrase"
    assert delegated["source"] == "guided_enrollment_dialog"
    assert delegated["recording_duration_ms"] == 1450
    assert delegated["audio_content_type"] == "audio/webm"
    assert delegated["audio_bytes"] == b"audio-bytes"
    assert "captured" in payload


async def test_voice_progress_view_delegates_to_orchestrator(hass, monkeypatch) -> None:
    """Progress endpoint should delegate to orchestrator rather than deriving state locally."""

    class _FakeRequest:
        def __init__(self, hass):
            self.app = {"hass": hass}
            self.query = {"person_id": "person.tom", "voice_profile_id": "tom_voice"}

    delegated = {}

    async def _fake_progress(self, *, person_id, voice_profile_id=None):
        delegated["person_id"] = person_id
        delegated["voice_profile_id"] = voice_profile_id
        return {
            "found": True,
            "person_id": person_id,
            "voice_profile_id": voice_profile_id,
            "progress": {
                "session_id": "session_1",
                "enrollment_state": "sample_received",
                "sample_count": 1,
                "target_sample_count": 3,
                "completion_percentage": 33,
                "is_complete": False,
                "is_active": True,
                "is_terminal": False,
                "cleanup_status": "not_started",
                "provider_type": "browser_microphone",
                "last_updated_at": "2026-07-08T12:00:00+00:00",
                "user_safe_status_summary": "Sample captured",
            },
        }

    monkeypatch.setattr(panel_module.EnrollmentOrchestrator, "get_browser_enrollment_progress", _fake_progress)

    response = await ConciergeVoiceEnrollmentProgressView().get(_FakeRequest(hass))
    payload = response.text

    assert delegated["person_id"] == "person.tom"
    assert delegated["voice_profile_id"] == "tom_voice"
    assert "sample_count" in payload
    assert "recording_path" not in payload
    assert "speech_text" not in payload


async def test_voice_recovery_view_delegates_to_orchestrator(hass, monkeypatch) -> None:
    """Recovery endpoint should delegate cancellation/recovery actions to orchestrator."""

    class _FakeRequest:
        def __init__(self, hass, payload):
            self.app = {"hass": hass}
            self._payload = payload

        async def json(self):
            return self._payload

    delegated = {}

    async def _fake_cancel(self, call_data):
        delegated["cancel"] = dict(call_data)
        return {
            "canceled": True,
            "already_terminal": False,
            "not_found": False,
            "cleanup_result_code": "complete",
            "session_id": "session_1",
        }

    async def _fake_recover(self, call_data):
        delegated["recover"] = dict(call_data)
        return {
            "recoverable": True,
            "recovered": True,
            "not_found": False,
            "recovery_state": "resume_available",
            "progress": {
                "sample_count": 1,
                "target_sample_count": 3,
                "completion_percentage": 33,
                "user_safe_status_summary": "Sample captured",
            },
        }

    monkeypatch.setattr(panel_module.EnrollmentOrchestrator, "cancel_enrollment", _fake_cancel)
    monkeypatch.setattr(panel_module.EnrollmentOrchestrator, "recover_enrollment", _fake_recover)

    cancel_response = await ConciergeVoiceEnrollmentRecoveryView().post(
        _FakeRequest(
            hass,
            {
                "action": "cancel",
                "person_id": "person.tom",
                "voice_profile_id": "tom_voice",
            },
        )
    )
    recover_response = await ConciergeVoiceEnrollmentRecoveryView().post(
        _FakeRequest(
            hass,
            {
                "action": "recover",
                "person_id": "person.tom",
                "voice_profile_id": "tom_voice",
            },
        )
    )

    assert delegated["cancel"]["person_id"] == "person.tom"
    assert delegated["recover"]["voice_profile_id"] == "tom_voice"
    assert "recording_path" not in cancel_response.text
    assert "speech_text" not in recover_response.text
