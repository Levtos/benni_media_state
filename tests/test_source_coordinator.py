"""Execute the real coordinator with fake HA states and deterministic timers."""
import importlib.util
import sys
import types
from pathlib import Path

import bms_const as C
import pytest


@pytest.fixture
def runtime(monkeypatch):
    modules = {}
    for name in ["homeassistant", "homeassistant.config_entries", "homeassistant.core", "homeassistant.helpers", "homeassistant.helpers.event", "homeassistant.helpers.storage", "homeassistant.helpers.update_coordinator"]:
        modules[name] = types.ModuleType(name)
        monkeypatch.setitem(sys.modules, name, modules[name])
    modules["homeassistant.config_entries"].ConfigEntry = object
    core = modules["homeassistant.core"]
    core.CALLBACK_TYPE = object
    core.Event = core.HomeAssistant = object
    core.callback = lambda fn: fn
    clock = types.SimpleNamespace(now=0.0, timers=[])

    def later(hass, delay, callback):
        timer = types.SimpleNamespace(at=clock.now + delay, callback=callback, cancelled=False)
        clock.timers.append(timer)
        return lambda: setattr(timer, "cancelled", True)

    modules["homeassistant.helpers.event"].async_call_later = later
    modules["homeassistant.helpers.event"].async_track_state_change_event = lambda *args: lambda: None

    class Store:
        def __init__(self, *args):
            pass

        def async_delay_save(self, *args):
            pass

    class Coordinator:
        def __class_getitem__(cls, item):
            return cls

        def __init__(self, hass, *args, **kwargs):
            self.hass = hass
            self.data = {}

        def async_set_updated_data(self, data):
            self.data = data

    modules["homeassistant.helpers.storage"].Store = Store
    modules["homeassistant.helpers.update_coordinator"].DataUpdateCoordinator = Coordinator
    name = "bms_pure_pkg.coordinator"
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / "custom_components/benni_media_state/coordinator.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module.time, "monotonic", lambda: clock.now)
    states = {}
    hass = types.SimpleNamespace(states=types.SimpleNamespace(get=states.get))
    entry = types.SimpleNamespace(data={}, options={}, entry_id="test")
    coord = module.MediaStateCoordinator(hass, entry)

    def put(key, value, **attrs):
        states[coord._entity_id(key)] = types.SimpleNamespace(state=value, attributes=attrs)

    def advance(now):
        while True:
            due = [t for t in clock.timers if not t.cancelled and t.at <= now]
            if not due:
                break
            timer = min(due, key=lambda t: t.at)
            clock.now = timer.at
            timer.cancelled = True
            timer.callback(None)
        clock.now = now

    return coord, clock, put, advance


def test_grace_starts_at_event_and_expires_without_another_state_event(runtime):
    coord, clock, put, advance = runtime
    put(C.CONF_TV_PLAYER, "on", source="Apple OTT")
    put(C.CONF_APPLETV_PLAYER, "playing")
    coord.async_set_updated_data(coord._compute())
    assert coord.data["context"] == C.CTX_STREAMING
    clock.now = 10
    put(C.CONF_APPLETV_PLAYER, "paused")
    put(C.CONF_TV_PLAYER, "on", source="unavailable")
    coord._on_state_change(None)
    advance(12)
    assert coord.data["context"] == C.CTX_STREAMING
    assert coord.data["source_arbitration"]["grace_remaining_seconds"] == 3
    advance(15)
    assert coord.data["context"] != C.CTX_STREAMING
    assert coord.data["source_arbitration"]["grace_expired"]


def test_other_source_wins_without_native_ps5_or_tv_master(runtime):
    coord, clock, put, advance = runtime
    put(C.CONF_TV_PLAYER, "on", source="Apple OTT")
    put(C.CONF_APPLETV_PLAYER, "playing")
    coord.async_set_updated_data(coord._compute())
    clock.now = 1
    put(C.CONF_APPLETV_PLAYER, "paused")
    put(C.CONF_PS5_PLAYER, "off")
    put(C.CONF_TV_PLAYER, "on", source="PlayStation 5")
    coord._on_state_change(None)
    advance(3)
    assert coord.data["device"] == C.DEV_PS5
    assert coord.data["source_arbitration"]["reason"] == "source_changed"


def test_tv_off_bypasses_running_grace(runtime):
    coord, clock, put, advance = runtime
    put(C.CONF_TV_PLAYER, "on", source="Apple OTT")
    put(C.CONF_APPLETV_PLAYER, "playing")
    coord.async_set_updated_data(coord._compute())
    put(C.CONF_APPLETV_PLAYER, "paused")
    put(C.CONF_TV_PLAYER, "on", source="unknown")
    coord._on_state_change(None)
    advance(1)
    put(C.CONF_TV_PLAYER, "off", source="Apple OTT")
    coord._on_state_change(None)
    advance(2)
    assert coord.data["context"] == C.CTX_IDLE
    assert not coord.data["source_arbitration"]["grace_active"]


def test_authoritative_playing_cannot_be_starved_by_repeated_events(runtime):
    coord, clock, put, advance = runtime
    put(C.CONF_APPLETV_PLAYER, "playing")
    coord._on_state_change(None)
    for time in [0.5, 1, 1.5]:
        advance(time)
        coord._on_state_change(None)
    advance(2)
    assert coord.data["context"] == C.CTX_STREAMING


def test_tv_only_startup_finishes_without_new_events(runtime):
    coord, clock, put, advance = runtime
    put(C.CONF_TV_PLAYER, "unavailable")
    put(C.CONF_TV_POWER, "50")
    coord.async_set_updated_data(coord._compute())
    assert coord.data["context"] == C.CTX_IDLE
    advance(20)
    assert coord.data["context"] == C.CTX_TV


def test_existing_binding_override_wins_over_lan_prefill(runtime):
    coord, clock, put, advance = runtime
    coord.entry.options[C.CONF_APPLETV_PLAYER] = "media_player.current_native"
    put(C.CONF_APPLETV_PLAYER, "paused")
    assert coord.bindings()[C.CONF_APPLETV_PLAYER] == "media_player.current_native"
    assert coord._atv()[0] == "paused"
