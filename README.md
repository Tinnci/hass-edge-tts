# Microsoft Edge TTS for Home Assistant

[English](README.md) | [简体中文](README.zh-Hans.md)

[![CI](https://github.com/Tinnci/hass-edge-tts/actions/workflows/ci.yml/badge.svg)](https://github.com/Tinnci/hass-edge-tts/actions/workflows/ci.yml)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://www.hacs.xyz/docs/faq/custom_repositories/)

Use Microsoft Edge voices as a Home Assistant text-to-speech engine.

The integration does not require an Azure application key. It supports Home
Assistant config entries, `tts.speak`, live voice discovery, and private
diagnostics.

This repository maintains the user interface of
[`hasscc/hass-edge-tts`](https://github.com/hasscc/hass-edge-tts). It also adds
current Home Assistant support, tests, lint rules, and continuous integration.

> [!IMPORTANT]
> Microsoft can change or restrict the Edge speech service without notice.
> Do not use this unofficial integration for a critical speech path.

## Features

- Home Assistant config flow and options flow
- A TTS entity for `tts.speak` and `/api/tts_get_url`
- Live Microsoft voice catalogue retrieval
- A bundled 322-voice catalogue when the live request fails
- Voice selection in the Home Assistant user interface
- `edge_tts.list_voices` with language and gender filters
- Default and per-call rate, pitch, volume, and voice settings
- Numeric prosody conversion, such as `rate: 10` to `+10%`
- A legacy direct proxy endpoint for existing clients

The integration does not support `style`, `styledegree`, `role`, or `contour`.

## Diagnostics and privacy

Home Assistant can download config-entry diagnostics for this integration.
The System Health page also shows a small operational summary.

The diagnostic data includes:

- the integration version,
- the voice catalogue source and size,
- configured locale and prosody settings,
- the latest synthesis status and duration,
- audio byte and chunk counts,
- the failure phase when synthesis fails.

The data does not include spoken text, proxy tokens, or the full voice
catalogue. The latest synthesis trace records only the message character count.

The TTS entity exposes the same bounded trace in the
`last_synthesis_trace` attribute. Home Assistant also stores it in
`hass.data["edge_tts"]` for local diagnostics.

## Installation

### HACS

[![Install repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tinnci&repository=hass-edge-tts&category=integration)

1. Open HACS.
2. Add `https://github.com/Tinnci/hass-edge-tts` as a custom integration repository.
3. Install **Microsoft Edge TTS**.
4. Restart Home Assistant.
5. Add the integration from **Settings > Devices & services**.

### Manual installation

1. Copy `custom_components/edge_tts` to `<ha-config>/custom_components/edge_tts`.
2. Restart Home Assistant.
3. Add the integration from **Settings > Devices & services**.

## Configuration

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=edge_tts)

The options flow stores these defaults:

- language,
- voice,
- speech rate,
- pitch,
- volume.

A service call can override each default.

## Voice catalogue

The integration requests the current voice catalogue during startup. It uses
the bundled catalogue if Microsoft is not available. This fallback keeps the
integration and voice picker available.

List Chinese voices:

```yaml
action: edge_tts.list_voices
data:
  language: zh
response_variable: voices
```

The `language` filter accepts a locale prefix such as `zh`, `zh-CN`, or `en`.
The `gender` filter accepts `Female` or `Male`.

Refresh the bundled catalogue after Microsoft adds voices:

```bash
uv run python scripts/refresh_voices.py
```

## Usage

### Speak with one voice

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player
  message: 欢迎回家
  language: zh-CN-XiaoyiNeural
```

### Override prosody

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

## Runtime boundary

This integration only synthesizes speech. It does not control satellite volume,
microphone gain, wake-word sensitivity, audio routing, echo cancellation, or
local fallback clips. The satellite runtime must own those functions.

## Development

Use `uv` for the Python environment.

```bash
uv sync --dev
uv run pytest
uvx ruff check .
uvx ruff format --check .
git diff --check
```

Tests cover setup, voice lookup, catalogue fallback, prosody conversion, audio
streaming, diagnostics, and System Health.

## Security

- Do not put Home Assistant access tokens in issues.
- Do not publish spoken household text in logs or screenshots.
- Download Home Assistant diagnostics before you report a synthesis defect.

## Credits

The original integration was created by
[@al-one](https://github.com/al-one), [@rany2](https://github.com/rany2), and
[@dscao](https://github.com/dscao).

See also:

- [`rany2/edge-tts`](https://github.com/rany2/edge-tts)
- [`hasscc/hass-edge-tts`](https://github.com/hasscc/hass-edge-tts)
- [Home Assistant TTS](https://www.home-assistant.io/integrations/tts/)

## Documentation style

This README applies practical rules from ASD-STE100 Simplified Technical
English, Issue 9. It uses active voice, short sentences, and consistent terms.

This use is not an ASD-STE100 compliance certification. Project-specific terms
remain necessary.

Reference: ASD STEMG. [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/), Issue 9, 2025.

## License

This source is available for non-commercial use under the
[PolyForm Noncommercial License 1.0.0](LICENSE).

Commercial use requires a separate license. This license is not an OSI
open-source license. Upstream-derived files keep their original notices and
terms. See [NOTICE.md](NOTICE.md).
