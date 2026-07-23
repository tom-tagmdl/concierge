"""Config flow for Concierge."""

from __future__ import annotations

import os

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .archive_runtime import (
    CONF_AUDIT_ARCHIVE_RETENTION_DAYS,
    DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS,
    is_valid_archive_destination_uri,
    normalize_archive_destination,
)

from .const import (
    DEFAULT_NAME,
    DOMAIN,
    CONF_VOICE_IDENTITY_LINKED,
)

CONF_AI_ENABLED = "ai_enabled"
CONF_AI_LOCAL_FIRST = "ai_local_first"
CONF_ACTION_PROVIDER = "action_provider"
CONF_TTS_ENABLED = "tts_enabled"
CONF_TTS_PROVIDER = "tts_provider"
CONF_MEDIA_PROVIDER = "media_provider"
CONF_ASSET_INTELLIGENCE_PROVIDER = "asset_intelligence_provider"
CONF_AUDIT_ARCHIVE_DESTINATION_URI = "audit_archive_destination_uri"
CONF_AUDIT_ARCHIVE_ENABLED = "audit_archive_enabled"
CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS = "audit_archive_include_reference_excerpts"
_VOICE_IDENTITY_DOMAIN = "voice_identity"
_VOICE_IDENTITY_DEFAULT_MODEL = "ecapa_v1"
_VOICE_IDENTITY_ALIGNMENT_NOTIFICATION_ID = "concierge_voice_identity_alignment"

DEFAULT_AI_ENABLED = False
DEFAULT_AI_LOCAL_FIRST = True
DEFAULT_ACTION_PROVIDER = "none"
DEFAULT_TTS_ENABLED = False
DEFAULT_TTS_PROVIDER = "none"
DEFAULT_MEDIA_PROVIDER = "none"
DEFAULT_ASSET_INTELLIGENCE_PROVIDER = "none"
DEFAULT_AUDIT_ARCHIVE_DESTINATION_URI = ""
DEFAULT_AUDIT_ARCHIVE_ENABLED = False
DEFAULT_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS = False

PROVIDER_NONE = "none"
PROVIDER_OPENAI = "openai_conversation"
PROVIDER_GOOGLE_TRANSLATE = "google_translate"
PROVIDER_MUSIC_ASSISTANT = "music_assistant"
PROVIDER_ASSET_INTELLIGENCE = "asset_intelligence"


def _discover_archive_destination_options() -> list[SelectOptionDict]:
    """Discover candidate archive destinations from attached HA storage roots."""
    options: list[SelectOptionDict] = [
        SelectOptionDict(value="", label="Not set")
    ]
    seen: set[str] = {""}
    discovered_paths: list[str] = []
    root_paths = ("/media", "/share")

    for root in root_paths:
        if not os.path.isdir(root):
            continue
        try:
            for dirpath, _, _ in os.walk(root, topdown=True, followlinks=False):
                normalized = normalize_archive_destination(dirpath)
                if normalized and normalized not in seen:
                    discovered_paths.append(normalized)
                    seen.add(normalized)
        except OSError:
            continue

    for path in sorted(discovered_paths, key=lambda item: item.lower()):
        options.append(SelectOptionDict(value=path, label=path))

    return options


async def _async_discover_archive_destination_options(hass) -> list[SelectOptionDict]:
    """Discover archive destination options without blocking the event loop."""
    return await hass.async_add_executor_job(_discover_archive_destination_options)


def _select(options: list[SelectOptionDict]) -> SelectSelector:
    """Build a standard dropdown selector."""
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.DROPDOWN,
        )
    )


def _discover_action_provider_options(hass) -> list[SelectOptionDict]:
    """Return available action providers from installed integrations."""
    options = [SelectOptionDict(value=PROVIDER_NONE, label="None")]

    if hass.config_entries.async_entries(PROVIDER_OPENAI):
        options.append(
            SelectOptionDict(value=PROVIDER_OPENAI, label="OpenAI (cloud hybrid)")
        )

    return options


def _discover_tts_provider_options(hass) -> list[SelectOptionDict]:
    """Return available TTS providers from installed integrations."""
    options = [SelectOptionDict(value=PROVIDER_NONE, label="None")]

    if hass.config_entries.async_entries(PROVIDER_OPENAI):
        options.append(
            SelectOptionDict(value=PROVIDER_OPENAI, label="OpenAI TTS (cloud hybrid)")
        )
    if hass.config_entries.async_entries(PROVIDER_GOOGLE_TRANSLATE):
        options.append(
            SelectOptionDict(
                value=PROVIDER_GOOGLE_TRANSLATE,
                label="Google Translate text-to-speech",
            )
        )

    return options


def _discover_media_provider_options(hass) -> list[SelectOptionDict]:
    """Return available media providers from installed integrations."""
    options = [SelectOptionDict(value=PROVIDER_NONE, label="None")]

    if hass.config_entries.async_entries(PROVIDER_MUSIC_ASSISTANT):
        options.append(
            SelectOptionDict(
                value=PROVIDER_MUSIC_ASSISTANT,
                label="Music Assistant",
            )
        )

    return options


def _discover_asset_intelligence_options(hass) -> list[SelectOptionDict]:
    """Return available Asset Intelligence connection options."""
    options = [SelectOptionDict(value=PROVIDER_NONE, label="None")]

    entries = hass.config_entries.async_entries(PROVIDER_ASSET_INTELLIGENCE)
    if entries:
        is_connected = any(entry.state is ConfigEntryState.LOADED for entry in entries)
        label = (
            "Asset Intelligence (connected)"
            if is_connected
            else "Asset Intelligence (installed)"
        )
        options.append(
            SelectOptionDict(
                value=PROVIDER_ASSET_INTELLIGENCE,
                label=label,
            )
        )

    return options


def _resolve_default_from_options(
    requested: str,
    options: list[SelectOptionDict],
    fallback: str,
) -> str:
    """Return a valid default value constrained to available selector options."""
    values = {option["value"] for option in options}
    if requested in values:
        return requested
    if fallback in values:
        return fallback
    return next(iter(values), fallback)


async def _async_notify_voice_identity_alignment(hass, updates: list[str]) -> None:
    """Publish a user-facing summary when Concierge aligns Voice Identity settings."""
    if not updates:
        return

    message_lines = [
        "Concierge updated Voice Identity settings to keep enrollment and build flows aligned:",
        "",
    ]
    message_lines.extend(f"- {item}" for item in updates)
    message_lines.extend(
        [
            "",
            "You can review or adjust these values in Voice Identity options.",
        ]
    )

    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "title": "Concierge aligned Voice Identity",
            "message": "\n".join(message_lines),
            "notification_id": _VOICE_IDENTITY_ALIGNMENT_NOTIFICATION_ID,
        },
        blocking=True,
    )


async def _async_align_voice_identity_entry_for_concierge(hass, *, linked: bool) -> list[str]:
    """Align Voice Identity runtime options when Concierge linkage is enabled."""
    if not linked:
        return []

    entries = hass.config_entries.async_entries(_VOICE_IDENTITY_DOMAIN)
    if not entries:
        return []

    entry = entries[0]
    merged = {**dict(entry.data), **dict(entry.options)}
    updates: list[str] = []

    service = dict(merged.get("service") or {})
    generation = dict(merged.get("generation") or {})
    feature_flags = dict(merged.get("feature_flags") or {})

    if not bool(service.get("enabled", False)):
        updates.append("service.enabled -> true")
    service["enabled"] = True

    model_preference = str(generation.get("model_preference") or _VOICE_IDENTITY_DEFAULT_MODEL).strip() or _VOICE_IDENTITY_DEFAULT_MODEL
    if str(generation.get("model_preference") or "").strip() != model_preference:
        updates.append(f"generation.model_preference -> {model_preference}")
    raw_supported_models = generation.get("supported_models", (_VOICE_IDENTITY_DEFAULT_MODEL,))
    if isinstance(raw_supported_models, str):
        supported_models = tuple(item.strip() for item in raw_supported_models.split(",") if item.strip())
    else:
        supported_models = tuple(str(item).strip() for item in raw_supported_models if str(item).strip())
    if not supported_models:
        supported_models = (_VOICE_IDENTITY_DEFAULT_MODEL,)
    if model_preference not in supported_models:
        supported_models = tuple(dict.fromkeys((*supported_models, model_preference)))
        updates.append(
            f"generation.supported_models includes {model_preference}"
        )

    generation["model_preference"] = model_preference
    generation["supported_models"] = supported_models

    # Concierge enrollment requires a generation backend path during development
    # validation. Enabling experimental models activates deterministic execution.
    if not bool(feature_flags.get("enable_experimental_models", False)):
        updates.append("feature_flags.enable_experimental_models -> true")
    feature_flags["enable_experimental_models"] = True

    updated_options = dict(entry.options)
    updated_options["service"] = service
    updated_options["generation"] = generation
    updated_options["feature_flags"] = feature_flags

    if updated_options == dict(entry.options):
        return []

    hass.config_entries.async_update_entry(entry, options=updated_options)
    return updates


def _build_global_config_schema(
    hass,
    defaults: dict,
    archive_destination_options: list[SelectOptionDict],
) -> vol.Schema:
    """Return the initial global configuration schema."""
    action_provider_options = _discover_action_provider_options(hass)
    tts_provider_options = _discover_tts_provider_options(hass)
    media_provider_options = _discover_media_provider_options(hass)
    asset_intelligence_options = _discover_asset_intelligence_options(hass)

    action_provider_default = _resolve_default_from_options(
        defaults.get(CONF_ACTION_PROVIDER, DEFAULT_ACTION_PROVIDER),
        action_provider_options,
        PROVIDER_OPENAI,
    )
    tts_provider_default = _resolve_default_from_options(
        defaults.get(CONF_TTS_PROVIDER, DEFAULT_TTS_PROVIDER),
        tts_provider_options,
        PROVIDER_OPENAI,
    )
    media_provider_default = _resolve_default_from_options(
        defaults.get(CONF_MEDIA_PROVIDER, DEFAULT_MEDIA_PROVIDER),
        media_provider_options,
        PROVIDER_MUSIC_ASSISTANT,
    )
    asset_intelligence_default = _resolve_default_from_options(
        defaults.get(
            CONF_ASSET_INTELLIGENCE_PROVIDER,
            DEFAULT_ASSET_INTELLIGENCE_PROVIDER,
        ),
        asset_intelligence_options,
        PROVIDER_ASSET_INTELLIGENCE,
    )
    voice_identity_linked_default = bool(defaults.get(CONF_VOICE_IDENTITY_LINKED, False))
    archive_destination_default = _resolve_default_from_options(
        normalize_archive_destination(
            defaults.get(
                CONF_AUDIT_ARCHIVE_DESTINATION_URI,
                DEFAULT_AUDIT_ARCHIVE_DESTINATION_URI,
            )
        ),
        archive_destination_options,
        "",
    )
    destination_is_valid = is_valid_archive_destination_uri(archive_destination_default)
    archive_retention_days_default = max(
        1,
        int(defaults.get(CONF_AUDIT_ARCHIVE_RETENTION_DAYS, DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS)),
    )

    schema: dict = {
        vol.Required("name", default=defaults.get("name", DEFAULT_NAME)): str,
        vol.Required(
            CONF_AI_ENABLED,
            default=defaults.get(CONF_AI_ENABLED, DEFAULT_AI_ENABLED),
        ): BooleanSelector(),
        vol.Required(
            CONF_AI_LOCAL_FIRST,
            default=defaults.get(CONF_AI_LOCAL_FIRST, DEFAULT_AI_LOCAL_FIRST),
        ): BooleanSelector(),
        vol.Required(CONF_ACTION_PROVIDER, default=action_provider_default): _select(
            action_provider_options
        ),
        vol.Required(
            CONF_TTS_ENABLED,
            default=defaults.get(CONF_TTS_ENABLED, DEFAULT_TTS_ENABLED),
        ): BooleanSelector(),
        vol.Required(CONF_TTS_PROVIDER, default=tts_provider_default): _select(
            tts_provider_options
        ),
        vol.Required(CONF_MEDIA_PROVIDER, default=media_provider_default): _select(
            media_provider_options
        ),
        vol.Required(
            CONF_ASSET_INTELLIGENCE_PROVIDER,
            default=asset_intelligence_default,
        ): _select(asset_intelligence_options),
        vol.Required(CONF_VOICE_IDENTITY_LINKED, default=voice_identity_linked_default): BooleanSelector(),
        vol.Required(
            CONF_AUDIT_ARCHIVE_DESTINATION_URI,
            default=archive_destination_default,
            description={
                "label": "Audit archive destination",
            },
        ): _select(archive_destination_options),
        vol.Required(
            CONF_AUDIT_ARCHIVE_ENABLED,
            default=(
                bool(defaults.get(CONF_AUDIT_ARCHIVE_ENABLED, DEFAULT_AUDIT_ARCHIVE_ENABLED))
                if destination_is_valid
                else False
            ),
            description={
                "label": "Enable audit archive exports",
            },
        ): BooleanSelector(),
        vol.Required(
            CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
            default=(
                bool(
                    defaults.get(
                        CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
                        DEFAULT_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
                    )
                )
                if destination_is_valid
                else False
            ),
            description={
                "label": "Include reference excerpts in archive exports",
            },
        ): BooleanSelector(),
        vol.Required(
            CONF_AUDIT_ARCHIVE_RETENTION_DAYS,
            default=archive_retention_days_default,
            description={
                "label": "Archive retention days",
            },
        ): NumberSelector(
            NumberSelectorConfig(
                min=1,
                max=3650,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        ),
    }

    return vol.Schema(schema)


class ConciergeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Concierge."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        archive_destination_options = await _async_discover_archive_destination_options(self.hass)
        if user_input is not None:
            destination = normalize_archive_destination(
                user_input.get(CONF_AUDIT_ARCHIVE_DESTINATION_URI, "")
            )
            user_input[CONF_AUDIT_ARCHIVE_DESTINATION_URI] = destination
            user_input[CONF_VOICE_IDENTITY_LINKED] = bool(user_input.get(CONF_VOICE_IDENTITY_LINKED, False))
            user_input[CONF_AUDIT_ARCHIVE_RETENTION_DAYS] = max(
                1,
                int(user_input.get(CONF_AUDIT_ARCHIVE_RETENTION_DAYS, DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS)),
            )

            destination_is_valid = is_valid_archive_destination_uri(destination)

            if destination and not is_valid_archive_destination_uri(destination):
                return self.async_show_form(
                    step_id="user",
                    data_schema=_build_global_config_schema(self.hass, user_input, archive_destination_options),
                    errors={"base": "invalid_archive_destination"},
                )

            if not destination_is_valid:
                user_input[CONF_AUDIT_ARCHIVE_ENABLED] = False
                user_input[CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS] = False

            alignment_updates = await _async_align_voice_identity_entry_for_concierge(
                self.hass,
                linked=bool(user_input.get(CONF_VOICE_IDENTITY_LINKED, False)),
            )
            await _async_notify_voice_identity_alignment(self.hass, alignment_updates)

            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_global_config_schema(self.hass, {"name": DEFAULT_NAME}, archive_destination_options),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow."""
        return ConciergeOptionsFlow(config_entry)


class ConciergeOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Concierge."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        """Manage options."""
        archive_destination_options = await _async_discover_archive_destination_options(self.hass)
        if user_input is not None:
            destination = normalize_archive_destination(
                user_input.get(CONF_AUDIT_ARCHIVE_DESTINATION_URI, "")
            )
            user_input[CONF_AUDIT_ARCHIVE_DESTINATION_URI] = destination
            user_input[CONF_VOICE_IDENTITY_LINKED] = bool(user_input.get(CONF_VOICE_IDENTITY_LINKED, False))
            user_input[CONF_AUDIT_ARCHIVE_RETENTION_DAYS] = max(
                1,
                int(user_input.get(CONF_AUDIT_ARCHIVE_RETENTION_DAYS, DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS)),
            )

            destination_is_valid = is_valid_archive_destination_uri(destination)

            if destination and not is_valid_archive_destination_uri(destination):
                return self.async_show_form(
                    step_id="init",
                    data_schema=_build_global_config_schema(self.hass, user_input, archive_destination_options),
                    errors={"base": "invalid_archive_destination"},
                )

            if not destination_is_valid:
                user_input[CONF_AUDIT_ARCHIVE_ENABLED] = False
                user_input[CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS] = False

            alignment_updates = await _async_align_voice_identity_entry_for_concierge(
                self.hass,
                linked=bool(user_input.get(CONF_VOICE_IDENTITY_LINKED, False)),
            )
            await _async_notify_voice_identity_alignment(self.hass, alignment_updates)

            return self.async_create_entry(title="", data=user_input)

        defaults = {
            "name": self._config_entry.title,
            CONF_AI_ENABLED: self._config_entry.options.get(
                CONF_AI_ENABLED,
                self._config_entry.data.get(CONF_AI_ENABLED, DEFAULT_AI_ENABLED),
            ),
            CONF_AI_LOCAL_FIRST: self._config_entry.options.get(
                CONF_AI_LOCAL_FIRST,
                self._config_entry.data.get(CONF_AI_LOCAL_FIRST, DEFAULT_AI_LOCAL_FIRST),
            ),
            CONF_ACTION_PROVIDER: self._config_entry.options.get(
                CONF_ACTION_PROVIDER,
                self._config_entry.data.get(CONF_ACTION_PROVIDER, DEFAULT_ACTION_PROVIDER),
            ),
            CONF_TTS_ENABLED: self._config_entry.options.get(
                CONF_TTS_ENABLED,
                self._config_entry.data.get(CONF_TTS_ENABLED, DEFAULT_TTS_ENABLED),
            ),
            CONF_TTS_PROVIDER: self._config_entry.options.get(
                CONF_TTS_PROVIDER,
                self._config_entry.data.get(CONF_TTS_PROVIDER, DEFAULT_TTS_PROVIDER),
            ),
            CONF_MEDIA_PROVIDER: self._config_entry.options.get(
                CONF_MEDIA_PROVIDER,
                self._config_entry.data.get(CONF_MEDIA_PROVIDER, DEFAULT_MEDIA_PROVIDER),
            ),
            CONF_ASSET_INTELLIGENCE_PROVIDER: self._config_entry.options.get(
                CONF_ASSET_INTELLIGENCE_PROVIDER,
                self._config_entry.data.get(
                    CONF_ASSET_INTELLIGENCE_PROVIDER,
                    DEFAULT_ASSET_INTELLIGENCE_PROVIDER,
                ),
            ),
            CONF_VOICE_IDENTITY_LINKED: self._config_entry.options.get(
                CONF_VOICE_IDENTITY_LINKED,
                self._config_entry.data.get(CONF_VOICE_IDENTITY_LINKED, False),
            ),
            CONF_AUDIT_ARCHIVE_DESTINATION_URI: self._config_entry.options.get(
                CONF_AUDIT_ARCHIVE_DESTINATION_URI,
                self._config_entry.data.get(
                    CONF_AUDIT_ARCHIVE_DESTINATION_URI,
                    DEFAULT_AUDIT_ARCHIVE_DESTINATION_URI,
                ),
            ),
            CONF_AUDIT_ARCHIVE_ENABLED: self._config_entry.options.get(
                CONF_AUDIT_ARCHIVE_ENABLED,
                self._config_entry.data.get(
                    CONF_AUDIT_ARCHIVE_ENABLED,
                    DEFAULT_AUDIT_ARCHIVE_ENABLED,
                ),
            ),
            CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS: self._config_entry.options.get(
                CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
                self._config_entry.data.get(
                    CONF_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
                    DEFAULT_AUDIT_ARCHIVE_INCLUDE_REFERENCE_EXCERPTS,
                ),
            ),
            CONF_AUDIT_ARCHIVE_RETENTION_DAYS: self._config_entry.options.get(
                CONF_AUDIT_ARCHIVE_RETENTION_DAYS,
                self._config_entry.data.get(
                    CONF_AUDIT_ARCHIVE_RETENTION_DAYS,
                    DEFAULT_AUDIT_ARCHIVE_RETENTION_DAYS,
                ),
            ),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_build_global_config_schema(self.hass, defaults, archive_destination_options),
        )
