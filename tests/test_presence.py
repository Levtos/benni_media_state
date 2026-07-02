"""Presence-Gate: media_state echo't die core_state-Entscheidung (kein eigenes
home/away-Klassifizieren mehr) + ON-Debounce als Defense-in-Depth.

Deckt ab:
1. Away-Wahrheit kommt aus `binary_sensor.benni_core_state_away` (away_raw/
   away_gated), NICHT aus einer eigenen presence-String-Klassifikation.
2. bei_eltern ist bereits im core_state-Gate als home (off) kodiert → kein Gate.
3. unknown/ungebunden (away_raw=None) → KEIN Fehl-Stop.
4. Abwesenheit (away_gated) erzwingt idle/entertainment_active=False.
5. ON-Debounce: transienter Away-Dip greift nicht; Rückkehr wirkt sofort.
"""
from __future__ import annotations

import bms_const as C
import bms_logic as L


def _inp(**kw):
    return L.Inputs(**kw)


# ------------------------------------------------- presence_state_from_away


def test_gated_away_is_abwesend():
    assert L.presence_state_from_away(True, True) == C.PRES_AWAY


def test_home_when_away_false():
    assert L.presence_state_from_away(False, False) == C.PRES_HOME


def test_unknown_when_source_unbound():
    # away_raw None (ungebunden/unavailable) → unknown, kein Fehl-Stop.
    assert L.presence_state_from_away(None, False) == C.PRES_UNKNOWN


def test_raw_away_but_not_yet_debounced_is_home():
    # Away liegt roh an, hat aber die Debounce-Schwelle noch nicht erreicht →
    # noch KEIN abwesend (Cockpit zeigt zuhause, bis das Gate greift).
    assert L.presence_state_from_away(True, False) == C.PRES_HOME


# ---------------------------------------------------------------- gate_away


def test_gate_away_holds_until_debounce_elapsed():
    # t=0 erstes Away → Timer startet, noch nicht gegated.
    gated, since = L.gate_away(True, None, 0.0, 25.0)
    assert gated is False and since == 0.0
    # t=10s → weiter im Fenster.
    gated, since = L.gate_away(True, since, 10.0, 25.0)
    assert gated is False and since == 0.0
    # t=25s → Schwelle erreicht → Gate greift.
    gated, since = L.gate_away(True, since, 25.0, 25.0)
    assert gated is True and since == 0.0


def test_gate_away_resets_on_non_away_tick():
    # Ein Nicht-Away-Tick (Rückkehr) öffnet sofort + löscht den Timer.
    gated, since = L.gate_away(False, 0.0, 10.0, 25.0)
    assert gated is False and since is None
    # None (ungebunden) verhält sich wie nicht-away.
    gated, since = L.gate_away(None, 12.0, 20.0, 25.0)
    assert gated is False and since is None


def test_gate_away_transient_dip_never_gates():
    # Away-Blip < Debounce, dann wieder home → nie gegated.
    gated, since = L.gate_away(True, None, 0.0, 25.0)
    assert gated is False
    gated, since = L.gate_away(False, since, 5.0, 25.0)
    assert gated is False and since is None


# ------------------------------------------------------------ away gate → decide


def test_away_forces_idle_and_stops_entertainment():
    # HomePods spielen + TV an, aber der (debouncte) core_state-Gate sagt away →
    # harte Deaktivierung: idle, entertainment_active=False, away_gate=True.
    d = L.decide(_inp(
        presence="abwesend", away_raw=True, away_gated=True,
        homepods_playing=True, tv_active=True,
    ))
    assert d.context == C.CTX_IDLE
    assert d.subcontext == C.SUB_NONE
    assert d.entertainment_active is False
    assert d.away_gate is True
    assert d.presence_state == C.PRES_AWAY
    assert d.presence_source == "abwesend"
    assert "away_gate" in d.active_reasons


def test_away_beats_gaming():
    d = L.decide(_inp(
        presence="abwesend", away_raw=True, away_gated=True,
        ps5_on=True, ps5_raw="Helldivers 2", ps5_enum=1,
    ))
    assert d.context == C.CTX_IDLE
    assert d.away_gate is True
    assert d.gaming_platform == C.GP_NONE
    assert d.headset_active is False


def test_away_beats_private_time():
    d = L.decide(_inp(
        presence="abwesend", away_raw=True, away_gated=True, stash_streams=2,
    ))
    assert d.context == C.CTX_IDLE
    assert d.away_gate is True


def test_raw_away_not_yet_debounced_does_not_gate():
    # Away liegt roh an, aber noch nicht gegated → laufende Medien bleiben.
    d = L.decide(_inp(
        presence="abwesend", away_raw=True, away_gated=False, tv_active=True,
    ))
    assert d.away_gate is False
    assert d.context == C.CTX_TV
    assert d.entertainment_active is True
    assert d.presence_state == C.PRES_HOME


def test_bei_eltern_does_not_gate_media():
    # bei_eltern ist im core_state-Gate bereits home (away=off) → kein Gate.
    d = L.decide(_inp(
        presence="bei_eltern", away_raw=False, away_gated=False, tv_active=True,
    ))
    assert d.context == C.CTX_TV
    assert d.away_gate is False
    assert d.presence_state == C.PRES_HOME
    assert d.presence_source == "bei_eltern"
    assert d.entertainment_active is True


def test_home_does_not_gate():
    d = L.decide(_inp(
        presence="zuhause", away_raw=False, away_gated=False, tv_active=True,
    ))
    assert d.away_gate is False
    assert d.presence_state == C.PRES_HOME
    assert d.context == C.CTX_TV
    assert d.entertainment_active is True


def test_unknown_presence_does_not_gate():
    # Defensive: away_raw None (Sensor-Aussetzer) darf laufende Medien NICHT
    # stoppen.
    d = L.decide(_inp(presence=None, away_raw=None, away_gated=False, tv_active=True))
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
    data = L.decide(_inp(
        presence="abwesend", away_raw=True, away_gated=True,
    )).as_dict()
    for key in ("presence_state", "presence_source", "away_gate"):
        assert key in data
    assert data["presence_state"] == C.PRES_AWAY
    assert data["away_gate"] is True
