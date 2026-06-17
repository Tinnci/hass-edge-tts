"""Regenerate the bundled voice catalogue in ``const.py`` from Microsoft's list.

The integration fetches the live voice list at runtime, but ships a static
catalogue as an offline fallback and as the basis for the tests. Run this after
Microsoft adds or removes voices::

    uv run python scripts/refresh_voices.py

It rewrites only the block between the GENERATED VOICES markers, leaving the
rest of ``const.py`` untouched.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

CONST_PATH = (
    Path(__file__).resolve().parent.parent
    / "custom_components"
    / "edge_tts"
    / "const.py"
)
BEGIN = "# --- BEGIN GENERATED VOICES"
END = "# --- END GENERATED VOICES ---"


def _q(value: str) -> str:
    """Quote a string as a Python literal, escaping embedded quotes."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _build_block(voices: list[dict]) -> str:
    rows = []
    for voice in sorted(voices, key=lambda item: item["ShortName"]):
        short = voice["ShortName"]
        locale = voice["Locale"]
        if not short.startswith(locale):
            # The tests rely on this invariant; surface anything unexpected.
            raise ValueError(f"{short!r} does not start with locale {locale!r}")
        gender = voice.get("Gender", "")
        rows.append(f"    {_q(short)}: ({_q(locale)}, {_q(gender)}),")
    body = "\n".join(rows)
    return (
        f"{BEGIN} ({len(voices)} voices) ---\n"
        "VOICES: dict[str, tuple[str, str]] = {\n"
        "    # Each value is the voice's locale and gender.\n"
        f"{body}\n"
        "}\n"
        f"{END}"
    )


def main() -> None:
    voices = asyncio.run(edge_tts.list_voices())
    block = _build_block(voices)

    text = CONST_PATH.read_text(encoding="utf-8")
    start = text.index(BEGIN)
    end_marker = text.index(END)
    line_end = text.index("\n", end_marker)
    new_text = text[:start] + block + text[line_end:]
    CONST_PATH.write_text(new_text, encoding="utf-8")
    print(f"Wrote {len(voices)} voices to {CONST_PATH}")


if __name__ == "__main__":
    main()
