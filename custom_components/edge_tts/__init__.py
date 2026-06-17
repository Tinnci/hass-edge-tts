"""The Edge TTS integration."""

import logging
from base64 import urlsafe_b64decode

import voluptuous as vol
from aiohttp import web
from homeassistant.components.http import KEY_AUTHENTICATED, KEY_HASS, HomeAssistantView
from homeassistant.components.tts import async_create_stream
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_LIST_VOICES
from .voices import async_get_voice_catalog, voice_label

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.TTS]

ATTR_LANGUAGE = "language"
ATTR_GENDER = "gender"

LIST_VOICES_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_LANGUAGE): cv.string,
        vol.Optional(ATTR_GENDER): vol.In(["Female", "Male"]),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Edge TTS from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    hass.http.register_view(EdgeTtsProxyView)
    hass.http.register_view(EdgeTtsProxyView(url="/api/tts_proxy/edge/{filename:.*}"))
    _async_register_services(hass)
    return True


async def options_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not hass.config_entries.async_entries(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_LIST_VOICES)
    return unloaded


@callback
def _async_register_services(hass: HomeAssistant) -> None:
    """Register the integration-wide services once."""
    if hass.services.has_service(DOMAIN, SERVICE_LIST_VOICES):
        return

    async def _handle_list_voices(call: ServiceCall) -> ServiceResponse:
        """Return every voice the engine can synthesize, optionally filtered."""
        catalog = await async_get_voice_catalog(hass)
        language = call.data.get(ATTR_LANGUAGE)
        gender = call.data.get(ATTR_GENDER)

        voices = [
            {**entry, "label": voice_label(entry)}
            for entry in catalog
            if (not language or entry["locale"].lower().startswith(language.lower()))
            and (not gender or entry["gender"] == gender)
        ]
        return {"count": len(voices), "voices": voices}

    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_VOICES,
        _handle_list_voices,
        schema=LIST_VOICES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )


class EdgeTtsProxyView(HomeAssistantView):
    requires_auth = False
    cors_allowed = True
    url = "/api/tts_proxy/edge"
    name = "api:tts_proxy_edge"

    def __init__(self, url: str | None = None) -> None:
        if url:
            self.url = url

    async def get(self, request: web.Request, **_kwargs: str) -> web.StreamResponse:
        hass = request.app[KEY_HASS]
        domain_data = hass.data.setdefault(DOMAIN, {})
        access_token = request.query.get("token")
        authenticated = request.get(KEY_AUTHENTICATED)
        if not authenticated and access_token:
            authenticated = (
                access_token in domain_data.get("access_tokens", {}).values()
            )
        if not authenticated:
            raise web.HTTPUnauthorized
        if not (message := request.query.get("message")):
            return self.json({"error": "message empty"}, 400)
        if message.startswith("base64:"):
            message = urlsafe_b64decode(message[7:]).decode()

        entity_id = request.query.get("entity_id") or domain_data.get("tts_entity_id")
        try:
            stream = async_create_stream(
                hass,
                entity_id or "tts.edge_tts",
                language=request.query.get("language"),
                options={
                    "voice": request.query.get("voice", ""),
                    "rate": request.query.get("rate", "+10%").replace(" ", "+"),
                    "volume": request.query.get("volume", "+10%").replace(" ", "+"),
                },
            )
        except Exception as err:  # noqa: BLE001 - boundary: surface any stream-setup error as JSON 400
            return self.json({"error": str(err)}, 400)

        stream.async_set_message(message)
        response: web.StreamResponse | None = None
        try:
            async for data in stream.async_stream_result():
                if response is None:
                    response = web.StreamResponse()
                    response.content_type = stream.content_type
                    await response.prepare(request)
                await response.write(data)
        except Exception as err:
            _LOGGER.exception("Error streaming tts")
            return self.json({"error": str(err)}, 400)
        if response is None:
            return web.Response(status=500)
        await response.write_eof()
        return response
