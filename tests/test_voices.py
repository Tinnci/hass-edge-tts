"""Tests for the runtime voice catalogue helpers (voices.py)."""

from unittest.mock import AsyncMock

from homeassistant.core import HomeAssistant

from custom_components.edge_tts.const import VOICES
from custom_components.edge_tts.voices import (
    async_get_voice_catalog,
    cached_catalog,
    voice_label,
)


async def test_live_catalog_is_normalized_and_cached(
    hass: HomeAssistant, mock_list_voices: AsyncMock
) -> None:
    """The live list is normalised, cached, and not re-fetched."""
    catalog = await async_get_voice_catalog(hass)
    assert len(catalog) == len(VOICES)

    entry = next(e for e in catalog if e["short_name"] == "zh-CN-XiaoxiaoNeural")
    assert entry["locale"] == "zh-CN"
    assert entry["gender"] == "Female"
    assert "Friendly" in entry["voice_personalities"]

    again = await async_get_voice_catalog(hass)
    assert again is catalog
    assert mock_list_voices.await_count == 1


async def test_catalog_falls_back_to_snapshot_when_offline(
    hass: HomeAssistant, mock_list_voices: AsyncMock
) -> None:
    """A network failure degrades to the bundled snapshot, not an error."""
    mock_list_voices.side_effect = ConnectionError("no network")
    catalog = await async_get_voice_catalog(hass)
    assert len(catalog) == len(VOICES)
    assert all("short_name" in entry for entry in catalog)


def test_cached_catalog_without_cache_uses_snapshot(hass: HomeAssistant) -> None:
    """cached_catalog works in callback contexts before any live fetch."""
    catalog = cached_catalog(hass)
    assert len(catalog) == len(VOICES)


def test_voice_label_formats_name_gender_personality() -> None:
    label = voice_label(
        {
            "short_name": "zh-CN-XiaoxiaoNeural",
            "locale": "zh-CN",
            "gender": "Female",
            "content_categories": ["News"],
            "voice_personalities": ["Warm"],
        }
    )
    assert label == "Xiaoxiao · Female · Warm"
