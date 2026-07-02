"""Config flow for Concierge."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    BooleanSelector,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DEFAULT_NAME,
    DOMAIN,
)

CONF_AI_ENABLED = "ai_enabled"
CONF_AI_LOCAL_FIRST = "ai_local_first"
CONF_ACTION_PROVIDER = "action_provider"
CONF_TTS_ENABLED = "tts_enabled"
CONF_TTS_PROVIDER = "tts_provider"
CONF_MEDIA_PROVIDER = "media_provider"
CONF_ASSET_INTELLIGENCE_PROVIDER = "asset_intelligence_provider"

DEFAULT_AI_ENABLED = False
DEFAULT_AI_LOCAL_FIRST = True
DEFAULT_ACTION_PROVIDER = "none"
DEFAULT_TTS_ENABLED = False
DEFAULT_TTS_PROVIDER = "none"
DEFAULT_MEDIA_PROVIDER = "none"
DEFAULT_ASSET_INTELLIGENCE_PROVIDER = "none"

PROVIDER_NONE = "none"
PROVIDER_OPENAI = "openai_conversation"
PROVIDER_GOOGLE_TRANSLATE = "google_translate"
PROVIDER_MUSIC_ASSISTANT = "music_assistant"
PROVIDER_ASSET_INTELLIGENCE = "asset_intelligence"


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


def _build_global_config_schema(hass, defaults: dict) -> vol.Schema:
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
    }

    return vol.Schema(schema)


class ConciergeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Concierge."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input["name"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=_build_global_config_schema(self.hass, {"name": DEFAULT_NAME}),
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
        if user_input is not None:
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
        }
        return self.async_show_form(
            step_id="init",
            data_schema=_build_global_config_schema(self.hass, defaults),
        )
