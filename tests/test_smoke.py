"""Smoke-Test: HA-freie logic.py lädt + decide()-Stub aufrufbar.

Lädt logic.py direkt per Pfad (kein HA-Import-Pfad nötig — logic.py ist
strikt HA-frei und ohne relative Imports).
"""
from __future__ import annotations

import importlib.util
import os
import sys

DOMAIN = "benni_media_state"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIC_PATH = os.path.join(ROOT, "custom_components", DOMAIN, "logic.py")


def _load_logic():
    name = f"{DOMAIN}_logic"
    spec = importlib.util.spec_from_file_location(name, LOGIC_PATH)
    mod = importlib.util.module_from_spec(spec)
    # In sys.modules registrieren, bevor exec läuft — sonst kann @dataclass die
    # Typ-Auflösung (sys.modules[cls.__module__]) nicht durchführen (Py 3.13).
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_logic_imports():
    logic = _load_logic()
    assert hasattr(logic, "decide")
    assert hasattr(logic, "Inputs")
    assert hasattr(logic, "MediaState")


def test_decide_stub_returns_defaults():
    logic = _load_logic()
    result = logic.decide(logic.Inputs())
    assert isinstance(result, logic.MediaState)
    data = result.as_dict()
    assert isinstance(data, dict)
    # Roster-Felder vorhanden, stabile Defaults.
    assert data["context"] == "idle"
    assert data["headset_active"] is False
    assert data["entertainment_active"] is False
    assert data["active_reasons"] == []
    # Quiet bleibt L1 (FLEET-31): media_state besitzt die Felder.
    assert data["quiet_mode"] is False
    assert data["quiet_mode_reason"] is None
    for key in (
        "context", "subcontext", "device", "gaming_source", "gaming_platform",
        "headset_active", "entertainment_active", "active_reasons",
        "quiet_mode", "quiet_mode_reason",
    ):
        assert key in data
