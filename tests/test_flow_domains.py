"""Config-/Options-Flow-Domain-Contract (FLEET-212).

Der HA-freie `source_domain_filter` bildet 1:1 die EntitySelector-Domain-Filter
ab. Damit ist ohne HA-Import testbar:
- Master-Felder akzeptieren Core-Devices-Master-Sensoren (`sensor`).
- Echte Media-Player-Felder lehnen Sensoren weiter ab (`media_player` only).
"""
from __future__ import annotations

import bms_const as C

MASTER_FIELDS = (
    C.CONF_TV_MASTER,
    C.CONF_APPLETV_MASTER,
    C.CONF_PS5_ACTIVE,
    C.CONF_SWITCH_ACTIVE,
    C.CONF_PC_ACTIVE,
    C.CONF_DENON_ACTIVE,
)

PLAYER_FIELDS = (
    C.CONF_TV_PLAYER,
    C.CONF_APPLETV_PLAYER,
    C.CONF_PS5_PLAYER,
    C.CONF_DENON_PLAYER,
    C.CONF_HOMEPODS_PLAYER,
)


def test_master_fields_accept_sensor():
    for key in MASTER_FIELDS:
        domains = C.source_domain_filter(key)
        assert domains is not None, key
        assert "sensor" in domains, key


def test_appletv_master_accepts_sensor():
    # Der konkrete Bug: sensor.benni_master_appletv gehört in ein Master-Feld.
    assert "sensor" in C.source_domain_filter(C.CONF_APPLETV_MASTER)


def test_player_fields_reject_sensor():
    for key in PLAYER_FIELDS:
        domains = C.source_domain_filter(key)
        assert domains == ("media_player",), key
        assert "sensor" not in domains, key


def test_appletv_player_is_media_player_only():
    assert C.source_domain_filter(C.CONF_APPLETV_PLAYER) == ("media_player",)


def test_generic_slots_are_unfiltered():
    # Freitext-/Enum-/Kontext-Slots bleiben ungefiltert (volle Flexibilität).
    for key in (C.CONF_PS5_RAW, C.CONF_PRESENCE, C.CONF_MEDIA_ENUM, C.CONF_DOOR):
        assert C.source_domain_filter(key) is None, key


def test_player_and_master_key_sets_are_disjoint():
    assert not (set(C.PLAYER_KEYS) & set(C.MASTER_KEYS))
