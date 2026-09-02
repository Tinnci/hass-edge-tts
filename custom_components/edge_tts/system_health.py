"""System health support for Edge TTS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.core import callback

if TYPE_CHECKING:
    from homeassistant.components import system_health
    from homeassistant.core import HomeAssistant

from .const import DATA_LAST_SYNTHESIS_TRACE, DOMAIN
from .voices import CATALOG_SOURCE_KEY, cached_catalog


@callback
def async_register(
    _hass: HomeAssistant, register: system_health.SystemHealthRegistration
) -> None:
    """Register Edge TTS system-health information."""
    register.async_register_info(system_health_info)


async def system_health_info(hass: HomeAssistant) -> dict[str, Any]:
    """Return lightweight catalogue and synthesis health."""
    domain_data = hass.data.get(DOMAIN) or {}
    trace = domain_data.get(DATA_LAST_SYNTHESIS_TRACE)
    trace = trace if isinstance(trace, dict) else {}
    return {
        "voice_catalog_source": domain_data.get(CATALOG_SOURCE_KEY, "bundled_default"),
        "voice_catalog_size": len(cached_catalog(hass)),
        "last_synthesis_status": trace.get("status", "not_run"),
        "last_synthesis_elapsed_ms": trace.get("elapsed_ms"),
    }
