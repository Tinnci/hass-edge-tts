# Microsoft Edge TTS for Home Assistant

[English](README.md) | [简体中文](README.zh-Hans.md)

这是一个 Home Assistant 自定义集成，把 Microsoft Edge 免费文字转语音服务暴露为 Home Assistant TTS 引擎，不需要 Azure 应用密钥。

本仓库是 [`hasscc/hass-edge-tts`](https://github.com/hasscc/hass-edge-tts) 的维护分支，由 [@Tinnci](https://github.com/Tinnci) 维护。它保留原集成的用户使用方式，同时补上当前 Home Assistant 兼容性、config/options flow、实时音色目录、测试、lint 和 CI。

原始集成作者包括 [@al-one](https://github.com/al-one)、[@rany2](https://github.com/rany2) 和 [@dscao](https://github.com/dscao)。

本维护发行版以 PolyForm Noncommercial License 1.0.0 提供源码，可用于非商业用途。来自上游的部分仍保留原始声明和许可证条款；详见 `NOTICE.md`。

## 当前能力

- Home Assistant config flow 和 options flow。
- 兼容 `tts.speak` 和 `/api/tts_get_url` 的 TTS entity。
- 启动时拉取 Microsoft 实时音色目录。
- 内置 322 个音色快照，网络不可用时作为 fallback。
- Home Assistant UI 中可选择音色。
- `edge_tts.list_voices` 服务支持 `language` 和 `gender` 过滤。
- 支持默认和单次调用的 prosody 参数：
  - `voice`
  - `rate`
  - `pitch`
  - `volume`
- 数值 prosody 会自动归一化，例如 `rate: 10` 转成 `+10%`。
- 保留 legacy HTTP proxy helper。
- 测试套件会在真实 Home Assistant 测试 harness 中加载自定义集成。

`style`、`styledegree`、`role` 和 `contour` 目前刻意不支持。

## 安装

### HACS 自定义仓库

[![Install repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Tinnci&repository=hass-edge-tts&category=integration)

1. 在 HACS 中添加 `https://github.com/Tinnci/hass-edge-tts` 作为自定义仓库。
2. 安装 `Microsoft Edge TTS`。
3. 重启 Home Assistant。
4. 在 Settings -> Devices & services 中添加集成。

### 手动安装

把：

```text
custom_components/edge_tts
```

复制到：

```text
<ha-config>/custom_components/edge_tts
```

然后重启 Home Assistant。

## 配置

[![Add Integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=edge_tts)

Options flow 会把默认合成设置保存在 config entry 上：

- 默认语言，
- 默认音色，
- 语速，
- 音调，
- 音量。

每次 `tts.speak` 调用传入的参数都会覆盖这些默认值。

## 音色目录

集成支持 `edge-tts` 暴露的所有 Microsoft 音色。启动时会尝试拉取实时目录；如果 Microsoft 不可达，会使用内置快照，因此集成仍能启动，音色选择器也仍可用。

在 Home Assistant 中列出音色：

```yaml
action: edge_tts.list_voices
data:
  language: zh
response_variable: voices
```

可选过滤：

- `language`：地区前缀，例如 `zh`、`zh-CN`、`en`、`ja`。
- `gender`：`Female` 或 `Male`。

Microsoft 发布新音色后，可重新生成内置快照：

```bash
uv run python scripts/refresh_voices.py
```

## 示例

### 基础 `tts.speak`

```yaml
action: tts.speak
target:
  entity_id: tts.edge_tts
data:
  media_player_entity_id: media_player.your_player
  message: 欢迎回家
  language: zh-CN-XiaoyiNeural
```

### 完整参数

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

## 开发

使用 `uv`：

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

测试覆盖：

- config flow 和 options flow，
- 支持的语言/音色查询，
- 实时音色目录 fallback，
- `edge_tts.list_voices`，
- prosody 参数归一化，
- 通过 `edge_tts.Communicate` 拉取 TTS 音频流。

## 语音助手部署说明

本集成只负责合成语音。它不控制 satellite 扬声器音量、唤醒词灵敏度、麦克风增益、OPUS 本地 fallback 片段或 TTS 播放门控。这些能力应该放在 `wyoming-satellite` 周边的 satellite runtime 中实现。

## 链接

- <https://github.com/rany2/edge-tts>
- <https://github.com/hasscc/hass-edge-tts>
- <https://www.home-assistant.io/integrations/tts/>

## 许可证

本维护发行版以 PolyForm Noncommercial License 1.0.0 提供源码，仅允许非商业用途。详见 `LICENSE`。

由于限制商业使用，它不是 OSI 开源许可证。商业使用需要获得维护者的单独授权。

来自上游的部分仍保留原始声明和许可证条款；详见 `NOTICE.md`。
