"""The speech service."""

import contextlib
import datetime as dt
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from homeassistant.components.tts import (
    CONF_LANG,
    TextToSpeechEntity,
    TTSAudioRequest,
    TTSAudioResponse,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import ulid

import edge_tts

from .const import (
    CONF_PITCH,
    CONF_RATE,
    CONF_VOICE,
    CONF_VOLUME,
    DATA_LAST_SYNTHESIS_TRACE,
    DEFAULT_LANG,
    DEFAULT_PITCH,
    DEFAULT_RATE,
    DEFAULT_VOICE,
    DEFAULT_VOLUME,
    DOMAIN,
    SUPPORTED_VOICES,
    TTS_SYNTHESIS_TRACE_SCHEMA_VERSION,
)
from .voices import async_get_voice_catalog, cached_catalog, voice_label

_LOGGER = logging.getLogger(__name__)

# Locale -> a representative default voice, used when only a language is given.
SUPPORTED_LANGUAGES = {
    **dict(zip(SUPPORTED_VOICES.values(), SUPPORTED_VOICES.keys(), strict=True)),
    DEFAULT_LANG: DEFAULT_VOICE,
}

# Style options removed by Microsoft; warn if anyone still passes them.
_STYLE_OPTIONS = ("style", "styledegree", "role")


class _SynthesisError(HomeAssistantError):
    """Internal synthesis error that carries a structured diagnostic trace."""

    def __init__(self, message: str, trace: dict[str, Any]) -> None:
        super().__init__(message)
        self.trace = trace


def _as_edge_value(value: str | float, unit: str) -> str:
    """Coerce a prosody option to the signed string Edge expects.

    Accepts integers/floats (``10`` -> ``"+10%"``) as well as strings that are
    already formatted (``"+10%"``, ``"-5Hz"``) or are bare numbers (``"10"``).
    """
    if isinstance(value, str):
        text = value.strip().replace(" ", "+")
        if text.endswith(("%", "Hz", "st")):
            return text
        try:
            number = int(float(text))
        except ValueError:
            # Leave it to edge_tts to validate and raise a clear error.
            return value
    else:
        number = int(value)
    return f"{'+' if number >= 0 else '-'}{abs(number)}{unit}"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Edge TTS entity from a config entry."""
    entity = EdgeTTSEntity(hass, config_entry)
    async_add_entities([entity])


class EdgeTTSEntity(TextToSpeechEntity):
    """The Edge TTS entity."""

    _attr_name = "Edge TTS"

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize Edge TTS entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._attr_unique_id = f"{config_entry.entry_id}-tts"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._config_entry.entry_id)},
            "name": "Edge TTS Service",
            "manufacturer": "Edge TTS Community",
            "model": "Cloud TTS",
            "sw_version": edge_tts.__version__,
            "entry_type": DeviceEntryType.SERVICE,
        }
        self._attr_extra_state_attributes = {}

    async def async_added_to_hass(self) -> None:
        domain_data = self.hass.data.setdefault(DOMAIN, {})
        domain_data["tts_entity_id"] = self.entity_id
        access_tokens = domain_data.setdefault(
            "access_tokens",
            {
                "temp": ulid.ulid_hex(),
                "long": self.hass.data["core.uuid"],
            },
        )
        self._attr_extra_state_attributes["access_tokens"] = access_tokens.copy()

        # Warm the voice catalogue so the voice picker is populated. Failures
        # degrade to the bundled snapshot inside async_get_voice_catalog.
        await async_get_voice_catalog(self.hass)

    @property
    def default_language(self) -> str:
        """Return the default language from options."""
        return self._config_entry.options.get(CONF_LANG, DEFAULT_LANG)

    @property
    def supported_languages(self) -> list[str]:
        """Return supported languages: locales plus raw voice names."""
        catalog = cached_catalog(self.hass)
        locales = sorted({entry["locale"] for entry in catalog})
        names = sorted(entry["short_name"] for entry in catalog)
        return [*locales, *names]

    @property
    def supported_options(self) -> list[str]:
        """Return a list of supported per-request options."""
        return [CONF_VOICE, CONF_PITCH, CONF_RATE, CONF_VOLUME]

    @callback
    def async_get_supported_voices(self, language: str) -> list[Voice] | None:
        """Return the voices selectable for a language in the HA UI."""
        catalog = cached_catalog(self.hass)
        matches = [entry for entry in catalog if entry["locale"] == language]
        if not matches:
            # ``language`` may itself be a raw voice name; offer its siblings.
            selected = next((e for e in catalog if e["short_name"] == language), None)
            if selected is not None:
                matches = [e for e in catalog if e["locale"] == selected["locale"]]
        if not matches:
            return None
        matches.sort(key=lambda entry: entry["short_name"])
        return [Voice(entry["short_name"], voice_label(entry)) for entry in matches]

    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        return "mp3", await self.async_process_tts_audio(message, language, options)

    async def async_process_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> bytes | None:
        try:
            audio, trace = await self.hass.async_add_executor_job(
                self._process_tts_audio,
                message,
                language,
                options,
            )
        except _SynthesisError as err:
            self._record_synthesis_trace(err.trace)
            raise
        self._record_synthesis_trace(trace)
        return audio

    def _process_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> tuple[bytes | None, dict[str, Any]]:
        opt = {CONF_LANG: language}
        if language in SUPPORTED_VOICES:
            opt[CONF_LANG] = SUPPORTED_VOICES[language]
            opt[CONF_VOICE] = language
        opt = {**self._config_entry.options, **opt, **(options or {})}

        lang = opt.get(CONF_LANG) or language or DEFAULT_LANG
        voice = opt.get(CONF_VOICE) or SUPPORTED_LANGUAGES.get(lang) or DEFAULT_VOICE
        pitch = _as_edge_value(opt.get(CONF_PITCH, DEFAULT_PITCH), "Hz")
        rate = _as_edge_value(opt.get(CONF_RATE, DEFAULT_RATE), "%")
        volume = _as_edge_value(opt.get(CONF_VOLUME, DEFAULT_VOLUME), "%")

        for field in _STYLE_OPTIONS:
            if field in opt:
                _LOGGER.warning(
                    "Edge TTS options style/styledegree/role are no longer supported, "
                    "please remove them from your automation or script. "
                    "See: https://github.com/hasscc/hass-edge-tts/issues/8"
                )
                break

        _LOGGER.debug("%s: %s", self.name, [message, opt])
        mp3 = b""
        start_time = time.perf_counter()
        audio_chunks = 0
        metadata_chunks = 0
        tts = edge_tts.Communicate(
            message,
            voice=voice,
            pitch=pitch,
            rate=rate,
            volume=volume,
        )
        try:
            for chunk in tts.stream_sync():
                if chunk["type"] == "audio":
                    mp3 += chunk["data"]
                    audio_chunks += 1
                else:
                    metadata_chunks += 1
                    _LOGGER.debug("Edge TTS metadata: %s", chunk)
        except edge_tts.exceptions.NoAudioReceived as exc:
            trace = _synthesis_trace(
                status="error",
                started_at=start_time,
                message=message,
                language=lang,
                requested_language=language,
                voice=voice,
                pitch=pitch,
                rate=rate,
                volume=volume,
                audio_bytes=len(mp3),
                audio_chunks=audio_chunks,
                metadata_chunks=metadata_chunks,
                error_type=type(exc).__name__,
                error_phase="stream",
            )
            _LOGGER.warning("No audio received for text: %s", message)
            raise _SynthesisError(
                f"{self.name}: No audio received: {message}", trace
            ) from exc
        end_time = time.perf_counter()
        elapsed_time = (end_time - start_time) * 1000
        _LOGGER.debug("load tts elapsed_time: %sms", elapsed_time)
        trace = _synthesis_trace(
            status="ok",
            started_at=start_time,
            message=message,
            language=lang,
            requested_language=language,
            voice=voice,
            pitch=pitch,
            rate=rate,
            volume=volume,
            audio_bytes=len(mp3),
            audio_chunks=audio_chunks,
            metadata_chunks=metadata_chunks,
        )
        return mp3, trace

    def _record_synthesis_trace(self, trace: dict[str, Any]) -> None:
        """Publish the latest synthesis trace to entity attributes and hass data."""
        domain_data = self.hass.data.setdefault(DOMAIN, {})
        domain_data[DATA_LAST_SYNTHESIS_TRACE] = dict(trace)
        self._attr_extra_state_attributes[DATA_LAST_SYNTHESIS_TRACE] = dict(trace)
        if self.entity_id:
            with contextlib.suppress(RuntimeError):
                self.async_write_ha_state()

    async def async_stream_tts_audio(
        self, request: TTSAudioRequest
    ) -> TTSAudioResponse:
        return TTSAudioResponse("mp3", self._process_tts_stream(request))

    async def _process_tts_stream(
        self, request: TTSAudioRequest
    ) -> AsyncGenerator[bytes]:
        """Generate speech from an incoming message."""
        _LOGGER.debug("Starting TTS Stream with options: %s", request.options)
        separators = [
            "\n",
            "。",
            ". ",
            "，",
            ", ",
            "；",
            "; ",
            "！",
            "! ",
            "？",
            "? ",
            "、",
        ]
        buffer = ""
        count = 0
        async for message in request.message_gen:
            _LOGGER.debug("Streaming tts sentence: %s", message)
            count += 1
            min_len = 2**count * 10
            for char in message:
                buffer += char
                msg = buffer.strip()
                if len(msg) < min_len:
                    continue
                if char in separators or buffer[-2:] in separators:
                    buffer = ""
                    yield await self.async_process_tts_audio(
                        msg, request.language, request.options
                    )
        if msg := buffer.strip():
            yield await self.async_process_tts_audio(
                msg, request.language, request.options
            )


def _synthesis_trace(  # noqa: PLR0913 - trace fields mirror the public diagnostic schema.
    *,
    status: str,
    started_at: float,
    message: str,
    language: str,
    requested_language: str,
    voice: str,
    pitch: str,
    rate: str,
    volume: str,
    audio_bytes: int,
    audio_chunks: int,
    metadata_chunks: int,
    error_type: str = "",
    error_phase: str = "",
) -> dict[str, Any]:
    """Return a bounded TTS synthesis trace without retaining spoken text."""
    elapsed_ms = round((time.perf_counter() - started_at) * 1000)
    trace: dict[str, Any] = {
        "schema_version": TTS_SYNTHESIS_TRACE_SCHEMA_VERSION,
        "generated_at": dt.datetime.now(tz=dt.UTC).isoformat(),
        "status": status,
        "provider": "edge-tts",
        "requested_language": requested_language,
        "language": language,
        "voice": voice,
        "prosody": {
            "pitch": pitch,
            "rate": rate,
            "volume": volume,
        },
        "message_chars": len(message),
        "audio_format": "mp3",
        "audio_bytes": audio_bytes,
        "audio_chunks": audio_chunks,
        "metadata_chunks": metadata_chunks,
        "elapsed_ms": elapsed_ms,
    }
    if error_type:
        trace["error_type"] = error_type
    if error_phase:
        trace["error_phase"] = error_phase
    return trace
