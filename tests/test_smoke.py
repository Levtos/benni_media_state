"""Smoke-Test: HA-freie logic.py lädt + decide() liefert stabile Defaults."""
from __future__ import annotations

import bms_logic as logic


def test_logic_imports():
    assert hasattr(logic, "decide")
    assert hasattr(logic, "Inputs")
    assert hasattr(logic, "MediaState")


def test_decide_defaults_to_idle():
    result = logic.decide(logic.Inputs())
    assert isinstance(result, logic.MediaState)
    data = result.as_dict()
    assert data["context"] == "idle"
    assert data["subcontext"] == "none"
    assert data["headset_active"] is False
    assert data["entertainment_active"] is False
    assert data["quiet_mode"] is False
    assert data["quiet_mode_reason"] is None
    for key in (
        "context", "subcontext", "device", "gaming_source", "gaming_platform",
        "headset_active", "entertainment_active", "active_reasons",
        "quiet_mode", "quiet_mode_reason",
    ):
        assert key in data
