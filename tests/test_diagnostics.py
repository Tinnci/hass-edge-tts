from homeassistant.components.tts import CONF_LANG
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.edge_tts.const import DATA_LAST_SYNTHESIS_TRACE, DOMAIN
from custom_components.edge_tts.diagnostics import async_get_config_entry_diagnostics
from custom_components.edge_tts.system_health import system_health_info
from custom_components.edge_tts.voices import CATALOG_SOURCE_KEY


async def test_diagnostics_excludes_proxy_tokens_and_spoken_text(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN, data={}, options={CONF_LANG: "zh-CN", "voice": "voice-a"}
    )
    hass.data[DOMAIN] = {
        "access_tokens": {"temp": "secret-token"},
        CATALOG_SOURCE_KEY: "live",
        DATA_LAST_SYNTHESIS_TRACE: {
            "status": "ok",
            "message_chars": 5,
            "elapsed_ms": 120,
        },
    }

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["voice_catalog"]["source"] == "live"
    assert result["last_synthesis_trace"]["message_chars"] == 5
    assert "access_tokens" not in str(result)
    assert "secret-token" not in str(result)


async def test_system_health_reports_catalog_and_last_trace(
    hass: HomeAssistant,
) -> None:
    hass.data[DOMAIN] = {
        CATALOG_SOURCE_KEY: "bundled_fallback",
        DATA_LAST_SYNTHESIS_TRACE: {"status": "ok", "elapsed_ms": 250},
    }

    result = await system_health_info(hass)

    assert result["voice_catalog_source"] == "bundled_fallback"
    assert result["voice_catalog_size"] > 300
    assert result["last_synthesis_status"] == "ok"
    assert result["last_synthesis_elapsed_ms"] == 250
