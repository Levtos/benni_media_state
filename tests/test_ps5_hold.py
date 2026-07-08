"""PS5-Gaming OFF-Hold (FLEET-262): überbrückt PlayStation-media_player-Dropouts.

Die Sony-PlayStation-Integration fällt beim Zocken periodisch ~30 s auf
`unavailable`; der gebundene core_devices-Master folgt (nicht watt-primär) auf
`unknown`. `logic.hold_ps5_on` hält `ps5_on` über diese degradierten Fenster,
räumt aber bei einem sauberen `off` sofort. Symmetrisch zu gate_away, nur als
OFF- statt ON-Debounce.

Deckt ab:
1. Echtes On refresht den Anker und hält sofort.
2. Sauberes Aus (Quelle nicht degradiert) räumt SOFORT — kein Hold.
3. Degradierter Einbruch < Fenster → gehalten; Anker bleibt.
4. Degradierter Einbruch >= Fenster → aufgegeben.
5. Nie ein echtes On gesehen → nichts erfunden.
6. End-to-end: ~30-s-Dropout wird überbrückt, echtes Aus danach beendet.
"""
from __future__ import annotations

import bms_const as C
import bms_logic as L


HOLD = C.PS5_DROPOUT_HOLD_SECONDS


# --------------------------------------------------------------- hold_ps5_on


def test_real_on_refreshes_anchor_and_holds():
    held, since = L.hold_ps5_on(True, False, None, 10.0, HOLD)
    assert held is True and since == 10.0
    # Weiterer echter On-Tick refresht den Anker.
    held, since = L.hold_ps5_on(True, False, since, 42.0, HOLD)
    assert held is True and since == 42.0


def test_clean_off_releases_immediately():
    # raw_on False, Quelle NICHT degradiert (Master/Player melden definit off) →
    # sofort aus, auch wenn gerade eben noch gespielt wurde.
    held, since = L.hold_ps5_on(False, False, 100.0, 101.0, HOLD)
    assert held is False and since is None


def test_degraded_dropout_within_window_holds():
    # Letztes echtes On bei t=0, jetzt t=30 mit degradierter Quelle → gehalten,
    # Anker unverändert (Fenster läuft weiter ab t=0).
    held, since = L.hold_ps5_on(False, True, 0.0, 30.0, HOLD)
    assert held is True and since == 0.0


def test_degraded_dropout_beyond_window_gives_up():
    held, since = L.hold_ps5_on(False, True, 0.0, HOLD + 0.1, HOLD)
    assert held is False and since is None


def test_never_on_does_not_invent_gaming():
    # hold_since None (nie ein echtes On) + degradierte Quelle → kein Hold.
    held, since = L.hold_ps5_on(False, True, None, 5.0, HOLD)
    assert held is False and since is None


def test_end_to_end_bridges_30s_dropout_then_real_off():
    # Session läuft.
    held, since = L.hold_ps5_on(True, False, None, 0.0, HOLD)
    assert held is True
    # Dropout startet (Quelle degradiert), ~5 s.
    held, since = L.hold_ps5_on(False, True, since, 5.0, HOLD)
    assert held is True and since == 0.0
    # Immer noch im Dropout bei ~30 s → weiter gehalten (Kette reißt NICHT).
    held, since = L.hold_ps5_on(False, True, since, 30.0, HOLD)
    assert held is True and since == 0.0
    # PS5 kommt zurück (echtes On) → Anker refresht.
    held, since = L.hold_ps5_on(True, False, since, 33.0, HOLD)
    assert held is True and since == 33.0
    # Benni schaltet wirklich aus → sofort aus (kein 90-s-Nachhang).
    held, since = L.hold_ps5_on(False, False, since, 34.0, HOLD)
    assert held is False and since is None


def test_held_ps5_on_keeps_gaming_scenario_in_decide():
    # Der Coordinator reicht den gehaltenen ps5_on-Wert an decide(); mit ps5_on
    # True bleibt das Gaming-Szenario stehen, auch wenn Titel gerade auf "idle"
    # gefallen ist (R6-Sticky übernimmt den Subcontext).
    d = L.decide(
        L.Inputs(ps5_on=True, ps5_raw="idle", tv_active=True),
        sticky_gaming_sub=C.SUB_GAME_DEFAULT,
    )
    assert d.context == C.CTX_GAMING
    assert d.gaming_platform == C.GP_PS5
    assert d.subcontext == C.SUB_GAME_DEFAULT
