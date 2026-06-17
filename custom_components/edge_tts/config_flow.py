from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.tts import CONF_LANG
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_PITCH,
    CONF_RATE,
    CONF_VOICE,
    CONF_VOLUME,
    DEFAULT_LANG,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOLUME,
    DOMAIN,
)
from .voices import async_get_voice_catalog, voice_label


class EdgeTTSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Edge TTS config flow."""

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="Edge TTS", data={})

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> EdgeTTSOptionsFlowHandler:
        """Get the options flow for this handler."""
        return EdgeTTSOptionsFlowHandler(config_entry)


class EdgeTTSOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle an options flow for Edge TTS.

    Stores synthesis defaults (language, voice, rate, pitch, volume) on the
    config entry. They are merged into every request and overridden by any
    per-call ``tts.speak`` options.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        catalog = await async_get_voice_catalog(self.hass)
        locales = sorted({entry["locale"] for entry in catalog})
        voice_options = [
            SelectOptionDict(
                value=entry["short_name"],
                label=f"{entry['short_name']} — {voice_label(entry)}",
            )
            for entry in sorted(catalog, key=lambda entry: entry["short_name"])
        ]

        prosody = NumberSelector(
            NumberSelectorConfig(min=-100, max=100, step=1, mode=NumberSelectorMode.BOX)
        )
        schema = vol.Schema(
            {
                vol.Required(CONF_LANG, default=DEFAULT_LANG): SelectSelector(
                    SelectSelectorConfig(
                        options=locales, mode=SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(CONF_VOICE): SelectSelector(
                    SelectSelectorConfig(
                        options=voice_options,
                        mode=SelectSelectorMode.DROPDOWN,
                        custom_value=True,
                    )
                ),
                vol.Optional(CONF_RATE, default=DEFAULT_RATE): prosody,
                vol.Optional(CONF_PITCH, default=DEFAULT_PITCH): prosody,
                vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): prosody,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema, dict(self._config_entry.options)
            ),
        )
