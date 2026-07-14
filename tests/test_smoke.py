"""Smoke-Test: HA-freie logic.py lädt + decide() liefert stabile Defaults."""
from __future__ import annotations

import ast
from pathlib import Path

import bms_const as C

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

def test_coordinator_uses_only_defined_config_constants():
    """Regression: undefined CONF_PC_TITLE crashed every coordinator refresh."""
    source = Path(__file__).parents[1] / "custom_components" / "benni_media_state" / "coordinator.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id.startswith("CONF_")}
    missing = sorted(name for name in used if not hasattr(C, name))
    assert missing == []
