"""Tests für den Activity-Context-Feed (FLEET-255).

Additiver Media-Activity-Feed für core_state (`derive_activity_context`). Prüft:
- Audio-only bleibt `media_context` idle, aber `activity_context` = music.
- Denon/HomePods → music; Gaming/Entertainment/Private mappen korrekt.
- Feed-Priorität: private_time > gaming > entertainment > music > idle.
- Reiche private-time-Erkennung (Stash-Streams/-Enum/Manual) wird genutzt.
- Kein Rückgriff auf core_state `activity_state` / `presence_effective`.
- Bestehende media_context-/entertainment_active-Semantik unverändert.
"""
from __future__ import annotations

import ast
import inspect
import textwrap

import bms_const as C
import bms_logic as L


def _code_without_docstring(fn) -> str:
    """Quelltext einer Funktion ohne ihren Docstring (nur echte Code-Zeilen)."""
    tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
    func = tree.body[0]
    if (
        func.body
        and isinstance(func.body[0], ast.Expr)
        and isinstance(func.body[0].value, ast.Constant)
    ):
        func.body = func.body[1:]
    return ast.unparse(func)


def _inp(**kw):
    return L.Inputs(**kw)


def _feed(**kw):
    """decide() → derive_activity_context() end-to-end (nutzt echte Ableitung)."""
    inp = _inp(**kw)
    state = L.decide(inp)
    return state, L.derive_activity_context(state, inp)


# ------------------------------------------------------ Audio-only: idle→music


def test_homepods_audio_only_media_context_idle_feed_music():
    state, ac = _feed(homepods_playing=True)
    # Regression: media_context bleibt bewusst idle (audio_only_idle).
    assert state.context == C.CTX_IDLE
    assert "audio_only_idle" in state.active_reasons
    assert state.entertainment_active is False
    # Feed surfacet dasselbe Audio als music.
    assert ac.state == C.ACTX_MUSIC
    assert ac.hold_strength == C.HOLD_SOFT
    assert ac.reason == "music:homepods"
    assert ac.attrs["music_active"] is True
    assert ac.attrs["media_context"] == C.CTX_IDLE
    assert ac.attrs["homepods_playing"] is True


def test_denon_audio_only_media_context_idle_feed_music():
    state, ac = _feed(denon_active=True)
    assert state.context == C.CTX_IDLE
    assert ac.state == C.ACTX_MUSIC
    assert ac.reason == "music:denon"
    assert ac.attrs["denon_active"] is True


# ------------------------------------------------------------------- Gaming


def test_ps5_gaming_feed_gaming():
    state, ac = _feed(ps5_on=True, ps5_raw="Elden Ring")
    assert state.context == C.CTX_GAMING
    assert ac.state == C.ACTX_GAMING
    assert ac.hold_strength == C.HOLD_HARD
    assert ac.attrs["gaming_platform"] == C.GP_PS5


def test_pc_gaming_feed_gaming():
    # PC-Gaming nur über Titel-Ebene (B2-Gate) — kein neuer Pfad im Feed.
    state, ac = _feed(pc_active=True, pc_raw="Factorio")
    assert state.context == C.CTX_GAMING
    assert ac.state == C.ACTX_GAMING


# -------------------------------------------------------------- Entertainment


def test_tv_feed_entertainment():
    state, ac = _feed(tv_active=True)
    assert state.context == C.CTX_TV
    assert ac.state == C.ACTX_ENTERTAINMENT
    assert ac.hold_strength == C.HOLD_SOFT
    assert ac.attrs["entertainment_active"] is True


def test_streaming_feed_entertainment():
    state, ac = _feed(atv_state="playing", atv_app_id="com.netflix.Netflix")
    assert state.context == C.CTX_STREAMING
    assert ac.state == C.ACTX_ENTERTAINMENT


# ------------------------------------------------ Private Time (reiche Trigger)


def test_private_stash_streams_feed_private():
    # control#3: auto-Private braucht Classifier ∧ PC ∧ Denon.
    state, ac = _feed(stash_streams=2, pc_active=True, denon_active=True)
    assert state.context == C.CTX_PRIVATE
    assert ac.state == C.ACTX_PRIVATE
    assert ac.hold_strength == C.HOLD_HARD
    assert ac.attrs["private_time_active"] is True
    assert ac.reason == "private:auto:classifier+pc+denon"


def test_private_stash_enum_feed_private():
    state, ac = _feed(stash_enum=1, pc_active=True, denon_active=True)
    assert state.context == C.CTX_PRIVATE
    assert ac.state == C.ACTX_PRIVATE
    assert ac.reason == "private:auto:classifier+pc+denon"


def test_private_manual_switch_feed_private():
    # Headset-Override: manueller Schalter ∧ PC (kein Denon nötig).
    state, ac = _feed(private_manual=True, pc_active=True)
    assert state.context == C.CTX_PRIVATE
    assert ac.state == C.ACTX_PRIVATE
    assert ac.reason == "private:manual:switch+pc"


# --------------------------------------------------------------- Feed-Priorität


def test_priority_private_over_gaming():
    _, ac = _feed(
        stash_streams=1, pc_active=True, denon_active=True,
        ps5_on=True, ps5_raw="Doom",
    )
    assert ac.state == C.ACTX_PRIVATE


def test_priority_gaming_over_music():
    _, ac = _feed(ps5_on=True, ps5_raw="Doom", homepods_playing=True)
    assert ac.state == C.ACTX_GAMING


def test_priority_entertainment_over_music():
    _, ac = _feed(tv_active=True, denon_active=True)
    assert ac.state == C.ACTX_ENTERTAINMENT


def test_idle_when_no_signals():
    _, ac = _feed()
    assert ac.state == C.ACTX_IDLE
    assert ac.hold_strength == C.HOLD_NONE
    assert ac.attrs["music_active"] is False
    assert ac.attrs["private_time_active"] is False


# ---------------------------------------------------------------- Away-Gate


def test_away_gate_forces_idle_even_with_audio():
    # away_gate spiegelt media_context: bei Abwesenheit alles idle.
    inp = _inp(homepods_playing=True, away_raw=True, away_gated=True)
    state = L.decide(inp)
    assert state.away_gate is True
    assert state.context == C.CTX_IDLE
    ac = L.derive_activity_context(state, inp)
    assert ac.state == C.ACTX_IDLE
    assert ac.reason == "away_gate"
    assert ac.attrs["private_time_active"] is False


# --------------------------------------------------------- Zyklus-Freiheit


def test_feed_ignores_core_activity_state():
    # Derselbe Roh-Media-Input, unterschiedliche core_state activity_state →
    # identischer Feed. Beweist: Feed hängt nicht an core_state activity_state.
    _, ac_a = _feed(homepods_playing=True, activity_state="gaming")
    _, ac_b = _feed(homepods_playing=True, activity_state="sleep")
    assert ac_a.state == ac_b.state == C.ACTX_MUSIC


def test_inputs_has_no_presence_effective_field():
    # presence_effective ist strukturell nicht abbildbar → kein Zyklus möglich.
    assert "presence_effective" not in L.Inputs.__dataclass_fields__


def test_derive_source_has_no_forbidden_dependencies():
    # Nur den Code-Body prüfen (Docstring erklärt die verbotenen Deps in Prosa).
    body = _code_without_docstring(L.derive_activity_context)
    assert "presence_effective" not in body
    assert "activity_state" not in body
