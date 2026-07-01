"""ReBind guardrails for master-backed source defaults."""
from __future__ import annotations

import bms_const as C


def test_benni_active_sources_default_to_masters():
    prefill = C.PROFILE_PREFILL[C.PROFILE_BENNI]

    assert C.CONF_TV_ACTIVE not in prefill
    assert prefill[C.CONF_TV_MASTER] == "sensor.benni_master_tv"
    # FLEET-212: Apple TV sauber getrennt — nativer Player + Master-Sensor.
    assert prefill[C.CONF_APPLETV_PLAYER] == "media_player.living_appletv"
    assert prefill[C.CONF_APPLETV_MASTER] == "sensor.benni_master_appletv"
    assert prefill[C.CONF_PS5_ACTIVE] == "sensor.benni_master_ps5"
    assert prefill[C.CONF_SWITCH_ACTIVE] == "sensor.benni_master_switch"
    assert prefill[C.CONF_PC_ACTIVE] == "sensor.benni_master_pc"
    assert prefill[C.CONF_DENON_ACTIVE] == "sensor.benni_master_denon"


def test_legacy_active_sources_have_master_repoints():
    assert C.LEGACY_ENTITY_REPOINTS == {
        # FLEET-212: `media_player.living_appletv` NICHT mehr repointet — es ist
        # jetzt der native Player-Slot (sonst würde ein value-basierter Repoint
        # den korrekt gewählten Player wieder auf den Sensor-Master umschreiben).
        "sensor.benni_device_living_appletv": "sensor.benni_master_appletv",
        "sensor.benni_device_living_tv": "sensor.benni_master_tv",
        "sensor.benni_device_ps5": "sensor.benni_master_ps5",
        "sensor.benni_device_living_switch_plug": "sensor.benni_master_switch",
        "sensor.benni_device_living_pc": "sensor.benni_master_pc",
        "sensor.benni_device_living_avr": "sensor.benni_master_denon",
    }

    prefill_values = {
        value
        for value in C.PROFILE_PREFILL[C.PROFILE_BENNI].values()
        if isinstance(value, str)
    }
    assert not (set(C.LEGACY_ENTITY_REPOINTS) & prefill_values)
