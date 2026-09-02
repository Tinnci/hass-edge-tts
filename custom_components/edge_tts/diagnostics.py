"""Diagnostics support for Edge TTS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

from .const import DATA_LAST_SYNTHESIS_TRACE, DOMAIN
from .voices import CATALOG_SOURCE_KEY, cached_catalog


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return synthesis diagnostics without proxy tokens or spoken text."""
    domain_data = hass.data.get(DOMAIN) or {}
    trace = domain_data.get(DATA_LAST_SYNTHESIS_TRACE)
    return {
        "entry": dict(entry.data),
        "options": dict(entry.options),
        "voice_catalog": {
            "source": domain_data.get(CATALOG_SOURCE_KEY, "bundled_default"),
            "voices": len(cached_catalog(hass)),
        },
        "last_synthesis_trace": dict(trace) if isinstance(trace, dict) else {},
    }
