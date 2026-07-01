"""Tests for the Edge TTS entity setup and audio path."""

from unittest.mock import patch

import edge_tts
import pytest
from homeassistant.components.tts import Voice
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edge_tts.const import (
    DATA_LAST_SYNTHESIS_TRACE,
    DEFAULT_LANG,
    DEFAULT_VOICE,
    DOMAIN,
    TTS_SYNTHESIS_TRACE_SCHEMA_VERSION,
)
from custom_components.edge_tts.tts import EdgeTTSEntity, _as_edge_value
from custom_components.edge_tts.voices import async_get_voice_catalog


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


async def test_get_tts_audio_records_last_synthesis_trace(
    hass: HomeAssistant,
) -> None:
    """The latest synthesis trace is stored without retaining spoken text."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)

    with patch("custom_components.edge_tts.tts.edge_tts.Communicate") as communicate:
        communicate.return_value.stream_sync.return_value = [
            {"type": "audio", "data": b"\x01\x02"},
            {"type": "WordBoundary"},
            {"type": "audio", "data": b"\x03"},
        ]
        await entity.async_get_tts_audio(
            "不要把这句话写入 trace", "zh-CN", {"rate": 10, "pitch": -5}
        )

    trace = hass.data[DOMAIN][DATA_LAST_SYNTHESIS_TRACE]
    assert trace["schema_version"] == TTS_SYNTHESIS_TRACE_SCHEMA_VERSION
    assert trace["status"] == "ok"
    assert trace["provider"] == "edge-tts"
    assert trace["language"] == "zh-CN"
    assert trace["voice"] == DEFAULT_VOICE
    assert trace["prosody"]["rate"] == "+10%"
    assert trace["prosody"]["pitch"] == "-5Hz"
    assert trace["audio_bytes"] == 3
    assert trace["audio_chunks"] == 2
    assert trace["metadata_chunks"] == 1
    assert trace["message_chars"] == len("不要把这句话写入 trace")
    assert "不要把这句话写入 trace" not in str(trace)
    assert entity.extra_state_attributes[DATA_LAST_SYNTHESIS_TRACE] == trace


async def test_get_tts_audio_records_failure_trace(hass: HomeAssistant) -> None:
    """Synthesis failures still leave a structured diagnostic trace."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)

    with patch("custom_components.edge_tts.tts.edge_tts.Communicate") as communicate:
        communicate.return_value.stream_sync.side_effect = (
            edge_tts.exceptions.NoAudioReceived("empty")
        )
        with pytest.raises(HomeAssistantError) as err:
            await entity.async_get_tts_audio("失败也不要保留原文", "zh-CN", {})

    trace = hass.data[DOMAIN][DATA_LAST_SYNTHESIS_TRACE]
    assert trace["status"] == "error"
    assert trace["error_phase"] == "stream"
    assert trace["error_type"] == "NoAudioReceived"
    assert trace["audio_bytes"] == 0
    assert trace["message_chars"] == len("失败也不要保留原文")
    assert "失败也不要保留原文" not in str(trace)
    assert "失败也不要保留原文" not in str(err.value)


@pytest.mark.parametrize(
    ("value", "unit", "expected"),
    [
        (10, "%", "+10%"),
        (-5, "Hz", "-5Hz"),
        (0, "%", "+0%"),
        (10.0, "%", "+10%"),
        ("10", "%", "+10%"),
        ("+10%", "%", "+10%"),
        ("-5Hz", "Hz", "-5Hz"),
        ("+0%", "%", "+0%"),
    ],
)
def test_as_edge_value(value: object, unit: str, expected: str) -> None:
    """Ints/floats/bare strings become signed Edge strings; formatted pass through."""
    assert _as_edge_value(value, unit) == expected


async def test_prosody_options_formatted_for_edge(hass: HomeAssistant) -> None:
    """Integer prosody options are converted to the strings Edge expects."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, options={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)

    with patch("custom_components.edge_tts.tts.edge_tts.Communicate") as communicate:
        communicate.return_value.stream_sync.return_value = [
            {"type": "audio", "data": b"x"}
        ]
        await entity.async_get_tts_audio(
            "hi", "zh-CN", {"rate": 10, "pitch": -5, "volume": 20}
        )

    _, kwargs = communicate.call_args
    assert kwargs["rate"] == "+10%"
    assert kwargs["pitch"] == "-5Hz"
    assert kwargs["volume"] == "+20%"


async def test_async_get_supported_voices_by_locale(hass: HomeAssistant) -> None:
    """A locale returns its voices as Voice objects with friendly labels."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)
    await async_get_voice_catalog(hass)  # warm the cache

    voices = entity.async_get_supported_voices("zh-CN")
    assert voices is not None
    assert all(isinstance(v, Voice) for v in voices)
    ids = [v.voice_id for v in voices]
    assert "zh-CN-XiaoxiaoNeural" in ids
    label = next(v.name for v in voices if v.voice_id == "zh-CN-XiaoxiaoNeural")
    assert "Xiaoxiao" in label


async def test_async_get_supported_voices_by_raw_voice_name(
    hass: HomeAssistant,
) -> None:
    """Passing a raw voice name returns the sibling voices of its locale."""
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)
    await async_get_voice_catalog(hass)

    voices = entity.async_get_supported_voices("zh-CN-XiaoxiaoNeural")
    assert voices is not None
    ids = [v.voice_id for v in voices]
    assert "zh-CN-XiaoxiaoNeural" in ids
    assert "zh-CN-YunxiNeural" in ids


async def test_async_get_supported_voices_unknown_returns_none(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)
    entity = EdgeTTSEntity(hass, entry)
    await async_get_voice_catalog(hass)

    assert entity.async_get_supported_voices("xx-XX") is None
