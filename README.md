# Microsoft Edge TTS for Home Assistant

This component is based on the TTS service of Microsoft Edge browser, no need to apply for `app_key`.

> [!NOTE]
> This is a maintained fork of [`hasscc/hass-edge-tts`](https://github.com/hasscc/hass-edge-tts) by [@Tinnci](https://github.com/Tinnci),
> adding quality tooling: Ruff lint/format, pre-commit, a pytest suite that loads the integration in a real Home Assistant, and CI gates.
> All credit for the original integration goes to [@al-one](https://github.com/al-one), [@rany2](https://github.com/rany2) and [@dscao](https://github.com/dscao).


## Install

[![Install repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tinnci&repository=hass-edge-tts&category=integration)

> Download and copy `custom_components/edge_tts` folder to `custom_components` folder in your HomeAssistant config folder

```shell
# Auto install via terminal shell
wget -O - https://hacs.vip/get | DOMAIN=edge_tts REPO_PATH=Tinnci/hass-edge-tts ARCHIVE_TAG=main bash -
```


## Config

[UI: config - integrations - add integration - Microsoft Edge TTS ]

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=edge_tts)

add integration \
<img width="500" height="300" alt="add integration" src="https://github.com/user-attachments/assets/3a4f3a30-bcd1-447e-8044-36c2bc3f78b0" />
 \
config option \
<img width="500" height="300" alt="config option" src="https://github.com/user-attachments/assets/0cadaf9e-d316-49b9-b28d-f1a8f7e7551c" />
 \
entity \
<img width="500" height="300" alt="entity" src="https://github.com/user-attachments/assets/42e8a6d7-c5e7-4f8f-9093-d93ca678ce87" />
 \
call service \
<img width="500" height="300" alt="call service" src="https://github.com/user-attachments/assets/fa353f2d-623b-460b-8fa4-0cbbc233f073" />


#### Voices

All voices Microsoft offers (300+) are supported. The list is fetched live from
Microsoft at startup, so newly released voices appear automatically; a bundled
snapshot is used as an offline fallback.

- In the UI, the **voice** picker for a language is populated automatically
  (Assist pipeline and the `tts.speak` action).
- To enumerate every voice with locale / gender / style metadata, call the
  [`edge_tts.list_voices`](https://my.home-assistant.io/redirect/developer_call_service/?service=edge_tts.list_voices)
  action (returns response data). Optional filters: `language` (locale prefix,
  e.g. `zh` or `zh-CN`) and `gender` (`Female` / `Male`).

```yaml
action: edge_tts.list_voices
data:
  language: zh
response_variable: voices
```

- Regenerate the bundled snapshot after Microsoft ships new voices:
  `uv run python scripts/refresh_voices.py`
- [Reference list of voices](https://github.com/Tinnci/hass-edge-tts/blob/main/custom_components/edge_tts/const.py)



## Using

- [![Call service: tts.speak](https://my.home-assistant.io/badges/developer_call_service.svg)](https://my.home-assistant.io/redirect/developer_call_service/?service=tts.speak)
- [REST API: /api/tts_get_url](https://www.home-assistant.io/integrations/tts#post-apitts_get_url)


### Options

- [`voice`](https://docs.microsoft.com/zh-CN/azure/cognitive-services/speech-service/speech-synthesis-markup?tabs=csharp#use-multiple-voices)
- [`pitch` / `rate` / `volume`](https://docs.microsoft.com/zh-CN/azure/cognitive-services/speech-service/speech-synthesis-markup?tabs=csharp#adjust-prosody)

Per call, prosody accepts either signed strings (`rate: +10%`, `pitch: -5Hz`,
`volume: +10%`) or plain integers (`rate: 10`, `pitch: -5`, `volume: 10`),
which are converted automatically.

Default `voice`, `rate`, `pitch` and `volume` can also be set once in the
integration's **Configure** (options) dialog; per-call options always override
those defaults.

> `style` / `styledegree` / `role` / `contour` are no longer supported ([#8](https://github.com/hasscc/hass-edge-tts/issues/8)).

### Basic example

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player_entity_id
  message: Hello
  language: zh-CN-XiaoyiNeural # Language or voice (Optional)
```

### Full example

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player_entity_id
  message: 吃葡萄不吐葡萄皮，不吃葡萄倒吐葡萄皮
  language: zh-CN
  cache: true
  options:
    voice: zh-CN-XiaoyiNeural
    rate: +0%
    volume: +10%
```

### More examples

```shell
curl -X POST -H "Authorization: Bearer <ACCESS TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"engine_id": "tts.edge_tts", "message": "欢迎回家", "language": "zh-CN-XiaoyiNeural", "cache": true, "options": {"volume": "+10%"}}' \
     http://homeassistant.local:8123/api/tts_get_url
```

```shell
curl -o hello.mp3 'http://homeassistant.local:8123/api/tts_proxy/edge?rate=+20%&message=hello&token=<tts_token>'
```
> The `tts_token` can be found in the tts entity attributes.


## Links

- https://github.com/rany2/edge-tts
- https://www.skills.sh/aahl/skills/edge-tts
- https://github.com/ag2s20150909/TTS
