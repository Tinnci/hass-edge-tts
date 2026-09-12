# Releasing / 发布

The next planned version is **0.9.0**. The installed household component matches
the maintained source at `63f85ea`, including privacy-safe diagnostics added after
0.8.3. The version remains 0.8.3 in source until the Release workflow performs its
atomic version update.

Run `uv sync --locked --group dev`, `uv run pytest`, `uv run ruff check .` and
`uv run ruff format --check .`. After the reviewed commit is on `main`, run
**Release** from `main` with the `minor` bump. It reuses Validate before changing
versions, updates manifest/project/lock versions together, checks the result and
builds the ZIP before pushing the release commit and tag atomically.

`edge_tts.zip` has `manifest.json` at its root and is selected by `hacs.json`.
Its contents install directly under `/config/custom_components/edge_tts`.
The archive regression test executes the workflow's real packaging command with
local bytecode and Finder metadata present. Neither belongs in the published ZIP.

## HACS and branding / HACS 与品牌

This maintained distribution uses PolyForm Noncommercial with the upstream
notices retained. GitHub reports its license as `NOASSERTION`. HACS custom
validation therefore omits only the default-index license eligibility check;
all other checks, including brands, remain required. This is not a claim of
eligibility for the default HACS catalogue, and the license has not been changed.

`brand/icon.png` and `brand/icon@2x.png` are unchanged copies from
[Home Assistant Brands, edge_tts](https://github.com/home-assistant/brands/tree/master/custom_integrations/edge_tts).
They identify Microsoft Edge TTS and do not imply vendor endorsement.

本轮为自定义 HACS 仓库准备发布，不修改既有非商业许可证。默认目录的许可证资格
与安装兼容性分别说明；正式发布会重新运行当前提交的官方校验，服务合成测试不等于
扬声器已实际播报。
