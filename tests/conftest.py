"""Shared fixtures for the Edge TTS integration tests."""

from collections.abc import Iterator
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.edge_tts.const import VOICES

pytest_plugins = ["pytest_homeassistant_custom_component"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the edge_tts custom integration in every test."""


def _fake_live_voices() -> list[dict]:
    """Recreate the live ``edge_tts.list_voices`` payload from the snapshot."""
    fake = []
    for short_name, (locale, gender) in VOICES.items():
        fake.append(
            {
                "ShortName": short_name,
                "Locale": locale,
                "Gender": gender,
                "VoiceTag": {
                    "ContentCategories": ["General"],
                    "VoicePersonalities": ["Friendly", "Positive"],
                },
            }
        )
    return fake


@pytest.fixture(autouse=True)
def mock_list_voices() -> Iterator[AsyncMock]:
    """Patch the network call so tests never hit Microsoft's endpoint.

    Returns the bundled catalogue reshaped as a live payload; individual tests
    can override ``return_value``/``side_effect`` to exercise other paths.
    """
    with patch(
        "custom_components.edge_tts.voices.edge_tts.list_voices",
        new_callable=AsyncMock,
    ) as mock:
        mock.return_value = _fake_live_voices()
        yield mock
