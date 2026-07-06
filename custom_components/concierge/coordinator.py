"""Data update coordinator for Concierge."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

from homeassistant.core import callback
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
from .storage import ConciergeStorage

_LOGGER = logging.getLogger(__name__)


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
        services_by_domain = self.hass.services.async_services()
        integration_capabilities = {
            domain: sorted(domain_services.keys())
            for domain, domain_services in services_by_domain.items()
            if domain not in {DOMAIN, "homeassistant", "persistent_notification"}
        }

        foundation_summary = {
            "room_count": len(state.rooms),
            "interaction_count": len(state.interactions),
            "signal_count": len(state.signals),
            "context_source_count": len(state.contexts),
            "person_profile_count": len(state.person_profiles),
            "voice_profile_count": len(state.voice_profiles),
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
        }
