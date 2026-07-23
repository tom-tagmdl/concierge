"""Issue #426 runtime voice attribution lifecycle end-to-end validation tests."""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.concierge import services as services_module
from custom_components.concierge.const import DOMAIN
from custom_components.concierge.models import PersonProfile
from custom_components.concierge.storage import ConciergeStorage

from runtime_voice_attribution_lifecycle_matrix import (
    ATTRIBUTION_SCENARIOS,
    AUTHORIZATION_SCENARIOS,
    CORRELATION_SCENARIOS,
    FALLBACK_SCENARIOS,
    FRESHNESS_SCENARIOS,
    HANDOFF_SCENARIOS,
    PRIVACY_ASSERTIONS,
    build_governance_checklist_output,
    render_governance_checklist_markdown,
)


_SKIP_HA_INTEGRATION = bool(os.environ.get("PYTEST_DISABLE_PLUGIN_AUTOLOAD"))
_HA_SKIP_REASON = "Requires Home Assistant pytest fixtures; skipped in plugin-autoload-disabled runs."


@pytest.fixture
def enable_custom_integrations() -> None:
    """Satisfy targeted test runs that require this shared fixture."""
    return None


def _service_call(*, target: str, intent_class: str) -> SimpleNamespace:
    return SimpleNamespace(data={"target": target, "intent_class": intent_class})


def _register_lookup_service(
    hass: HomeAssistant,
    *,
    responses: list[dict[str, object]],
    captured_calls: list[dict[str, object]],
) -> None:
    if hass.services.has_service("voice_identity", "get_identity_context"):
        hass.services.async_remove("voice_identity", "get_identity_context")

    state = {"index": 0}

    async def _handle_get_identity_context(call):
        captured_calls.append(dict(call.data))
        index = min(state["index"], len(responses) - 1)
        state["index"] += 1
        payload = responses[index]
        return {
            "success": True,
            "reason_code": "ready",
            "entry_id": "entry",
            "identity_context": dict(payload["identity_context"]),
            "runtime_attribution": dict(payload.get("runtime_attribution") or {}),
        }

    hass.services.async_register(
        "voice_identity",
        "get_identity_context",
        _handle_get_identity_context,
        supports_response=SupportsResponse.ONLY,
    )


def test_authoritative_lifecycle_matrix_contains_required_dimensions() -> None:
    assert len(ATTRIBUTION_SCENARIOS) >= 5
    assert len(FRESHNESS_SCENARIOS) >= 3
    assert len(HANDOFF_SCENARIOS) >= 2
    assert len(CORRELATION_SCENARIOS) >= 5
    assert len(FALLBACK_SCENARIOS) >= 2
    assert len(AUTHORIZATION_SCENARIOS) >= 5
    assert len(PRIVACY_ASSERTIONS) >= 6


@pytest.mark.parametrize("scenario", AUTHORIZATION_SCENARIOS, ids=[s["id"] for s in AUTHORIZATION_SCENARIOS])
def test_authorization_outcome_matrix_is_deterministic(scenario: dict[str, object]) -> None:
    runtime_context = {
        "identity_context": {
            "state": scenario["identity_state"],
            "confidence_band": scenario["confidence_band"],
        },
        "voice_identity_runtime_attribution": {
            "freshness": scenario["freshness_class"],
            "attribution_age_ms": scenario["attribution_age_ms"],
        },
    }
    decision = services_module._evaluate_runtime_identity_authorization_policy(
        call=_service_call(target=str(scenario["target"]), intent_class=str(scenario["intent_class"])),
        requested_target=str(scenario["target"]),
        resolved_target=str(scenario["target"]),
        runtime_context=runtime_context,
    )

    assert decision["identity_requirement_class"] == scenario["expected_requirement"]
    assert decision["identity_policy_outcome"] == scenario["expected_outcome"]
    assert decision["identity_policy_reason_code"] == scenario["expected_reason"]
    assert decision["allows_execution"] is scenario["expected_allows_execution"]


@pytest.mark.skipif(_SKIP_HA_INTEGRATION, reason=_HA_SKIP_REASON)
@pytest.mark.asyncio
async def test_lifecycle_handoff_supersession_uses_latest_speaker_same_conversation(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    area = ar.async_get(hass).async_create(name="Kitchen")
    await hass.services.async_call(
        DOMAIN,
        "update_room_config",
        {"area_id": area.id},
        blocking=True,
    )

    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="vp_tom"),
    )
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.david", name="David", voice_profile_id="vp_david"),
    )

    device_registry = dr.async_get(hass)
    satellite_device = device_registry.async_get_or_create(
        config_entry_id=setup_integration.entry_id,
        identifiers={("test", "satellite-kitchen")},
        area_id=area.id,
    )
    satellite_entity = er.async_get(hass).async_get_or_create(
        "assist_satellite",
        "test",
        "satellite-kitchen",
        device_id=satellite_device.id,
        suggested_object_id="kitchen_satellite",
        original_name="Kitchen Satellite",
    )

    captured_calls: list[dict[str, object]] = []
    _register_lookup_service(
        hass,
        responses=[
            {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "confidence": 0.92,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                },
                "runtime_attribution": {
                    "resolution_source": "conversation_id",
                    "freshness": "fresh",
                    "attribution_age_ms": 60,
                    "reason_code": "attribution_ready",
                },
            },
            {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.david",
                    "voice_profile_id": "vp_david",
                    "confidence": 0.93,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                },
                "runtime_attribution": {
                    "resolution_source": "conversation_id",
                    "freshness": "fresh",
                    "attribution_age_ms": 40,
                    "reason_code": "attribution_ready",
                },
            },
        ],
        captured_calls=captured_calls,
    )

    first = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "who am i",
            "intent_class": "general_qna",
            "context": {
                "conversation_id": "conv-426",
                "device_id": satellite_device.id,
                "satellite_id": satellite_entity.entity_id,
                "text": "who am i",
            },
        },
        blocking=True,
        return_response=True,
    )
    second = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "who am i",
            "intent_class": "general_qna",
            "context": {
                "conversation_id": "conv-426",
                "device_id": satellite_device.id,
                "satellite_id": satellite_entity.entity_id,
                "text": "who am i",
            },
        },
        blocking=True,
        return_response=True,
    )

    assert first["identity_self_query"]["resolved_person_id"] == "person.tom"
    assert second["identity_self_query"]["resolved_person_id"] == "person.david"
    assert second["execution_envelope"]["active_person_resolution"]["resolved_person_id"] == "person.david"

    assert len(captured_calls) == 2
    assert captured_calls[0]["conversation_id"] == "conv-426"
    assert captured_calls[1]["conversation_id"] == "conv-426"
    assert captured_calls[0]["room_id"] == area.id
    assert captured_calls[1]["room_id"] == area.id


@pytest.mark.skipif(_SKIP_HA_INTEGRATION, reason=_HA_SKIP_REASON)
@pytest.mark.asyncio
async def test_lifecycle_same_conversation_missing_identity_does_not_carry_forward_prior_speaker(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    _ = setup_integration

    storage = ConciergeStorage(hass)
    await storage.async_update_person_profile(
        PersonProfile(person_id="person.tom", name="Tom", voice_profile_id="vp_tom"),
    )

    captured_calls: list[dict[str, object]] = []
    _register_lookup_service(
        hass,
        responses=[
            {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "confidence": 0.92,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                },
                "runtime_attribution": {
                    "resolution_source": "conversation_id",
                    "freshness": "fresh",
                    "attribution_age_ms": 60,
                    "reason_code": "attribution_ready",
                },
            },
            {
                "identity_context": {
                    "state": "unknown",
                    "person_id": None,
                    "voice_profile_id": None,
                    "confidence": None,
                    "confidence_band": None,
                    "reason_code": "identity_context_missing",
                    "source": "voice_identity",
                },
                "runtime_attribution": {
                    "resolution_source": "conversation_id",
                    "freshness": "not_applicable",
                    "attribution_age_ms": None,
                    "reason_code": "identity_context_missing",
                },
            },
        ],
        captured_calls=captured_calls,
    )

    first = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "who am i",
            "intent_class": "general_qna",
            "context": {
                "conversation_id": "conv-426-carry",
                "text": "who am i",
            },
        },
        blocking=True,
        return_response=True,
    )
    second = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "who am i",
            "intent_class": "general_qna",
            "context": {
                "conversation_id": "conv-426-carry",
                "text": "who am i",
            },
        },
        blocking=True,
        return_response=True,
    )

    assert first["identity_self_query"]["resolved_person_id"] == "person.tom"
    assert second["identity_self_query"]["resolved_person_id"] is None
    assert second["identity_self_query"]["active_person_reason_code"] == "identity_context_missing"


@pytest.mark.skipif(_SKIP_HA_INTEGRATION, reason=_HA_SKIP_REASON)
@pytest.mark.asyncio
async def test_lifecycle_fallback_path_supported_non_authoritative_and_blocks_sensitive_execution(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    _ = setup_integration

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "media_player.preferred_music",
            "intent_class": "person_preference",
        },
        blocking=True,
        return_response=True,
    )

    ingress = result["conversation_agent_ingress"]
    assert ingress["ingress_mode"] == "fallback_service_or_automation"
    assert ingress["identity_authority"] == "non_authoritative_fallback"
    assert ingress["speaker_lookup"]["reason_code"] == "identity_audio_missing"

    assert result["identity_requirement_class"] == "identity_required"
    assert result["identity_policy_outcome"] == "deny"
    assert result["identity_policy_reason_code"] == "identity_required_but_missing"
    assert result["execution_outcome_category"] == "REFUSAL_SUCCESS"


@pytest.mark.skipif(_SKIP_HA_INTEGRATION, reason=_HA_SKIP_REASON)
@pytest.mark.asyncio
async def test_lifecycle_privacy_projection_has_no_biometric_or_raw_audio_leakage(
    hass: HomeAssistant,
    setup_integration,
) -> None:
    _ = setup_integration

    captured_calls: list[dict[str, object]] = []
    _register_lookup_service(
        hass,
        responses=[
            {
                "identity_context": {
                    "state": "known",
                    "person_id": "person.tom",
                    "voice_profile_id": "vp_tom",
                    "confidence": 0.92,
                    "confidence_band": "high",
                    "reason_code": "attribution_ready",
                    "source": "voice_identity",
                },
                "runtime_attribution": {
                    "resolution_source": "conversation_id",
                    "freshness": "fresh",
                    "attribution_age_ms": 80,
                    "reason_code": "attribution_ready",
                },
            }
        ],
        captured_calls=captured_calls,
    )

    result = await hass.services.async_call(
        DOMAIN,
        "execute",
        {
            "target": "who am i",
            "intent_class": "general_qna",
            "context": {
                "conversation_id": "conv-426-privacy",
                "text": "who am i",
            },
        },
        blocking=True,
        return_response=True,
    )

    rendered = str(result["execution_envelope"]).lower()
    rendered += str(result["conversation_agent_ingress"]).lower()
    for forbidden in PRIVACY_ASSERTIONS:
        assert forbidden not in rendered


def test_governance_checklist_output_is_machine_and_human_readable() -> None:
    output = build_governance_checklist_output()
    payload = output.to_dict()

    assert payload == {
        "attribution_scenarios_passed": len(ATTRIBUTION_SCENARIOS),
        "freshness_scenarios_passed": len(FRESHNESS_SCENARIOS),
        "handoff_scenarios_passed": len(HANDOFF_SCENARIOS),
        "correlation_lookup_scenarios_passed": len(CORRELATION_SCENARIOS),
        "fallback_scenarios_passed": len(FALLBACK_SCENARIOS),
        "authorization_scenarios_passed": len(AUTHORIZATION_SCENARIOS),
        "privacy_scenarios_passed": len(PRIVACY_ASSERTIONS),
        "open_remediation_items": [],
    }

    markdown = render_governance_checklist_markdown(output)
    assert "runtime voice attribution lifecycle governance checklist" in markdown.lower()
    assert "attribution scenarios passed" in markdown.lower()
    assert "open remediation items: none" in markdown.lower()