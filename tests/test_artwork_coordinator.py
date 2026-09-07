"""Sanitized contracts observed on HA/MA on 2026-09-07 (#18)."""
import bms_const as C

from .test_source_coordinator import runtime as runtime  # noqa: F401


def test_observed_apple_music_proxy_is_available_before_classifier(runtime):
    coord, _, put, _ = runtime
    put(C.CONF_HOMEPODS_PLAYER, "playing", media_content_id="apple_music://track/example",
        entity_picture="http://192.0.2.1:8095/imageproxy/example?size=512&fmt=png",
        entity_picture_local="/api/media_player_proxy/media_player.example?cache=example")
    put(C.CONF_MEDIA_ENUM, "1", artwork="https://example.com/classifier.png")
    result = coord._artwork(C.CONF_HOMEPODS_PLAYER, C.CONF_MEDIA_ENUM, music_assistant=True)
    assert [c["source"] for c in result["artwork_candidates"]] == ["entity_picture", "entity_picture_local", "title_classifier"]
    assert result["artwork_candidates"][1]["url"].startswith("/api/media_player_proxy/")


def test_observed_radio_https_remains_first(runtime):
    coord, _, put, _ = runtime
    put(C.CONF_HOMEPODS_PLAYER, "playing", media_content_id="radiobrowser://example",
        entity_picture="https://example.com/radio.jpg",
        entity_picture_local="/api/media_player_proxy/media_player.example?cache=radio")
    result = coord._artwork(C.CONF_HOMEPODS_PLAYER, music_assistant=True)
    assert result["artwork_url"] == "https://example.com/radio.jpg"
    assert len(result["artwork_candidates"]) == 2


def test_existing_ma_priority_and_duplicate_removal(runtime):
    coord, _, put, _ = runtime
    put(C.CONF_HOMEPODS_PLAYER, "playing", media_image_url="https://example.com/ma.jpg",
        entity_picture="/api/media_player_proxy/media_player.example",
        entity_picture_local="/api/media_player_proxy/media_player.example")
    result = coord._artwork(C.CONF_HOMEPODS_PLAYER, music_assistant=True)
    assert [c["source"] for c in result["artwork_candidates"]] == ["music_assistant", "entity_picture"]


def test_no_artwork_does_not_invent_a_proxy(runtime):
    coord, _, put, _ = runtime
    put(C.CONF_HOMEPODS_PLAYER, "playing")
    assert coord._artwork(C.CONF_HOMEPODS_PLAYER, music_assistant=True) == {"artwork_url": None, "artwork_candidates": []}
