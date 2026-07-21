"""Data update coordinator for Concierge."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from homeassistant.core import callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers.event import async_track_time_change
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .archive_runtime import (
    archive_options_from_entry,
    archive_trigger_age_days,
    cutoff_datetime,
    get_ha_purge_keep_days,
    parse_iso_datetime,
    resolve_archive_destination_path,
)
from .const import (
    CONF_NIGHT_MODE_ENABLED,
    CONF_UPDATE_INTERVAL_SECONDS,
    COORDINATOR_MAX_UPDATE_SECONDS,
    COORDINATOR_MIN_UPDATE_SECONDS,
    DEFAULT_NIGHT_MODE_ENABLED,
    DEFAULT_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    SIGNAL_READY,
)
from .models import ActivityEvent
from .services import _build_messaging_governance_boundary
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)

_ACTIVE_PERSON_STATE_AVAILABLE = "active_person_available"
_ACTIVE_PERSON_STATE_UNKNOWN = "active_person_unknown"
_ACTIVE_PERSON_STATE_AMBIGUOUS = "active_person_ambiguous"
_ACTIVE_PERSON_STATE_UNAVAILABLE = "active_person_unavailable"


def _latest_execution_envelope_ref(state) -> dict[str, Any] | None:
    """Return latest execution-envelope reference from activity history."""
    refs: list[dict[str, Any]] = []
    for activity in sorted(
        state.activities.values(),
        key=lambda item: str(getattr(item, "started_at", "")),
        reverse=True,
    ):
        for ref in list(getattr(activity, "external_refs", [])):
            if str(ref.get("ref_type", "") or "") == "execution_envelope":
                refs.append(dict(ref))
    return refs[0] if refs else None


def _coerce_confidence(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _resolve_active_person_resolution(latest_envelope: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve active household person state from consumed Voice Identity outcomes."""
    if latest_envelope is None:
        return {
            "resolution_enabled": True,
            "active_person_state": _ACTIVE_PERSON_STATE_UNAVAILABLE,
            "active_person_available": False,
            "resolved_person_id": None,
            "resolved_voice_profile_id": None,
            "attribution_available": False,
            "identity_context_available": False,
            "confidence_available": False,
            "confidence_accepted": False,
            "confidence": None,
            "confidence_band": None,
            "readiness_state": "unavailable",
            "reason_code": "no_execution_envelope",
            "resolution_posture": "fail_closed",
            "fail_closed": True,
            "authority_source": "voice_identity",
            "consumption_only": True,
        }

    attribution_consumed = bool(latest_envelope.get("voice_identity_attribution_consumed", False))
    attribution_state = str(latest_envelope.get("voice_identity_attribution_state", "") or "").strip().lower()
    attribution_reason = str(latest_envelope.get("voice_identity_attribution_reason_code", "") or "").strip().lower()
    person_id = str(latest_envelope.get("voice_identity_attribution_person_id", "") or "").strip() or None
    voice_profile_id = str(
        latest_envelope.get("voice_identity_attribution_voice_profile_id", "") or ""
    ).strip() or None
    confidence_consumed = bool(latest_envelope.get("voice_identity_confidence_consumed", False))
    confidence_value = _coerce_confidence(latest_envelope.get("voice_identity_confidence_value"))
    confidence_band = str(latest_envelope.get("voice_identity_confidence_band", "") or "").strip().lower() or None
    readiness_raw = str(latest_envelope.get("voice_identity_attribution_readiness", "") or "").strip().lower()
    readiness_state = readiness_raw or "unspecified"

    ambiguous_reason_codes = {"low_confidence", "ambiguous_match"}
    unavailable_reason_codes = {
        "voice_identity_not_loaded",
        "voice_identity_linkage_disabled",
        "attribution_service_unavailable",
        "identity_context_service_unavailable",
        "attribution_unavailable",
        "attribution_not_ready",
    }

    available = bool(attribution_consumed and person_id)
    ambiguous = bool(
        attribution_state == "low_confidence"
        or confidence_band in {"low", "ambiguous"}
        or attribution_reason in ambiguous_reason_codes
    )
    unavailable = bool(
        (readiness_raw and readiness_raw != "ready")
        or attribution_state == "unavailable"
        or attribution_reason in unavailable_reason_codes
    )

    if available:
        state = _ACTIVE_PERSON_STATE_AVAILABLE
        reason_code = attribution_reason or "attribution_ready"
    elif ambiguous:
        state = _ACTIVE_PERSON_STATE_AMBIGUOUS
        reason_code = attribution_reason or "low_confidence"
    elif unavailable:
        state = _ACTIVE_PERSON_STATE_UNAVAILABLE
        reason_code = attribution_reason or "attribution_unavailable"
    else:
        state = _ACTIVE_PERSON_STATE_UNKNOWN
        reason_code = attribution_reason or "identity_unknown"

    confidence_accepted = bool(
        available
        and confidence_consumed
        and confidence_band not in {"low", "ambiguous", "unknown", "unavailable", "no_match"}
    )

    return {
        "resolution_enabled": True,
        "active_person_state": state,
        "active_person_available": available,
        "resolved_person_id": person_id if available else None,
        "resolved_voice_profile_id": voice_profile_id if available else None,
        "attribution_available": attribution_consumed,
        "identity_context_available": attribution_state in {"known", "unknown", "low_confidence"},
        "confidence_available": confidence_consumed,
        "confidence_accepted": confidence_accepted,
        "confidence": confidence_value,
        "confidence_band": confidence_band,
        "readiness_state": readiness_state,
        "reason_code": reason_code,
        "resolution_posture": "resolved" if available else "fail_closed",
        "fail_closed": not available,
        "authority_source": "voice_identity",
        "consumption_only": True,
    }


class ConciergeCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinates runtime state for Concierge."""

    def __init__(self, hass, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.entry = entry
        self.hass = hass
        self._storage = ConciergeStorage(hass)
        self._nightly_archive_unsub = None
        self._archive_job_inflight = False

        configured_seconds = int(
            entry.options.get(
                CONF_UPDATE_INTERVAL_SECONDS,
                entry.data.get(CONF_UPDATE_INTERVAL_SECONDS, DEFAULT_UPDATE_INTERVAL_SECONDS),
            )
        )
        interval_seconds = max(COORDINATOR_MIN_UPDATE_SECONDS, min(COORDINATOR_MAX_UPDATE_SECONDS, configured_seconds))

        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_coordinator",
            update_interval=timedelta(seconds=interval_seconds),
        )

    def _activity_id(self, intent_class: str) -> str:
        """Create a unique coordinator activity identifier."""
        return f"{intent_class}_{int(datetime.now(timezone.utc).timestamp() * 1000)}_{uuid4().hex[:8]}"

    @staticmethod
    def _safe_outcome_reason(err: Exception) -> str:
        """Return compact activity outcome reason text."""
        text = str(err or "").strip()
        return text[:500]

    async def _async_with_coordinator_activity(
        self,
        *,
        intent_class: str,
        request_summary: str,
        action_name: str,
        runner,
        channel: str = "coordinator_runtime",
        actor_class: str = "concierge_coordinator",
        resolved_area_id: str | None = None,
        resolved_person_id: str | None = None,
        external_refs: list[dict[str, Any]] | None = None,
        policy_gates: list[str] | None = None,
    ) -> Any:
        """Execute coordinator work under strict backend activity lifecycle logging."""
        started_at = datetime.now(timezone.utc).isoformat()
        activity_id = self._activity_id(intent_class)

        await self._storage.async_record_activity_event(
            ActivityEvent(
                activity_id=activity_id,
                correlation_id=activity_id,
                started_at=started_at,
                channel=channel,
                actor_class=actor_class,
                intent_class=intent_class,
                request_summary=request_summary,
                resolved_person_id=resolved_person_id,
                resolved_area_id=resolved_area_id,
                confidence=1.0,
                external_refs=list(external_refs or []),
            )
        )

        try:
            run_payload = await runner()
        except Exception as err:
            await self._storage.async_close_activity_event(
                activity_id=activity_id,
                ended_at=datetime.now(timezone.utc).isoformat(),
                outcome="error",
                outcome_reason=self._safe_outcome_reason(err),
                actions_taken=[action_name],
                policy_gates=list(policy_gates or []),
            )
            raise

        result = run_payload
        activity_refs: list[dict[str, Any]] = []
        activity_summary = ""
        actions_taken = [action_name]
        if isinstance(run_payload, dict):
            result = run_payload.get("result", run_payload)
            refs = run_payload.get("external_refs", [])
            activity_refs = list(refs) if isinstance(refs, list) else []
            activity_summary = str(run_payload.get("request_summary", "")).strip()
            actions = run_payload.get("actions_taken", [action_name])
            actions_taken = list(actions) if isinstance(actions, list) else [action_name]

        if activity_refs or activity_summary:
            state = await self._storage.async_load_state()
            activity = state.activities.get(activity_id)
            if activity is not None:
                if activity_summary:
                    activity.request_summary = activity_summary
                if activity_refs:
                    activity.external_refs = list(activity.external_refs) + activity_refs
                await self._storage.async_record_activity_event(activity)

        await self._storage.async_close_activity_event(
            activity_id=activity_id,
            ended_at=datetime.now(timezone.utc).isoformat(),
            outcome="success",
            outcome_reason="",
            actions_taken=actions_taken,
            policy_gates=list(policy_gates or []),
        )
        return result

    @callback
    def async_start_background_jobs(self) -> None:
        """Start Concierge background jobs that should persist for entry lifetime."""
        if self._nightly_archive_unsub is not None:
            return

        # Run nightly before typical recorder purge windows.
        self._nightly_archive_unsub = async_track_time_change(
            self.hass,
            self._async_handle_nightly_archive,
            hour=2,
            minute=30,
            second=0,
        )

    @callback
    def async_stop_background_jobs(self) -> None:
        """Stop Concierge background jobs."""
        if self._nightly_archive_unsub is not None:
            self._nightly_archive_unsub()
            self._nightly_archive_unsub = None

    async def _async_handle_nightly_archive(self, now=None) -> None:
        """Archive aging activity entries nightly and purge stale archive files."""
        if self._archive_job_inflight:
            return

        self._archive_job_inflight = True
        try:
            async def _runner() -> dict[str, Any]:
                archive_options = archive_options_from_entry(self.entry)
                if not archive_options.get("archive_enabled"):
                    return {
                        "result": None,
                        "request_summary": "Coordinator nightly archive skipped: archive disabled",
                        "actions_taken": ["nightly_archive_skip_disabled"],
                        "external_refs": [
                            {"ref_type": "archive_job", "status": "skipped", "reason": "archive_disabled"}
                        ],
                    }

                destination_uri = str(archive_options.get("destination_uri", "") or "").strip()
                if not destination_uri:
                    return {
                        "result": None,
                        "request_summary": "Coordinator nightly archive skipped: destination missing",
                        "actions_taken": ["nightly_archive_skip_destination_missing"],
                        "external_refs": [
                            {"ref_type": "archive_job", "status": "skipped", "reason": "destination_missing"}
                        ],
                    }

                try:
                    destination_path = resolve_archive_destination_path(destination_uri)
                except Exception as err:
                    _LOGGER.warning("Concierge: invalid archive destination for nightly archive: %s", err)
                    return {
                        "result": None,
                        "request_summary": "Coordinator nightly archive skipped: destination invalid",
                        "actions_taken": ["nightly_archive_skip_invalid_destination"],
                        "external_refs": [
                            {
                                "ref_type": "archive_job",
                                "status": "skipped",
                                "reason": "invalid_destination",
                                "destination_uri": destination_uri,
                            }
                        ],
                    }

                ha_purge_keep_days = get_ha_purge_keep_days(self.hass)
                trigger_age_days = archive_trigger_age_days(ha_purge_keep_days)
                retention_days = int(archive_options.get("archive_retention_days", 30) or 30)

                state = await self._storage.async_load_state()
                activities = list(state.activities.values())

                result = await self.hass.async_add_executor_job(
                    self._run_archive_rotation,
                    destination_path,
                    activities,
                    trigger_age_days,
                    retention_days,
                )
                archived_count = int(result.get("archived_count", 0))
                pruned_count = int(result.get("pruned_count", 0))
                _LOGGER.debug(
                    "Concierge nightly archive complete: archived=%s pruned=%s trigger_age_days=%s retention_days=%s",
                    archived_count,
                    pruned_count,
                    trigger_age_days,
                    retention_days,
                )

                return {
                    "result": result,
                    "request_summary": (
                        "Coordinator nightly archive completed: "
                        f"archived={archived_count}, pruned={pruned_count}"
                    ),
                    "actions_taken": ["nightly_archive_rotate", "nightly_archive_prune"],
                    "external_refs": [
                        {
                            "ref_type": "archive_job",
                            "status": "completed",
                            "destination_uri": destination_uri,
                            "trigger_age_days": trigger_age_days,
                            "retention_days": retention_days,
                            "archived_count": archived_count,
                            "pruned_count": pruned_count,
                        }
                    ],
                }

            await self._async_with_coordinator_activity(
                intent_class="coordinator_nightly_archive",
                request_summary="Coordinator nightly archive job started",
                action_name="nightly_archive",
                channel="coordinator_job",
                runner=_runner,
            )
        except Exception:
            _LOGGER.exception("Concierge: nightly archive job failed")
        finally:
            self._archive_job_inflight = False

    def _run_archive_rotation(
        self,
        destination_path: Path,
        activities,
        trigger_age_days: int,
        retention_days: int,
    ) -> dict[str, int]:
        """Archive eligible activities and prune expired archive files."""
        archive_root = destination_path / "concierge_auto_archive"
        archive_root.mkdir(parents=True, exist_ok=True)

        state_path = archive_root / ".archive_state.json"
        last_cutoff = None
        if state_path.exists():
            try:
                previous = json.loads(state_path.read_text(encoding="utf-8"))
                last_cutoff = parse_iso_datetime(previous.get("last_cutoff_utc"))
            except Exception:
                last_cutoff = None

        cutoff = cutoff_datetime(trigger_age_days)
        rows: list[dict[str, Any]] = []
        for activity in activities:
            started_at = parse_iso_datetime(getattr(activity, "started_at", None))
            if started_at is None:
                continue
            if started_at > cutoff:
                continue
            if last_cutoff is not None and started_at <= last_cutoff:
                continue
            rows.append(
                {
                    "activity_id": getattr(activity, "activity_id", ""),
                    "correlation_id": getattr(activity, "correlation_id", ""),
                    "started_at": getattr(activity, "started_at", None),
                    "ended_at": getattr(activity, "ended_at", None),
                    "channel": getattr(activity, "channel", ""),
                    "actor_class": getattr(activity, "actor_class", ""),
                    "intent_class": getattr(activity, "intent_class", ""),
                    "request_summary": getattr(activity, "request_summary", ""),
                    "resolved_person_id": getattr(activity, "resolved_person_id", None),
                    "resolved_area_id": getattr(activity, "resolved_area_id", None),
                    "confidence": getattr(activity, "confidence", None),
                    "external_refs": list(getattr(activity, "external_refs", []) or []),
                    "outcome": getattr(activity, "outcome", None),
                    "outcome_reason": getattr(activity, "outcome_reason", ""),
                    "actions_taken": list(getattr(activity, "actions_taken", []) or []),
                    "policy_gates": list(getattr(activity, "policy_gates", []) or []),
                }
            )

        rows.sort(key=lambda item: str(item.get("started_at", "")))
        archived_count = 0
        if rows:
            archive_file = archive_root / f"activity_{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
            with archive_file.open("a", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=True) + "\n")
            archived_count = len(rows)

        state_payload = {
            "last_cutoff_utc": cutoff.isoformat(),
            "last_run_utc": datetime.now(timezone.utc).isoformat(),
            "trigger_age_days": int(trigger_age_days),
            "retention_days": int(retention_days),
        }
        state_path.write_text(json.dumps(state_payload, ensure_ascii=True, indent=2), encoding="utf-8")

        expiration = datetime.now(timezone.utc) - timedelta(days=max(1, int(retention_days)))
        pruned_count = 0
        for path in archive_root.glob("activity_*.jsonl"):
            try:
                modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
                if modified < expiration:
                    path.unlink(missing_ok=True)
                    pruned_count += 1
            except OSError:
                continue

        return {
            "archived_count": archived_count,
            "pruned_count": pruned_count,
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch runtime data.

        Concierge currently provides orchestration health and effective options state.
        """
        night_mode_enabled = bool(
            self.entry.options.get(
                CONF_NIGHT_MODE_ENABLED,
                self.entry.data.get(CONF_NIGHT_MODE_ENABLED, DEFAULT_NIGHT_MODE_ENABLED),
            )
        )

        state = await self._storage.async_load_state()
        latest_execution_ref = _latest_execution_envelope_ref(state)
        active_person_resolution = _resolve_active_person_resolution(latest_execution_ref)
        foundation_area_ids = {area.id for area in ar.async_get(self.hass).async_list_areas()}
        configured_room_outside_foundation_count = sum(
            1 for area_id in state.rooms if area_id not in foundation_area_ids
        )
        composites_with_missing_area_count = sum(
            1
            for composite in state.composites.values()
            if any(area_id not in foundation_area_ids for area_id in composite.area_ids)
        )
        services_by_domain = self.hass.services.async_services()
        integration_capabilities = {
            domain: sorted(domain_services.keys())
            for domain, domain_services in services_by_domain.items()
            if domain not in {DOMAIN, "homeassistant", "persistent_notification"}
        }

        foundation_summary = {
            "room_identity_source": "home_assistant_area_registry",
            "concierge_role": "bounded_consumer_orchestrator",
            "capability_projection_boundary": {
                "projection_role": "governed_projection_consumer",
                "projection_is_authority": False,
                "deferred_release_2_owners": {
                    "authoritative_input_consumption": "#314",
                    "vocabulary_to_capability_handoff": "#315",
                    "asset_intelligence_cp00_handoff": "#316",
                    "capability_discovery": "#317",
                    "capability_diagnostics_explainability": "#318",
                },
            },
            "continuity_governance_boundary": {
                "continuity_role": "governed_continuity_consumer",
                "continuity_is_authority": False,
                "privacy_boundary_preserved": True,
                "continuity_diagnostics_explainability_enabled": True,
                "deferred_release_3_owners": {
                    "person_room_affinity_boundary": "#326",
                    "privacy_household_memory_boundary": "#327",
                    "continuity_affinity_diagnostics_explainability": "#328",
                    "restoration_governance_boundary": "#329",
                    "release_3_validation": "#338",
                },
            },
            "person_room_affinity_boundary": {
                "affinity_role": "governed_person_room_affinity_consumer",
                "affinity_is_authority": False,
                "guest_safe_boundary_preserved": True,
                "privacy_boundary_preserved": True,
                "affinity_diagnostics_explainability_enabled": True,
                "deferred_release_3_owners": {
                    "privacy_household_memory_boundary": "#327",
                    "continuity_affinity_diagnostics_explainability": "#328",
                    "restoration_governance_boundary": "#329",
                    "release_3_validation": "#338",
                },
            },
            "privacy_household_memory_boundary": {
                "privacy_memory_role": "governed_privacy_household_memory_consumer",
                "privacy_memory_is_authority": False,
                "guest_safe_boundary_preserved": True,
                "deferred_release_3_owners": {
                    "continuity_affinity_diagnostics_explainability": "#328",
                    "restoration_governance_boundary": "#329",
                    "release_3_validation": "#338",
                },
            },
            "messaging_governance_boundary": _build_messaging_governance_boundary(
                route_scope="global",
                context_area_id=None,
                resolved_composite_id=None,
                recipient_scope="household",
                message_context_type="foundation",
            ),
            "occupancy_governance_boundary": {
                "occupancy_role": "governed_occupancy_boundary_consumer",
                "occupancy_is_authority": False,
                "occupancy_authority_external": True,
                "occupancy_policy_authority_external": True,
                "occupancy_truth_authority_external": True,
                "guest_safe_boundary_preserved": True,
                "privacy_boundary_preserved": True,
                "occupancy_decision_behavior_enabled": False,
                "occupancy_execution_enabled": False,
                "occupancy_inference_enabled": False,
                "occupancy_diagnostics_behavior_enabled": False,
                "deferred_release_3_owners": {
                    "presence_governance_boundary": "#334",
                    "guest_unknown_occupant_behavior": "#335",
                    "multi_occupant_behavior": "#336",
                    "occupancy_presence_diagnostics_explainability": "#337",
                    "release_3_validation": "#338",
                },
            },
            "presence_governance_boundary": {
                "presence_role": "governed_presence_boundary_consumer",
                "presence_is_authority": False,
                "presence_authority_external": True,
                "presence_policy_authority_external": True,
                "presence_truth_authority_external": True,
                "guest_safe_boundary_preserved": True,
                "privacy_boundary_preserved": True,
                "presence_detection_enabled": False,
                "presence_inference_enabled": False,
                "presence_attribution_enabled": True,
                "presence_behavior_enabled": False,
                "presence_diagnostics_behavior_enabled": False,
                "deferred_release_3_owners": {
                    "guest_unknown_occupant_behavior": "#335",
                    "multi_occupant_behavior": "#336",
                    "occupancy_presence_diagnostics_explainability": "#337",
                    "release_3_validation": "#338",
                },
            },
            "guest_unknown_occupant_behavior": {
                "guest_unknown_behavior_role": "governed_guest_unknown_occupant_behavior_consumer",
                "guest_unknown_behavior_is_authority": False,
                "consumes_occupancy_governance_boundary": True,
                "consumes_presence_governance_boundary": True,
                "occupancy_authority_external": True,
                "presence_authority_external": True,
                "identity_authority_external": True,
                "household_memory_authority_external": True,
                "guest_safe_boundary_preserved": True,
                "privacy_boundary_preserved": True,
                "identity_attribution_enabled": True,
                "occupancy_truth_modification_enabled": False,
                "presence_truth_modification_enabled": False,
                "behavior_enabled": True,
                "deferred_release_3_owners": {
                    "multi_occupant_behavior": "#336",
                    "occupancy_presence_diagnostics_explainability": "#337",
                    "release_3_validation": "#338",
                },
            },
            "multi_occupant_behavior": {
                "multi_occupant_behavior_role": "governed_multi_occupant_behavior_consumer",
                "multi_occupant_behavior_is_authority": False,
                "consumes_occupancy_governance_boundary": True,
                "consumes_presence_governance_boundary": True,
                "consumes_guest_unknown_behavior": True,
                "occupancy_authority_external": True,
                "presence_authority_external": True,
                "identity_authority_external": True,
                "household_memory_authority_external": True,
                "guest_safe_boundary_preserved": True,
                "privacy_boundary_preserved": True,
                "identity_attribution_enabled": True,
                "occupancy_truth_modification_enabled": False,
                "presence_truth_modification_enabled": False,
                "conflict_visibility_enabled": True,
                "behavior_enabled": True,
                "deferred_release_3_owners": {
                    "occupancy_presence_diagnostics_explainability": "#337",
                    "release_3_validation": "#338",
                },
            },
            "restoration_governance_boundary": {
                "restoration_role": "governed_restoration_boundary_consumer",
                "restoration_is_authority": False,
                "restoration_authority_external": True,
                "restoration_policy_authority_external": True,
                "restoration_execution_enabled": True,
                "restoration_decision_behavior_enabled": True,
                "e3a_preservation_alignment_enabled": True,
                "restoration_diagnostics_behavior_enabled": True,
                "deferred_release_3_owners": {
                    "restoration_outcome_implementation": "#330",
                    "e3a_preservation_alignment": "#331",
                    "restoration_diagnostics_explainability": "#332",
                    "release_3_validation": "#338",
                },
            },
            "foundation_area_count": len(foundation_area_ids),
            "room_count": len(state.rooms),
            "composite_count": len(state.composites),
            "interaction_count": len(state.interactions),
            "signal_count": len(state.signals),
            "context_source_count": len(state.contexts),
            "person_profile_count": len(state.person_profiles),
            "voice_profile_count": len(state.voice_profiles),
            "configured_room_outside_foundation_count": configured_room_outside_foundation_count,
            "composites_with_missing_area_count": composites_with_missing_area_count,
            "active_person_resolution_enabled": True,
            "active_person_state": active_person_resolution["active_person_state"],
            "active_person_reason_code": active_person_resolution["reason_code"],
            "active_person_available": active_person_resolution["active_person_available"],
        }
        room_configs = {
            area_id: {
                "posture": room.posture,
                "media_player_entity_ids": room.media_player_entity_ids,
                "voice_device_entity_ids": room.voice_device_entity_ids,
                "tts_voice": room.tts_voice,
            }
            for area_id, room in state.rooms.items()
        }

        return {
            "status": SIGNAL_READY,
            "night_mode_enabled": night_mode_enabled,
            "entry_title": self.entry.title,
            "foundation_summary": foundation_summary,
            "capability_domains": sorted(integration_capabilities.keys()),
            "room_configs": room_configs,
            "person_profiles": {
                person_id: {
                    "name": person.name,
                    "linked_area_id": person.linked_area_id,
                    "ble_device_ids": person.ble_device_ids,
                    "aqara_presence_entity_ids": person.aqara_presence_entity_ids,
                    "voice_profile_id": person.voice_profile_id,
                }
                for person_id, person in state.person_profiles.items()
            },
            "voice_profiles": {
                voice_profile_id: {
                    "name": profile.name,
                    "tts_voice": profile.tts_voice,
                    "enrollment_state": profile.enrollment_state,
                    "sample_count": profile.sample_count,
                }
                for voice_profile_id, profile in state.voice_profiles.items()
            },
            "active_person_resolution": active_person_resolution,
        }
