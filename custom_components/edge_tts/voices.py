"""Runtime voice catalogue: a live fetch from Microsoft with a static fallback.

``const.VOICES`` is a snapshot bundled with the integration. At runtime we try
to fetch the current list from Microsoft (which is what ``edge-tts`` itself
does) so newly released voices appear without shipping a new release, and fall
back to the bundled snapshot when the network is unavailable.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import edge_tts

from .const import DOMAIN, VOICES

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Key under ``hass.data[DOMAIN]`` where the resolved catalogue is cached.
CATALOG_KEY = "voice_catalog"

# A single normalised voice record.
VoiceEntry = dict[str, Any]


def _static_catalog() -> list[VoiceEntry]:
    """Build the catalogue from the bundled snapshot in ``const.VOICES``.

    The snapshot only carries locale and gender; style metadata is available
    from the live list when online.
    """
    return [
        {
            "short_name": short_name,
            "locale": locale,
            "gender": gender,
            "content_categories": [],
            "voice_personalities": [],
        }
        for short_name, (locale, gender) in VOICES.items()
    ]


def _normalize(voice: dict[str, Any]) -> VoiceEntry:
    """Normalise one entry from ``edge_tts.list_voices`` to our record shape."""
    tag = voice.get("VoiceTag") or {}
    return {
        "short_name": voice["ShortName"],
        "locale": voice["Locale"],
        "gender": voice.get("Gender", ""),
        "content_categories": list(tag.get("ContentCategories") or []),
        "voice_personalities": list(tag.get("VoicePersonalities") or []),
    }


async def async_get_voice_catalog(
    hass: HomeAssistant, *, force_refresh: bool = False
) -> list[VoiceEntry]:
    """Return the voice catalogue, fetching live once and caching the result.

    Falls back to the bundled snapshot if the live list cannot be retrieved.
    """
    domain_data = hass.data.setdefault(DOMAIN, {})
    cached = domain_data.get(CATALOG_KEY)
    if cached and not force_refresh:
        return cached

    try:
        live = await edge_tts.list_voices()
        catalog = [_normalize(voice) for voice in live]
        catalog.sort(key=lambda entry: entry["short_name"])
        _LOGGER.debug("Fetched %d voices from Edge TTS", len(catalog))
    except Exception as err:  # noqa: BLE001 - network boundary; degrade gracefully
        _LOGGER.warning(
            "Could not fetch the live Edge TTS voice list (%s); "
            "using the bundled catalogue of %d voices",
            err,
            len(VOICES),
        )
        catalog = _static_catalog()

    domain_data[CATALOG_KEY] = catalog
    return catalog


def cached_catalog(hass: HomeAssistant) -> list[VoiceEntry]:
    """Return the cached catalogue, or the bundled snapshot if none is cached.

    Synchronous accessor for callback contexts (e.g. ``async_get_supported_
    voices``), where awaiting a live fetch is not possible.
    """
    domain_data = hass.data.get(DOMAIN) or {}
    return domain_data.get(CATALOG_KEY) or _static_catalog()


def voice_label(entry: VoiceEntry) -> str:
    """Build a friendly label, e.g. ``Xiaoxiao · Female · Warm``."""
    short_name = entry["short_name"]
    # Drop the locale prefix and the trailing "Neural" for the spoken name.
    name = short_name.split("-")[-1].removesuffix("Neural")
    parts = [name]
    if entry.get("gender"):
        parts.append(entry["gender"])
    if personalities := entry.get("voice_personalities"):
        parts.append(", ".join(personalities))
    return " · ".join(parts)
