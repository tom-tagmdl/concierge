"""Architecture protection tests for enrollment capture provider abstraction."""

from __future__ import annotations

import pytest

import voluptuous as vol

from custom_components.concierge.enrollment_capture import BrowserMicCaptureProvider
from custom_components.concierge.enrollment_capture import CAPTURE_PROVIDER_REASON_SATELLITE_CAPTURE_NOT_SUPPORTED
from custom_components.concierge.enrollment_capture import CAPTURE_PROVIDER_REASON_SATELLITE_PROVIDER_NOT_CONFIGURED
from custom_components.concierge.enrollment_capture import CAPTURE_PROVIDER_STATUS_NO_CAPTURE_API
from custom_components.concierge.enrollment_capture import CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED
from custom_components.concierge.enrollment_capture import CAPTURE_PROVIDER_STATUS_READY
from custom_components.concierge.enrollment_capture import CaptureSampleRequest
from custom_components.concierge.enrollment_capture import SatelliteCaptureProvider


async def test_browser_provider_capability_is_sanitized_and_ready(hass) -> None:
    """Browser provider capability should expose only sanitized availability fields."""

    async def _require_storage_preflight(publish_repairs: bool):
        assert publish_repairs is False
        return object()

    provider = BrowserMicCaptureProvider(hass, _require_storage_preflight)
    capability = await provider.get_capability()

    assert capability.status == CAPTURE_PROVIDER_STATUS_READY
    projection = capability.as_public_dict()
    assert projection["provider_type"] == "browser_microphone"
    assert projection["provider_available"] is True
    assert "provider_device_id" not in projection
    assert "recording_path" not in projection


async def test_browser_provider_not_configured_maps_to_sanitized_status(hass) -> None:
    """Browser provider should map storage-not-configured into sanitized capability status."""

    async def _require_storage_preflight(publish_repairs: bool):
        raise vol.Invalid("external enrollment storage preflight failed: storage_not_configured")

    provider = BrowserMicCaptureProvider(hass, _require_storage_preflight)
    capability = await provider.get_capability()

    assert capability.available is False
    assert capability.supported is True
    assert capability.status == CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED


async def test_satellite_provider_is_future_unsupported_and_non_captureable(hass) -> None:
    """Satellite provider is modeled honestly as not-configured/unsupported when unconfigured."""
    provider = SatelliteCaptureProvider(hass)
    capability = await provider.get_capability()

    assert capability.available is False
    assert capability.supported is False
    assert capability.status == CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED
    assert capability.reason_code == CAPTURE_PROVIDER_REASON_SATELLITE_PROVIDER_NOT_CONFIGURED

    with pytest.raises(Exception, match="capture_provider_unsupported"):
        await provider.capture_sample(
            CaptureSampleRequest(
                person_id="person.tom",
                voice_profile_id="tom_voice",
                phrase_index=0,
                audio_content_type="audio/wav",
                audio_bytes=b"sample",
            )
        )


async def test_satellite_provider_reports_no_capture_api_when_entities_exist(hass, monkeypatch) -> None:
    """Satellite provider should report no_capture_api when entities exist but capture API is unsupported."""
    provider = SatelliteCaptureProvider(hass)
    monkeypatch.setattr(provider, "_has_configured_satellite_entities", lambda: True)

    capability = await provider.get_capability()

    assert capability.available is False
    assert capability.supported is False
    assert capability.status == CAPTURE_PROVIDER_STATUS_NO_CAPTURE_API
    assert capability.reason_code == CAPTURE_PROVIDER_REASON_SATELLITE_CAPTURE_NOT_SUPPORTED


async def test_satellite_capture_poc_reports_honest_unavailable_entity(hass) -> None:
    """Satellite POC should fail honestly when no assist satellite entities are available."""
    provider = SatelliteCaptureProvider(hass, capture_api_supported=True, provider_selected=True)

    result, audio_bytes, content_type = await provider.run_satellite_capture_poc(timeout_seconds=5.0)

    assert result["provider_type"] == "satellite"
    assert result["satellite_entity_available"] is False
    assert result["capture_started"] is False
    assert result["chunks_received"] == 0
    assert result["bytes_received"] == 0
    assert result["failure_code"] == "satellite_entity_not_found"
    assert audio_bytes is None
    assert content_type is None


async def test_satellite_capture_poc_result_is_sanitized(hass, monkeypatch) -> None:
    """Satellite POC result must not expose identifiers, raw chunks, or paths."""
    provider = SatelliteCaptureProvider(hass, capture_api_supported=True, provider_selected=True)

    monkeypatch.setattr(
        provider,
        "_discover_satellite_entities",
        lambda: [{"entity_id": "assist_satellite.voice_pe", "device_id": "device-123", "platform": "esphome"}],
    )

    async def _fake_invoke(*, device_id: str, timeout_seconds: float):
        del device_id, timeout_seconds
        return True, {
            "capture_command_available": True,
            "capture_started": True,
            "chunks_received": 2,
            "bytes_received": 16,
            "audio_rate": 16000,
            "audio_width": 2,
            "audio_channels": 1,
            "failure_code": None,
            "failure_message_safe": None,
            "audio_bytes": b"1234567890abcdef",
        }

    monkeypatch.setattr(provider, "_invoke_assist_pipeline_device_capture", _fake_invoke)

    result, audio_bytes, content_type = await provider.run_satellite_capture_poc(timeout_seconds=5.0)

    assert result["satellite_entity_available"] is True
    assert result["capture_command_available"] is True
    assert result["capture_started"] is True
    assert result["chunks_received"] == 2
    assert result["bytes_received"] == 16
    assert result["audio_rate"] == 16000
    assert result["audio_width"] == 2
    assert result["audio_channels"] == 1
    assert result["failure_code"] is None
    assert "audio_bytes" not in result
    assert "device_id" not in result
    assert "entity_id" not in result
    assert "recording_path" not in result
    assert audio_bytes == b"1234567890abcdef"
    assert content_type == "audio/L16; rate=16000; channels=1"


async def test_satellite_capture_prompt_arms_capture_before_ask_question(hass, monkeypatch) -> None:
    """Satellite enrollment should arm raw capture before prompting the satellite to listen."""
    provider = SatelliteCaptureProvider(hass, capture_api_supported=True, provider_selected=True)

    monkeypatch.setattr(
        provider,
        "_discover_satellite_entities",
        lambda: [{"entity_id": "assist_satellite.voice_pe", "device_id": "device-123", "platform": "esphome"}],
    )

    service_calls: list[tuple[str, str, dict[str, object], dict[str, str] | None, bool]] = []
    step_order: list[str] = []

    async def _fake_async_call(domain, service, service_data=None, target=None, blocking=False, **kwargs):
        step_order.append("prompt")
        service_calls.append((domain, service, dict(service_data or {}), target, blocking))
        assert kwargs.get("return_response") is True
        return {"id": "captured", "sentence": "Please play soft jazz in the office speaker group for fifteen minutes."}

    async def _fake_invoke(*, device_id: str, timeout_seconds: float, capture_ready=None):
        assert device_id == "device-123"
        assert timeout_seconds == 5.0
        step_order.append("capture")
        assert capture_ready is not None
        capture_ready.set()
        return True, {
            "capture_command_available": True,
            "capture_started": True,
            "chunks_received": 1,
            "bytes_received": 8,
            "audio_rate": 16000,
            "audio_width": 2,
            "audio_channels": 1,
            "failure_code": None,
            "failure_message_safe": None,
            "audio_bytes": b"12345678",
        }

    monkeypatch.setattr(hass.services, "async_call", _fake_async_call)
    monkeypatch.setattr(provider, "_invoke_assist_pipeline_device_capture", _fake_invoke)

    result, audio_bytes, content_type = await provider.capture_satellite_audio(
        timeout_seconds=5.0,
        satellite_entity_id="assist_satellite.voice_pe",
        device_id=None,
        prompt_text="Please read phrase 5 now.",
        preannounce=False,
    )

    assert result["failure_code"] is None
    assert audio_bytes == b"12345678"
    assert content_type == "audio/L16; rate=16000; channels=1"
    assert step_order == ["capture", "prompt"]
    assert service_calls == [
        (
            "assist_satellite",
            "ask_question",
            {
                "entity_id": "assist_satellite.voice_pe",
                "question": "Please read phrase 5 now.",
                "preannounce": False,
            },
            None,
            True,
        )
    ]
