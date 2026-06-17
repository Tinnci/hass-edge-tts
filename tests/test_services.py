"""Tests for the edge_tts.list_voices service."""

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edge_tts.const import DOMAIN, SERVICE_LIST_VOICES


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN, title="Edge TTS", data={})
    entry.add_to_hass(hass)
    hass.data["core.uuid"] = "test-edge-tts-uuid"
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_list_voices_service_is_registered(hass: HomeAssistant) -> None:
    await _setup_entry(hass)
    assert hass.services.has_service(DOMAIN, SERVICE_LIST_VOICES)


async def test_list_voices_service_filters_by_language(hass: HomeAssistant) -> None:
    await _setup_entry(hass)

    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_LIST_VOICES,
        {"language": "zh"},
        blocking=True,
        return_response=True,
    )

    assert result["count"] > 0
    assert result["count"] == len(result["voices"])
    assert all(v["locale"].startswith("zh") for v in result["voices"])
    assert any(v["short_name"] == "zh-CN-XiaoxiaoNeural" for v in result["voices"])
    assert all("label" in v for v in result["voices"])


async def test_list_voices_service_filters_by_gender(hass: HomeAssistant) -> None:
    await _setup_entry(hass)

    result = await hass.services.async_call(
        DOMAIN,
        SERVICE_LIST_VOICES,
        {"gender": "Male"},
        blocking=True,
        return_response=True,
    )

    assert result["count"] > 0
    assert all(v["gender"] == "Male" for v in result["voices"])
