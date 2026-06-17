"""Tests for the Edge TTS entity setup and audio path."""

from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edge_tts.const import DEFAULT_LANG, DEFAULT_VOICE, DOMAIN
from custom_components.edge_tts.tts import EdgeTTSEntity


async def test_entry_sets_up_tts_entity(hass: HomeAssistant) -> None:
    """Setting up the config entry loads it and exposes a tts entity."""
    entry = MockConfigEntry(domain=DOMAIN, title="Edge TTS", data={})
    entry.add_to_hass(hass)
    # core.uuid is populated by HA bootstrap in production; supply it for the
    # minimal test instance so async_added_to_hass can build its access tokens.
    hass.data["core.uuid"] = "test-edge-tts-uuid"
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    tts_entities = [
        s.entity_id for s in hass.states.async_all() if s.entity_id.startswith("tts.")
    ]
    assert any("edge" in eid for eid in tts_entities), tts_entities


async def test_supported_languages_includes_default(hass: HomeAssistant) -> None:
    """Both the default language and raw voice names are accepted languages."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)

    langs = entity.supported_languages
    assert DEFAULT_LANG in langs
    assert DEFAULT_VOICE in langs


async def test_get_tts_audio_returns_mp3(hass: HomeAssistant) -> None:
    """async_get_tts_audio streams chunks from edge_tts into mp3 bytes."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)

    fake_chunks = [
        {"type": "audio", "data": b"\x01\x02"},
        {"type": "WordBoundary"},
        {"type": "audio", "data": b"\x03"},
    ]
    with patch("custom_components.edge_tts.tts.edge_tts.Communicate") as communicate:
        communicate.return_value.stream_sync.return_value = fake_chunks
        fmt, data = await entity.async_get_tts_audio("你好", "zh-CN", {})

    assert fmt == "mp3"
    assert data == b"\x01\x02\x03"
    communicate.assert_called_once()
