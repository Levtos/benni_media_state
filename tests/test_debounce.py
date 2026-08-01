"""benni_media#13 — Debounce-Fenster von media_state auf dem TV-Übergangspfad.

Belegte Kosten (Recorder, 2026-07-31, TV-Start):

    22:23:18.897  sensor.benni_master_denon  off → active
    22:23:39.860  sensor.benni_master_tv     off → active
    22:23:43.864  media_context              idle → tv      (+4.004 s)

Zwischen TV-Master und Kontextwechsel lag genau EIN volles Debounce-Fenster
(4.0 s), ohne dass ein Burst vorlag. Das Fenster ist ein Churn-Schutz, kein
Korrektheits-Gate — es wird verkürzt und zusätzlich nach oben gedeckelt.
"""
from __future__ import annotations

import bms_const as C
import bms_logic as L


# --------------------------------------------------------------------------- #
# Fenster-Länge
# --------------------------------------------------------------------------- #
def test_debounce_window_is_shortened():
    """4.0 s → 2.0 s: spart 2 s auf dem kritischen Übergangspfad."""
    assert C.DEFAULT_DEBOUNCE == 2.0


def test_debounce_window_still_coalesces_a_realistic_burst():
    """Z2M liefert die Attribute EINES Geräts binnen Millisekunden — 2 s reicht.

    Das Leistungs-Raster ist 10 s; zwei echte, getrennte Ereignisse liegen also
    weit außerhalb des Fensters und dürfen auch getrennt bleiben.
    """
    assert C.DEFAULT_DEBOUNCE >= 1.0     # Burst sicher gebündelt
    assert C.DEFAULT_DEBOUNCE < 10.0     # aber kleiner als das Z2M-Raster


def test_max_wait_cap_is_larger_than_the_window():
    """Der Deckel darf das normale Bündeln nicht aushebeln."""
    assert C.DEFAULT_DEBOUNCE_MAX_WAIT > C.DEFAULT_DEBOUNCE


def test_worst_case_state_latency_is_bounded():
    """Deterministische Obergrenze statt unbegrenztem Verschieben."""
    assert C.DEFAULT_DEBOUNCE_MAX_WAIT + C.DEFAULT_DEBOUNCE <= 10.0


# --------------------------------------------------------------------------- #
# Re-Arm-Regel (pure)
# --------------------------------------------------------------------------- #
def test_rearm_without_running_window():
    """Kein Fenster → immer armen (Burst-Sammlung beginnt)."""
    assert L.debounce_rearm(False, None, 6.0) is True
    assert L.debounce_rearm(False, 99.0, 6.0) is True


def test_rearm_while_window_is_young():
    """Junges Fenster → weiter bündeln (Verhalten wie bisher)."""
    assert L.debounce_rearm(True, 0.0, 6.0) is True
    assert L.debounce_rearm(True, 5.9, 6.0) is True


def test_no_rearm_once_the_cap_is_reached():
    """Deckel erreicht → Fenster läuft aus, statt verlängert zu werden."""
    assert L.debounce_rearm(True, 6.0, 6.0) is False
    assert L.debounce_rearm(True, 12.0, 6.0) is False


def test_rearm_without_known_age_is_conservative():
    """Unbekanntes Alter → wie bisher armen (kein Verhalten auf Rateweg)."""
    assert L.debounce_rearm(True, None, 6.0) is True


def test_sustained_change_stream_cannot_starve_the_compute():
    """Simuliert einen Dauer-Änderungsstrom im 0.5-s-Takt."""
    age = 0.0
    rearms = 0
    for _ in range(40):
        if L.debounce_rearm(True, age, C.DEFAULT_DEBOUNCE_MAX_WAIT):
            rearms += 1
        age += 0.5
    # Ab dem Deckel wird nicht mehr verlängert → endliche Zahl von Re-Arms.
    assert rearms < 40
    assert rearms == int(C.DEFAULT_DEBOUNCE_MAX_WAIT / 0.5)


# --------------------------------------------------------------------------- #
# Nicht angefasste Timer (Regressionsschutz)
# --------------------------------------------------------------------------- #
def test_away_debounce_is_untouched():
    """FLEET-213/214: 25 s ON-Debounce gegen Presence-Flappen bleibt."""
    assert C.AWAY_DEBOUNCE_SECONDS == 25.0


def test_ps5_dropout_hold_is_untouched():
    """FLEET-262: 90 s PS5-Dropout-Hold bleibt."""
    assert C.PS5_DROPOUT_HOLD_SECONDS == 90.0


def test_away_gate_still_requires_the_full_window():
    """Der Away-Gate ist ein Korrektheits-Gate und wird NICHT verkürzt."""
    gated, since = L.gate_away(True, None, 1000.0, C.AWAY_DEBOUNCE_SECONDS)
    assert gated is False   # gerade erst begonnen
    gated2, _ = L.gate_away(
        True, since, 1000.0 + C.AWAY_DEBOUNCE_SECONDS, C.AWAY_DEBOUNCE_SECONDS
    )
    assert gated2 is True
