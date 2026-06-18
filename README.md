# Microsoft Edge TTS for Home Assistant

A Home Assistant custom integration that exposes Microsoft Edge's free TTS
service as a Home Assistant TTS engine. No Azure app key is required.

This repository is a maintained fork of
[`hasscc/hass-edge-tts`](https://github.com/hasscc/hass-edge-tts) by
[@Tinnci](https://github.com/Tinnci). It keeps the original integration's user
surface while adding current Home Assistant compatibility, a config/options
flow, live voice catalogue support, tests, linting, and CI.

All credit for the original integration goes to
[@al-one](https://github.com/al-one), [@rany2](https://github.com/rany2), and
[@dscao](https://github.com/dscao).

## Current capabilities

- Home Assistant config flow and options flow.
- TTS entity compatible with `tts.speak` and `/api/tts_get_url`.
- Live Microsoft voice catalogue fetch at startup.
- Bundled 322-voice snapshot as an offline fallback.
- Voice picker support in the Home Assistant UI.
- `edge_tts.list_voices` service with `language` and `gender` filters.
- Per-call and default prosody options:
  - `voice`
  - `rate`
  - `pitch`
  - `volume`
- Numeric prosody normalization, for example `rate: 10` -> `+10%`.
- Legacy direct proxy helper through the integration's HTTP view.
- Test suite that loads the custom integration in a real HA test harness.

`style`, `styledegree`, `role`, and `contour` are intentionally not supported.

## Install

### HACS custom repository

[![Install repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tinnci&repository=hass-edge-tts&category=integration)

1. Add `https://github.com/Tinnci/hass-edge-tts` as a HACS custom repository.
2. Install `Microsoft Edge TTS`.
3. Restart Home Assistant.
4. Add the integration from Settings -> Devices & services.

### Manual install

Copy:

```text
custom_components/edge_tts
```

to:

```text
<ha-config>/custom_components/edge_tts
```

Then restart Home Assistant.

## Configure

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=edge_tts)

The options flow stores default synthesis settings on the config entry:

- language,
- default voice,
- speech rate,
- pitch,
- volume.

Per-call options always override those defaults.

## Voice catalogue

All voices Microsoft exposes through `edge-tts` are supported. At startup the
integration tries to fetch the live catalogue. If Microsoft is unreachable, the
bundled snapshot is used so the integration still starts and the picker still
has voices.

List voices from Home Assistant:

```yaml
action: edge_tts.list_voices
data:
  language: zh
response_variable: voices
```

Optional filters:

- `language`: locale prefix such as `zh`, `zh-CN`, `en`, `ja`.
- `gender`: `Female` or `Male`.

Regenerate the bundled snapshot after Microsoft ships new voices:

```bash
uv run python scripts/refresh_voices.py
```

## Examples

### Basic `tts.speak`

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player
  message: 欢迎回家
  language: zh-CN-XiaoyiNeural
```

### Full options

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player
  message: 吃葡萄不吐葡萄皮，不吃葡萄倒吐葡萄皮
  language: zh-CN
  cache: true
  options:
    voice: zh-CN-XiaoyiNeural
    rate: +0%
    pitch: 0
    volume: +10%
```

### REST `tts_get_url`

```bash
curl -X POST \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"engine_id":"tts.edge_tts","message":"欢迎回家","language":"zh-CN-XiaoyiNeural","cache":true,"options":{"volume":"+10%"}}' \
  http://homeassistant.local:8123/api/tts_get_url
```

## Development

Use `uv`:

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

The tests cover:

- config flow and options flow,
- supported language/voice lookup,
- live catalogue fallback,
- `edge_tts.list_voices`,
- prosody normalization,
- TTS audio streaming from `edge_tts.Communicate`.

## Notes for voice assistant deployments

This integration only synthesizes speech. It does not control satellite speaker
volume, wakeword sensitivity, microphone gain, OPUS fallback clips, or TTS
playback gates. Those belong to the satellite runtime around
`wyoming-satellite`.

## Links

- <https://github.com/rany2/edge-tts>
- <https://github.com/hasscc/hass-edge-tts>
- <https://www.home-assistant.io/integrations/tts/>
