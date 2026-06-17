"""Tests for the static voice/language tables in const.py.

These run without Home Assistant installed, so they stay fast and act as a
guard against accidental corruption of the large VOICES table.
"""

from custom_components.edge_tts import const


def test_domain_is_edge_tts() -> None:
    assert const.DOMAIN == "edge_tts"


def test_default_voice_and_language_are_consistent() -> None:
    # The default voice must exist in the table and map to the default language.
    assert const.DEFAULT_VOICE in const.SUPPORTED_VOICES
    assert const.SUPPORTED_VOICES[const.DEFAULT_VOICE] == const.DEFAULT_LANG


def test_supported_voices_table_is_well_formed() -> None:
    assert isinstance(const.SUPPORTED_VOICES, dict)
    assert len(const.SUPPORTED_VOICES) > 100  # Microsoft ships hundreds of voices.
    for voice, language in const.SUPPORTED_VOICES.items():
        assert isinstance(voice, str)
        assert voice
        assert isinstance(language, str)
        assert language
        # Voice names are conventionally "<locale>-<Name>Neural".
        assert voice.startswith(language), (voice, language)


def test_voices_catalogue_structure() -> None:
    assert isinstance(const.VOICES, dict)
    assert len(const.VOICES) > 300  # The bundled snapshot is the full catalogue.
    for short_name, meta in const.VOICES.items():
        assert isinstance(meta, tuple)
        assert len(meta) == 2
        locale, gender = meta
        assert short_name.startswith(locale), (short_name, locale)
        assert gender in ("Female", "Male", "")


def test_supported_voices_is_derived_from_catalogue() -> None:
    expected = {name: meta[0] for name, meta in const.VOICES.items()}
    assert expected == const.SUPPORTED_VOICES
