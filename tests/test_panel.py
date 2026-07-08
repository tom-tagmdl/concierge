from __future__ import annotations

from types import SimpleNamespace

import pytest
from aiohttp import web
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, CONNECTION_NETWORK_MAC

from custom_components.concierge import panel as panel_module
from custom_components.concierge.enrollment_storage import StorageReadinessResult
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
    """Upload endpoint should reject writes when provider readiness fails."""

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

    fake_provider = SimpleNamespace(
        validate_ready=lambda: StorageReadinessResult(
            ready=False,
            failure_code="storage_unavailable",
            failure_message_safe="external enrollment storage is unavailable",
            provider_type="mounted_path",
        )
    )
    monkeypatch.setattr(panel_module, "_voice_storage_provider_from_hass", lambda hass: fake_provider)

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
