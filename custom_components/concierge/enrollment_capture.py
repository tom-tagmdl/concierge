"""Capture provider abstraction for enrollment sample acquisition."""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
import inspect
import logging
from types import SimpleNamespace
from typing import Awaitable
from typing import Callable
from typing import Protocol

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED
from .const import VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE
from .enrollment_storage import MountedPathEnrollmentStorageProvider

CAPTURE_PROVIDER_PREFERENCE_AUTO = "auto"
CAPTURE_PROVIDER_PREFERENCE_BROWSER = "browser"
CAPTURE_PROVIDER_PREFERENCE_SATELLITE = "satellite"

CAPTURE_PROVIDER_TYPE_BROWSER_MICROPHONE = "browser_microphone"
CAPTURE_PROVIDER_TYPE_SATELLITE = "satellite"

CAPTURE_PROVIDER_STATUS_READY = "ready"
CAPTURE_PROVIDER_STATUS_UNAVAILABLE = "unavailable"
CAPTURE_PROVIDER_STATUS_UNSUPPORTED = "unsupported"
CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED = "not_configured"
CAPTURE_PROVIDER_STATUS_FUTURE_PROVIDER = "future_provider"
CAPTURE_PROVIDER_STATUS_CAPABILITY_UNKNOWN = "capability_unknown"
CAPTURE_PROVIDER_STATUS_NO_CAPTURE_API = "no_capture_api"
CAPTURE_PROVIDER_STATUS_PROVIDER_NOT_SELECTED = "provider_not_selected"

CAPTURE_PROVIDER_REASON_READY = "ready"
CAPTURE_PROVIDER_REASON_STORAGE_NOT_CONFIGURED = "storage_not_configured"
CAPTURE_PROVIDER_REASON_STORAGE_UNAVAILABLE = "storage_unavailable"
CAPTURE_PROVIDER_REASON_SATELLITE_PROVIDER_NOT_CONFIGURED = "satellite_provider_not_configured"
CAPTURE_PROVIDER_REASON_SATELLITE_CAPTURE_NOT_SUPPORTED = "satellite_capture_not_supported"
CAPTURE_PROVIDER_REASON_SATELLITE_FUTURE_PROVIDER = "satellite_future_provider"
CAPTURE_PROVIDER_REASON_PROVIDER_NOT_SELECTED = "provider_not_selected"
CAPTURE_PROVIDER_REASON_CAPABILITY_UNKNOWN = "capability_unknown"

SATELLITE_CAPTURE_POC_EXPECTED_RATE = 16000
SATELLITE_CAPTURE_POC_EXPECTED_WIDTH = 2
SATELLITE_CAPTURE_POC_EXPECTED_CHANNELS = 1
SATELLITE_CAPTURE_POC_MAX_TIMEOUT_SECONDS = 60.0

SATELLITE_CAPTURE_POC_FAILURE_ENTITY_NOT_FOUND = "satellite_entity_not_found"
SATELLITE_CAPTURE_POC_FAILURE_DEVICE_NOT_FOUND = "satellite_device_not_found"
SATELLITE_CAPTURE_POC_FAILURE_COMMAND_UNAVAILABLE = "capture_command_unavailable"
SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED = "capture_command_failed"
SATELLITE_CAPTURE_POC_FAILURE_AUDIO_DECODE_FAILED = "capture_audio_decode_failed"
SATELLITE_CAPTURE_POC_FAILURE_TIMEOUT_INVALID = "capture_timeout_invalid"
SATELLITE_CAPTURE_POC_FAILURE_NO_CHUNKS = "capture_no_chunks"
SATELLITE_CAPTURE_POC_FAILURE_PROMPT_FAILED = "satellite_prompt_failed"

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class CaptureProviderCapability:
    """Sanitized provider capability response."""

    provider_key: str
    provider_type: str
    available: bool
    supported: bool
    status: str
    user_safe_status_summary: str
    capture_supported: bool
    selection_supported: bool
    reason_code: str
    is_default: bool = False

    def as_public_dict(self) -> dict[str, object]:
        """Return privacy-safe projection suitable for diagnostics and APIs."""
        return {
            "provider_key": self.provider_key,
            "provider_type": self.provider_type,
            "provider_available": bool(self.available),
            "provider_supported": bool(self.supported),
            "provider_status": self.status,
            "provider_status_summary": self.user_safe_status_summary,
            "capture_supported": bool(self.capture_supported),
            "selection_supported": bool(self.selection_supported),
            "reason_code": self.reason_code,
            "provider_is_default": bool(self.is_default),
        }


@dataclass(slots=True)
class CaptureSampleRequest:
    """Provider handoff request for one enrollment sample capture."""

    person_id: str
    voice_profile_id: str
    phrase_index: int
    audio_content_type: str
    audio_bytes: bytes


@dataclass(slots=True)
class CaptureSampleResult:
    """Provider handoff result for one captured enrollment sample."""

    saved: bool
    recording_path: str
    recording_mime_type: str
    recording_size_bytes: int
    phrase_index: int

    def as_payload(self) -> dict[str, object]:
        return {
            "saved": bool(self.saved),
            "recording_path": self.recording_path,
            "recording_mime_type": self.recording_mime_type,
            "recording_size_bytes": int(self.recording_size_bytes),
            "phrase_index": int(self.phrase_index),
        }


class EnrollmentCaptureProvider(Protocol):
    """Capture provider boundary contract for enrollment sample acquisition."""

    provider_key: str
    provider_type: str

    async def get_capability(self) -> CaptureProviderCapability:
        """Return one provider capability result."""

    async def capture_sample(self, request: CaptureSampleRequest) -> CaptureSampleResult:
        """Capture and persist one sample through provider-specific handoff."""


class BrowserMicCaptureProvider:
    """Production capture provider using browser microphone handoff."""

    provider_key = CAPTURE_PROVIDER_PREFERENCE_BROWSER
    provider_type = CAPTURE_PROVIDER_TYPE_BROWSER_MICROPHONE

    def __init__(
        self,
        hass: HomeAssistant,
        require_storage_preflight: Callable[[bool], Awaitable[MountedPathEnrollmentStorageProvider]],
    ) -> None:
        self._hass = hass
        self._require_storage_preflight = require_storage_preflight

    @staticmethod
    def _status_and_reason_from_storage_failure(message: str) -> tuple[str, str]:
        lowered = str(message or "").lower()
        if VOICE_ENROLLMENT_PREFLIGHT_STORAGE_NOT_CONFIGURED in lowered:
            return CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED, CAPTURE_PROVIDER_REASON_STORAGE_NOT_CONFIGURED
        if VOICE_ENROLLMENT_PREFLIGHT_STORAGE_UNKNOWN_FAILURE in lowered:
            return CAPTURE_PROVIDER_STATUS_CAPABILITY_UNKNOWN, CAPTURE_PROVIDER_REASON_CAPABILITY_UNKNOWN
        return CAPTURE_PROVIDER_STATUS_UNAVAILABLE, CAPTURE_PROVIDER_REASON_STORAGE_UNAVAILABLE

    async def get_capability(self) -> CaptureProviderCapability:
        try:
            await self._require_storage_preflight(False)
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=True,
                supported=True,
                status=CAPTURE_PROVIDER_STATUS_READY,
                user_safe_status_summary="Browser microphone capture is available.",
                capture_supported=True,
                selection_supported=True,
                reason_code=CAPTURE_PROVIDER_REASON_READY,
                is_default=True,
            )
        except vol.Invalid as err:
            status, reason_code = self._status_and_reason_from_storage_failure(str(err))
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=False,
                supported=True,
                status=status,
                user_safe_status_summary="Browser microphone capture is currently unavailable.",
                capture_supported=True,
                selection_supported=True,
                reason_code=reason_code,
                is_default=True,
            )

    async def capture_sample(self, request: CaptureSampleRequest) -> CaptureSampleResult:
        provider = await self._require_storage_preflight(True)
        session_id = f"{request.person_id}__{request.voice_profile_id}"

        write_result = await self._hass.async_add_executor_job(
            lambda: provider.write_sample(
                session_id=session_id,
                sample_index=int(request.phrase_index),
                content_type=request.audio_content_type,
                data_bytes=request.audio_bytes,
            )
        )
        return CaptureSampleResult(
            saved=True,
            recording_path=write_result.sample_path,
            recording_mime_type=request.audio_content_type,
            recording_size_bytes=len(request.audio_bytes),
            phrase_index=int(request.phrase_index),
        )


class SatelliteCaptureProvider:
    """Satellite enrollment capture provider using supported Home Assistant APIs."""

    provider_key = CAPTURE_PROVIDER_PREFERENCE_SATELLITE
    provider_type = CAPTURE_PROVIDER_TYPE_SATELLITE

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        capture_api_supported: bool = False,
        provider_selected: bool = True,
    ) -> None:
        self._hass = hass
        self._capture_api_supported = bool(capture_api_supported)
        self._provider_selected = bool(provider_selected)

    def _discover_satellite_entities(self) -> list[dict[str, str]]:
        registry = er.async_get(self._hass)
        entities: list[dict[str, str]] = []
        for entry in registry.entities.values():
            if entry.domain != "assist_satellite":
                continue
            if entry.disabled_by:
                continue
            entities.append(
                {
                    "entity_id": str(entry.entity_id),
                    "device_id": str(entry.device_id or ""),
                    "platform": str(entry.platform or ""),
                }
            )
        return entities

    def _capture_command_available(self) -> bool:
        try:
            from homeassistant.components.assist_pipeline import websocket_api as assist_pipeline_ws
        except Exception:
            return False
        command_handler = getattr(assist_pipeline_ws, "websocket_device_capture", None)
        if command_handler is None:
            return False
        return inspect.iscoroutinefunction(inspect.unwrap(command_handler))

    async def _prompt_satellite_start_conversation(
        self,
        *,
        satellite_entity_id: str,
        prompt_text: str,
        preannounce: bool,
    ) -> tuple[bool, str | None, str | None]:
        try:
            prompt_response = await self._hass.services.async_call(
                "assist_satellite",
                "ask_question",
                {
                    "entity_id": str(satellite_entity_id),
                    "question": str(prompt_text),
                    "preannounce": bool(preannounce),
                },
                blocking=True,
                return_response=True,
            )
        except Exception as err:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_PROMPT_FAILED,
                f"failed to ask satellite enrollment question: {err}",
            )
            return False, failure_code, safe_message

        if prompt_response is None:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_PROMPT_FAILED,
                "satellite enrollment question did not return a response",
            )
            return False, failure_code, safe_message

        return True, None, None

    def _select_satellite(
        self,
        *,
        satellite_entity_id: str | None,
        device_id: str | None,
    ) -> tuple[dict[str, object], dict[str, str] | None]:
        result: dict[str, object] = {
            "provider_type": self.provider_type,
            "satellite_entity_available": False,
            "capture_command_available": False,
            "capture_started": False,
            "chunks_received": 0,
            "bytes_received": 0,
            "audio_rate": None,
            "audio_width": None,
            "audio_channels": None,
            "failure_code": None,
            "failure_message_safe": None,
        }

        entities = self._discover_satellite_entities()
        result["satellite_entity_available"] = bool(entities)
        if not entities:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_ENTITY_NOT_FOUND,
                "no assist satellite entity is available",
            )
            result["failure_code"] = failure_code
            result["failure_message_safe"] = safe_message
            return result, None

        requested_device_id = str(device_id or "").strip()
        requested_entity_id = str(satellite_entity_id or "").strip()

        selected: dict[str, str] | None = None
        if requested_entity_id:
            for entity in entities:
                if entity["entity_id"] == requested_entity_id:
                    selected = entity
                    break
            if selected is None:
                failure_code, safe_message = self._sanitize_failure(
                    SATELLITE_CAPTURE_POC_FAILURE_ENTITY_NOT_FOUND,
                    "requested assist satellite entity is not available",
                )
                result["failure_code"] = failure_code
                result["failure_message_safe"] = safe_message
                return result, None
        elif requested_device_id:
            for entity in entities:
                if entity["device_id"] == requested_device_id:
                    selected = entity
                    break
            if selected is None:
                failure_code, safe_message = self._sanitize_failure(
                    SATELLITE_CAPTURE_POC_FAILURE_DEVICE_NOT_FOUND,
                    "requested assist satellite device is not available",
                )
                result["failure_code"] = failure_code
                result["failure_message_safe"] = safe_message
                return result, None
        else:
            selected = entities[0]

        selected_device_id = str(selected.get("device_id") or "").strip() if selected else ""
        if not selected_device_id:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_DEVICE_NOT_FOUND,
                "selected assist satellite does not expose a device id",
            )
            result["failure_code"] = failure_code
            result["failure_message_safe"] = safe_message
            return result, None

        return result, selected

    @staticmethod
    def _sanitize_failure(failure_code: str, message: str) -> tuple[str, str]:
        safe_message = str(message or "satellite capture command is unavailable").strip()
        if not safe_message:
            safe_message = "satellite capture command is unavailable"
        return str(failure_code or SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED), safe_message[:240]

    async def _invoke_assist_pipeline_device_capture(
        self,
        *,
        device_id: str,
        timeout_seconds: float,
        capture_ready: asyncio.Event | None = None,
    ) -> tuple[bool, dict[str, object]]:
        try:
            from homeassistant.components.assist_pipeline import websocket_api as assist_pipeline_ws
        except Exception as err:  # pragma: no cover - import failure guarded in tests
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_COMMAND_UNAVAILABLE,
                f"assist pipeline websocket API unavailable: {err}",
            )
            return False, {
                "capture_command_available": False,
                "capture_started": False,
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": failure_code,
                "failure_message_safe": safe_message,
                "audio_bytes": b"",
            }

        command_handler = getattr(assist_pipeline_ws, "websocket_device_capture", None)
        if command_handler is None:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_COMMAND_UNAVAILABLE,
                "assist_pipeline/device/capture is not available",
            )
            return False, {
                "capture_command_available": False,
                "capture_started": False,
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": failure_code,
                "failure_message_safe": safe_message,
                "audio_bytes": b"",
            }

        capture_coroutine = inspect.unwrap(command_handler)
        if not inspect.iscoroutinefunction(capture_coroutine):
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_COMMAND_UNAVAILABLE,
                "assist_pipeline/device/capture handler is not callable",
            )
            return False, {
                "capture_command_available": False,
                "capture_started": False,
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": failure_code,
                "failure_message_safe": safe_message,
                "audio_bytes": b"",
            }

        class _POCConnection:
            def __init__(self, ready_event: asyncio.Event | None) -> None:
                self.subscriptions: dict[object, Callable[[], object]] = {}
                self.user = SimpleNamespace(is_admin=True, id="concierge-satellite-poc")
                self.capture_started = False
                self.error_code: str | None = None
                self.error_message: str | None = None
                self.audio_events: list[dict[str, object]] = []
                self._ready_event = ready_event

            def send_result(self, msg_id: int, result: object | None = None) -> None:
                del msg_id, result
                self.capture_started = True
                if self._ready_event is not None:
                    self._ready_event.set()

            def send_event(self, msg_id: int, event: object | None = None) -> None:
                del msg_id
                if isinstance(event, dict):
                    self.audio_events.append(event)

            def send_error(self, msg_id: int, code: str, message: str) -> None:
                del msg_id
                self.error_code = str(code)
                self.error_message = str(message)
                if self._ready_event is not None:
                    self._ready_event.set()

            def async_handle_exception(self, msg: dict[str, object], err: Exception) -> None:
                del msg
                self.error_code = SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED
                self.error_message = str(err)
                if self._ready_event is not None:
                    self._ready_event.set()

        connection = _POCConnection(capture_ready)
        message = {
            "id": 1,
            "type": "assist_pipeline/device/capture",
            "device_id": str(device_id),
            "timeout": float(timeout_seconds),
        }

        try:
            await capture_coroutine(self._hass, connection, message)
        except Exception as err:  # pragma: no cover - guarded by async_handle_exception path
            _LOGGER.debug("satellite capture command invocation failed", exc_info=err)
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED,
                f"assist_pipeline/device/capture invocation failed: {err}",
            )
            return False, {
                "capture_command_available": True,
                "capture_started": bool(connection.capture_started),
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": failure_code,
                "failure_message_safe": safe_message,
                "audio_bytes": b"",
            }
        finally:
            unsub = connection.subscriptions.get(1)
            if callable(unsub):
                try:
                    unsub()
                except Exception:  # pragma: no cover - defensive cleanup only
                    _LOGGER.debug("satellite capture websocket subscription cleanup failed", exc_info=True)

        if connection.error_code:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_COMMAND_FAILED,
                connection.error_message or "assist_pipeline/device/capture failed",
            )
            return False, {
                "capture_command_available": True,
                "capture_started": bool(connection.capture_started),
                "chunks_received": 0,
                "bytes_received": 0,
                "audio_rate": None,
                "audio_width": None,
                "audio_channels": None,
                "failure_code": failure_code,
                "failure_message_safe": safe_message,
                "audio_bytes": b"",
            }

        chunks: list[bytes] = []
        audio_rate: int | None = None
        audio_width: int | None = None
        audio_channels: int | None = None

        for event in connection.audio_events:
            event_type = str(event.get("type", "") or "")
            if event_type != "audio":
                continue

            chunk_b64 = str(event.get("audio", "") or "")
            if not chunk_b64:
                continue

            try:
                chunk = base64.b64decode(chunk_b64, validate=True)
            except Exception as err:
                failure_code, safe_message = self._sanitize_failure(
                    SATELLITE_CAPTURE_POC_FAILURE_AUDIO_DECODE_FAILED,
                    f"failed to decode satellite audio chunk: {err}",
                )
                return False, {
                    "capture_command_available": True,
                    "capture_started": bool(connection.capture_started),
                    "chunks_received": len(chunks),
                    "bytes_received": sum(len(item) for item in chunks),
                    "audio_rate": audio_rate,
                    "audio_width": audio_width,
                    "audio_channels": audio_channels,
                    "failure_code": failure_code,
                    "failure_message_safe": safe_message,
                    "audio_bytes": b"",
                }

            if audio_rate is None:
                audio_rate = int(event.get("rate") or 0)
            if audio_width is None:
                audio_width = int(event.get("width") or 0)
            if audio_channels is None:
                audio_channels = int(event.get("channels") or 0)
            chunks.append(chunk)

        combined_audio = b"".join(chunks)
        return True, {
            "capture_command_available": True,
            "capture_started": bool(connection.capture_started),
            "chunks_received": len(chunks),
            "bytes_received": len(combined_audio),
            "audio_rate": audio_rate,
            "audio_width": audio_width,
            "audio_channels": audio_channels,
            "failure_code": None,
            "failure_message_safe": None,
            "audio_bytes": combined_audio,
        }

    async def run_satellite_capture_poc(
        self,
        *,
        timeout_seconds: float,
        satellite_entity_id: str | None = None,
        device_id: str | None = None,
        prompt_before_capture: bool = False,
        prompt_text: str = "Please say your enrollment phrase now.",
        preannounce: bool = False,
    ) -> tuple[dict[str, object], bytes | None, str | None]:
        result, selected = self._select_satellite(
            satellite_entity_id=satellite_entity_id,
            device_id=device_id,
        )
        if selected is None:
            return result, None, None

        bounded_timeout = float(timeout_seconds)
        if bounded_timeout <= 0 or bounded_timeout > SATELLITE_CAPTURE_POC_MAX_TIMEOUT_SECONDS:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_TIMEOUT_INVALID,
                "satellite capture timeout must be between 0 and 60 seconds",
            )
            result["failure_code"] = failure_code
            result["failure_message_safe"] = safe_message
            return result, None, None

        if prompt_before_capture:
            capture_ready = asyncio.Event()
            capture_task = asyncio.create_task(
                self._invoke_assist_pipeline_device_capture(
                    device_id=str(selected["device_id"]),
                    timeout_seconds=bounded_timeout,
                    capture_ready=capture_ready,
                )
            )
            try:
                await capture_ready.wait()
                if capture_task.done():
                    success, capture_payload = await capture_task
                else:
                    prompt_ok, failure_code, failure_message = await self._prompt_satellite_start_conversation(
                        satellite_entity_id=selected["entity_id"],
                        prompt_text=prompt_text,
                        preannounce=preannounce,
                    )
                    if not prompt_ok:
                        capture_task.cancel()
                        try:
                            await capture_task
                        except asyncio.CancelledError:
                            pass
                        result["failure_code"] = failure_code
                        result["failure_message_safe"] = failure_message
                        return result, None, None
                    success, capture_payload = await capture_task
            except Exception:
                if not capture_task.done():
                    capture_task.cancel()
                    try:
                        await capture_task
                    except asyncio.CancelledError:
                        pass
                raise
        else:
            success, capture_payload = await self._invoke_assist_pipeline_device_capture(
                device_id=str(selected["device_id"]),
                timeout_seconds=bounded_timeout,
            )
        result.update(
            {
                "capture_command_available": bool(capture_payload.get("capture_command_available", False)),
                "capture_started": bool(capture_payload.get("capture_started", False)),
                "chunks_received": int(capture_payload.get("chunks_received", 0) or 0),
                "bytes_received": int(capture_payload.get("bytes_received", 0) or 0),
                "audio_rate": capture_payload.get("audio_rate"),
                "audio_width": capture_payload.get("audio_width"),
                "audio_channels": capture_payload.get("audio_channels"),
                "failure_code": capture_payload.get("failure_code"),
                "failure_message_safe": capture_payload.get("failure_message_safe"),
            }
        )
        if not success:
            return result, None, None

        audio_bytes = capture_payload.get("audio_bytes")
        if not isinstance(audio_bytes, (bytes, bytearray)) or not audio_bytes:
            failure_code, safe_message = self._sanitize_failure(
                SATELLITE_CAPTURE_POC_FAILURE_NO_CHUNKS,
                "no satellite audio chunks were received during capture window",
            )
            result["failure_code"] = failure_code
            result["failure_message_safe"] = safe_message
            return result, b"", "audio/L16; rate=16000; channels=1"

        return result, bytes(audio_bytes), "audio/L16; rate=16000; channels=1"

    async def capture_satellite_audio(
        self,
        *,
        timeout_seconds: float,
        satellite_entity_id: str | None = None,
        device_id: str | None = None,
        prompt_text: str,
        preannounce: bool,
    ) -> tuple[dict[str, object], bytes | None, str | None]:
        """Capture one satellite audio sample for production enrollment transport."""
        return await self.run_satellite_capture_poc(
            timeout_seconds=timeout_seconds,
            satellite_entity_id=satellite_entity_id,
            device_id=device_id,
            prompt_before_capture=True,
            prompt_text=prompt_text,
            preannounce=preannounce,
        )

    def _has_configured_satellite_entities(self) -> bool:
        registry = er.async_get(self._hass)
        for entity in registry.entities.values():
            if entity.domain == "assist_satellite" and not entity.disabled_by:
                return True
        return False

    async def get_capability(self) -> CaptureProviderCapability:
        if not self._provider_selected:
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=False,
                supported=False,
                status=CAPTURE_PROVIDER_STATUS_PROVIDER_NOT_SELECTED,
                user_safe_status_summary="Satellite enrollment is not selected.",
                capture_supported=False,
                selection_supported=True,
                reason_code=CAPTURE_PROVIDER_REASON_PROVIDER_NOT_SELECTED,
                is_default=False,
            )

        has_satellite_entities = self._has_configured_satellite_entities()
        if not has_satellite_entities:
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=False,
                supported=False,
                status=CAPTURE_PROVIDER_STATUS_NOT_CONFIGURED,
                user_safe_status_summary="Satellite enrollment is not configured.",
                capture_supported=False,
                selection_supported=True,
                reason_code=CAPTURE_PROVIDER_REASON_SATELLITE_PROVIDER_NOT_CONFIGURED,
                is_default=False,
            )

        if not self._capture_api_supported:
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=False,
                supported=False,
                status=CAPTURE_PROVIDER_STATUS_NO_CAPTURE_API,
                user_safe_status_summary="Satellite enrollment capture API is not currently supported.",
                capture_supported=False,
                selection_supported=True,
                reason_code=CAPTURE_PROVIDER_REASON_SATELLITE_CAPTURE_NOT_SUPPORTED,
                is_default=False,
            )

        if not self._capture_command_available():
            return CaptureProviderCapability(
                provider_key=self.provider_key,
                provider_type=self.provider_type,
                available=False,
                supported=False,
                status=CAPTURE_PROVIDER_STATUS_NO_CAPTURE_API,
                user_safe_status_summary="Satellite enrollment capture API is not currently supported.",
                capture_supported=False,
                selection_supported=True,
                reason_code=CAPTURE_PROVIDER_REASON_SATELLITE_CAPTURE_NOT_SUPPORTED,
                is_default=False,
            )

        return CaptureProviderCapability(
            provider_key=self.provider_key,
            provider_type=self.provider_type,
            available=True,
            supported=True,
            status=CAPTURE_PROVIDER_STATUS_READY,
            user_safe_status_summary="Satellite enrollment capture is available.",
            capture_supported=True,
            selection_supported=True,
            reason_code=CAPTURE_PROVIDER_REASON_READY,
            is_default=False,
        )

    async def capture_sample(self, request: CaptureSampleRequest) -> CaptureSampleResult:
        raise vol.Invalid("capture_provider_unsupported: satellite enrollment is not available in this release")
