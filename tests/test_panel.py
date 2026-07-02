from __future__ import annotations

from types import SimpleNamespace

from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, CONNECTION_NETWORK_MAC

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
