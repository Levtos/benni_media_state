"""Presence-Gate (FLEET-212): Abwesenheit deaktiviert die Medienlogik.

Deckt die Akzeptanzkriterien ab:
1. home/zuhause/bei_eltern/on → anwesend (kein Gate).
2. away/abwesend/not_home → abwesend (Gate greift).
3. unknown/unavailable/None → nicht anwesend, aber KEIN Fehl-Stop.
4. Abwesenheit erzwingt idle/entertainment_active=False (stoppt Musik/Media).
"""
from __future__ import annotations

import bms_const as C
import bms_logic as L


def _inp(**kw):
    return L.Inputs(**kw)


# ---------------------------------------------------------- classify_presence


def test_home_states_are_present():
    for raw in ("zuhause", "home", "on", "true", "1", "present", "ZuHause"):
        assert L.classify_presence(raw) == C.PRES_HOME, raw


def test_away_states_are_absent():
    for raw in ("abwesend", "not_home", "not home", "off", "away", "0", "AbWeSend"):
        assert L.classify_presence(raw) == C.PRES_AWAY, raw


def test_bei_eltern_counts_as_home_equivalent():
    assert L.classify_presence("bei_eltern") == C.PRES_HOME


def test_unknown_states_are_not_present():
    for raw in (None, "", "unknown", "unavailable", "none", "voll_random"):
        assert L.classify_presence(raw) == C.PRES_UNKNOWN, raw


# ---------------------------------------------------------------- away gate


def test_away_forces_idle_and_stops_entertainment():
    # Musik läuft (HomePods) + TV an, aber Benni ist abwesend → harte
    # Deaktivierung: idle, entertainment_active=False, away_gate=True.
    d = L.decide(_inp(presence="abwesend", homepods_playing=True, tv_active=True))
    assert d.context == C.CTX_IDLE
    assert d.subcontext == C.SUB_NONE
    assert d.entertainment_active is False
    assert d.away_gate is True
    assert d.presence_state == C.PRES_AWAY
    assert d.presence_source == "abwesend"
    assert "away_gate" in d.active_reasons


def test_away_beats_gaming():
    # Presence-Gate hat Vorrang vor Gaming (höchste Priorität).
    d = L.decide(_inp(presence="abwesend", ps5_on=True, ps5_raw="Helldivers 2", ps5_enum=1))
    assert d.context == C.CTX_IDLE
    assert d.away_gate is True
    assert d.gaming_platform == C.GP_NONE
    assert d.headset_active is False


def test_away_beats_private_time():
    d = L.decide(_inp(presence="abwesend", stash_streams=2))
    assert d.context == C.CTX_IDLE
    assert d.away_gate is True


def test_bei_eltern_does_not_gate_media():
    d = L.decide(_inp(presence="bei_eltern", tv_active=True))
    assert d.context == C.CTX_TV
    assert d.away_gate is False
    assert d.presence_state == C.PRES_HOME
    assert d.presence_source == "bei_eltern"
    assert d.entertainment_active is True


def test_home_does_not_gate():
    d = L.decide(_inp(presence="zuhause", tv_active=True))
    assert d.away_gate is False
    assert d.presence_state == C.PRES_HOME
    assert d.context == C.CTX_TV
    assert d.entertainment_active is True


def test_unknown_presence_does_not_gate():
    # Defensive: unknown darf laufende Medien NICHT stoppen (Sensor-Aussetzer).
    d = L.decide(_inp(presence=None, tv_active=True))
    assert d.away_gate is False
    assert d.presence_state == C.PRES_UNKNOWN
    assert d.context == C.CTX_TV
    assert d.entertainment_active is True


def test_default_inputs_presence_unknown_no_gate():
    d = L.decide(_inp())
    assert d.presence_state == C.PRES_UNKNOWN
    assert d.away_gate is False
    assert d.context == C.CTX_IDLE


def test_away_gate_fields_in_as_dict():
    data = L.decide(_inp(presence="abwesend")).as_dict()
    for key in ("presence_state", "presence_source", "away_gate"):
        assert key in data
    assert data["presence_state"] == C.PRES_AWAY
    assert data["away_gate"] is True
