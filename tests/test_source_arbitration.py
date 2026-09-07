"""Issue #24: real foreground changes and the exact source-loss deadline."""
import bms_const as C
import bms_logic as L
import pytest


@pytest.mark.parametrize("playback", ["paused", "idle"])
def test_movie_pause_requires_existing_stream_and_active_apple_foreground(playback):
    source = L.ForegroundSource()
    source.update(True, False, "Apple OTT", 0)
    assert L.decide(L.Inputs(atv_state="playing", foreground=source.current)).context == C.CTX_STREAMING
    assert L.decide(L.Inputs(atv_state=playback, foreground=source.current, streaming_confirmed=True)).context == C.CTX_STREAMING
    source.update(False, True, "Apple OTT", 1)
    result = L.decide(L.Inputs(atv_state=playback, foreground=source.current, streaming_confirmed=True))
    assert result.context == C.CTX_IDLE
    assert result.device != C.DEV_APPLETV
    assert source.diagnostics(1)["grace_active"] is False


@pytest.mark.parametrize("playback", ["paused", "idle"])
def test_pause_is_not_a_new_streaming_session(playback):
    assert L.decide(L.Inputs(atv_state=playback, foreground=C.DEV_APPLETV)).context == C.CTX_IDLE


def test_playing_during_cold_start_and_even_without_source_is_fast_path():
    assert L.decide(L.Inputs(atv_state="playing", tv_active=False)).context == C.CTX_STREAMING


@pytest.mark.parametrize("playback", ["paused", "idle", "playing"])
def test_ps5_foreground_wins_even_before_ps5_player_reports_on(playback):
    source = L.ForegroundSource()
    source.update(True, False, "Apple OTT", 0)
    source.update(True, False, "PlayStation 5", 1)
    state = L.decide(L.Inputs(atv_state=playback, foreground=source.current, streaming_confirmed=True))
    assert (state.context, state.device, state.subcontext) == (C.CTX_GAMING, C.DEV_PS5, C.SUB_GAME_GRIND)
    assert source.reason == "source_changed"


def test_dropout_five_seconds_from_loss_not_last_report_or_each_compute():
    source = L.ForegroundSource()
    source.update(True, False, "Apple OTT", 0)
    source.update(True, False, None, 100)
    for now in [100, 102, 104.999]:
        source.update(True, False, "unavailable", now)
        assert source.current == C.DEV_APPLETV
        assert source.diagnostics(now)["grace_active"]
        assert source.lost_at == 100
    source.update(True, False, None, 105)
    assert source.current is None
    assert source.diagnostics(105)["grace_expired"]
    assert source.diagnostics(105)["grace_remaining_seconds"] == 0
    result = L.decide(L.Inputs(tv_active=True, atv_state="paused", foreground=source.current, streaming_confirmed=True))
    assert result.context == C.CTX_TV
    source.update(True, False, None, 200)
    assert source.current is None


@pytest.mark.parametrize("replacement, expected, reason", [("Apple OTT", C.DEV_APPLETV, "source_recovered"), ("PlayStation 5", C.DEV_PS5, "source_changed")])
def test_source_returns_during_grace(replacement, expected, reason):
    source = L.ForegroundSource()
    source.update(True, False, "Apple OTT", 0)
    source.update(True, False, None, 1)
    source.update(True, False, replacement, 3)
    assert source.current == expected and source.reason == reason
    assert source.lost_at is None
    assert not source.diagnostics(3)["grace_active"]


@pytest.mark.parametrize("tv_active, tv_off, source_value", [(False, False, None), (True, True, None), (True, False, "unrecognized HDMI")])
def test_grace_never_masks_loss_of_confirmed_tv_or_unrecognized_source(tv_active, tv_off, source_value):
    source = L.ForegroundSource()
    source.update(True, False, "Apple OTT", 0)
    source.update(tv_active, tv_off, source_value, 1)
    assert source.current is None
    source.update(True, False, None, 2)
    assert source.current is None  # no resurrection after off/invalid source


def test_no_source_history_cannot_start_grace():
    source = L.ForegroundSource()
    source.update(True, False, None, 0)
    assert source.current is None and source.lost_at is None


def test_preemptible_enum_keeps_existing_grind_contract_and_returns_after_stream():
    inputs = dict(ps5_on=True, ps5_raw="background game", ps5_enum=3)
    grind = L.decide(L.Inputs(**inputs))
    assert grind.subcontext == C.SUB_GAME_GRIND
    streaming = L.decide(L.Inputs(**inputs, atv_state="playing", foreground=C.DEV_APPLETV))
    assert streaming.context == C.CTX_STREAMING
    returned = L.decide(L.Inputs(**inputs, atv_state="off", foreground=C.DEV_PS5))
    assert returned.device == C.DEV_PS5 and returned.subcontext == C.SUB_GAME_GRIND


def test_private_and_away_still_beat_foreground():
    source = dict(foreground=C.DEV_PS5, atv_state="playing")
    assert L.decide(L.Inputs(**source, pc_active=True, private_manual=True)).context == C.CTX_PRIVATE
    assert L.decide(L.Inputs(**source, away_gated=True)).context == C.CTX_IDLE
