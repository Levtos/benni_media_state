"""Tests für den switch_dock Anstiegs-Latch (FLEET-Workaround).

Bildet das Live-Bug-Muster ab: die Switch-Steckdose pulst im Standby kurz
(≈3–5 W, bis ~71 s) → ohne Latch flippt switch_dock und churnt den Radio-Stream.
Der Latch verschluckt Pulse < latch_seconds; echtes Spielen (dauerhaft) gewinnt.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import bms_logic as logic

T0 = datetime(2026, 6, 17, 9, 0, 0, tzinfo=timezone.utc)
LATCH = 120.0


def _step(raw, latched, rise_since, t):
    return logic.latch_rising_edge(
        raw, latched=latched, rise_since=rise_since, now=t, latch_seconds=LATCH
    )


def test_raw_false_stays_inactive():
    r = _step(False, latched=False, rise_since=None, t=T0)
    assert r.active is False and r.latched is False and r.rise_since is None
    assert r.recheck_in is None


def test_rise_starts_window_but_not_active_yet():
    r = _step(True, latched=False, rise_since=None, t=T0)
    assert r.active is False  # noch im Fenster
    assert r.rise_since == T0
    assert r.recheck_in == LATCH  # voller Rest


def test_short_standby_pulse_is_swallowed():
    """71-s-Puls (längster live beobachteter) darf NICHT durchschlagen."""
    r = _step(True, latched=False, rise_since=None, t=T0)
    # nach 71 s immer noch True, aber < 120 s → inaktiv
    r = _step(True, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=71))
    assert r.active is False and r.latched is False
    # Puls endet (Plug fällt auf 0) → reset, nie gelatcht
    r = _step(False, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=72))
    assert r.active is False and r.rise_since is None


def test_sustained_load_latches_after_window():
    r = _step(True, latched=False, rise_since=None, t=T0)
    r = _step(True, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=119))
    assert r.active is False
    r = _step(True, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=120))
    assert r.active is True and r.latched is True and r.recheck_in is None


def test_latched_stays_active_and_falls_with_raw():
    # einmal gelatcht
    r = _step(True, latched=True, rise_since=T0, t=T0 + timedelta(seconds=300))
    assert r.active is True and r.recheck_in is None
    # Abfall folgt sofort
    r = _step(False, latched=True, rise_since=T0, t=T0 + timedelta(seconds=301))
    assert r.active is False and r.latched is False and r.rise_since is None


def test_flicker_resets_window():
    """Kurzes Flackern setzt das Fenster zurück — kein Aufsummieren."""
    r = _step(True, latched=False, rise_since=None, t=T0)
    r = _step(False, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=60))
    assert r.rise_since is None
    r = _step(True, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=90))
    assert r.rise_since == T0 + timedelta(seconds=90)  # neu gestartet
    # 90 s nach Neustart (= 180 s nach T0) noch nicht aktiv
    r = _step(True, latched=r.latched, rise_since=r.rise_since, t=T0 + timedelta(seconds=180))
    assert r.active is False


def test_zero_latch_disables_delay():
    r = logic.latch_rising_edge(
        True, latched=False, rise_since=None, now=T0, latch_seconds=0.0
    )
    assert r.active is True and r.latched is True
