"""Tests for the Edge TTS config flow."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edge_tts.const import DOMAIN


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """A user-initiated flow creates the Edge TTS entry with no input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Edge TTS"


async def test_single_instance_only(hass: HomeAssistant) -> None:
    """A second flow aborts because only one instance is allowed."""
    first = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert first["type"] is FlowResultType.CREATE_ENTRY

    second = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "single_instance_allowed"


async def test_options_flow_stores_synthesis_defaults(hass: HomeAssistant) -> None:
    """The options flow persists language/voice/prosody defaults on the entry."""
    entry = MockConfigEntry(domain=DOMAIN, title="Edge TTS", data={})
    entry.add_to_hass(hass)
    hass.data["core.uuid"] = "test-edge-tts-uuid"
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "language": "zh-CN",
            "voice": "zh-CN-YunxiNeural",
            "rate": 10,
            "pitch": 0,
            "volume": -5,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["voice"] == "zh-CN-YunxiNeural"
    assert entry.options["rate"] == 10
    assert entry.options["volume"] == -5
    # The options flow must not clobber the runtime domain data.
    assert "access_tokens" in hass.data[DOMAIN]
