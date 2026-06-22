"""Pure-logic-Tests für den Context-Carve (Phase 3, FLEET-30).

Deckt die Board-Vorgaben ab:
- B2-Gate FINAL: PC-Gaming nur über die Titel-Ebene (ETM-Raw ≠ "No Game");
  Enum wählt nur den Sound-Mode-Subcontext (Enum 0 = gültiges Spiel).
- R6: PS5 an + Titel leer (Menü) → gaming_grind; Titel leer WÄHREND Session
  → letzter Subcontext sticky.
- FLEET-31: Quiet ist vom Szenario entkoppelt (kein CTX_PRIVATE mehr durch
  Quiet); private_time hat eigene ODER-Trigger (Stash/TC-Stash/manuell).
- Basis-Szenarien (TV/ATV/Rollback/audio_only) wie Toolbox.
"""
from __future__ import annotations

import bms_const as C
import bms_logic as L


def _inp(**kw):
    return L.Inputs(**kw)


# ----------------------------------------------------------------- Basis


def test_idle_default():
    d = L.decide(_inp())
    assert d.context == C.CTX_IDLE
    assert d.subcontext == C.SUB_NONE
    assert d.entertainment_active is False


def test_tv_alone():
    d = L.decide(_inp(tv_active=True))
    assert d.context == C.CTX_TV
    assert d.subcontext == C.SUB_TV_DEFAULT
    assert d.device == C.DEV_TV
    assert d.entertainment_active is True


def test_tv_source_ard():
    d = L.decide(_inp(tv_active=True, tv_source="ARD"))
    assert d.subcontext == C.SUB_TV_ARD


def test_appletv_netflix():
    d = L.decide(_inp(atv_state="playing", atv_app_id="com.netflix.Netflix"))
    assert d.context == C.CTX_STREAMING
    assert d.subcontext == C.SUB_STR_NETFLIX
    assert d.device == C.DEV_APPLETV


def test_appletv_master_idle_counts_as_streaming():
    d = L.decide(_inp(atv_state="idle", atv_app_id="com.netflix.Netflix"))
    assert d.context == C.CTX_STREAMING
    assert d.subcontext == C.SUB_STR_NETFLIX
    assert d.device == C.DEV_APPLETV


def test_appletv_unknown_app_defaults():
    d = L.decide(_inp(atv_state="playing", atv_app_id="com.example.foo"))
    assert d.subcontext == C.SUB_STR_DEFAULT


def test_appletv_system_app_rollback():
    d = L.decide(
        _inp(atv_state="playing", atv_app_id="com.apple.TVSettings", tv_active=True),
        pre_atv=(C.CTX_TV, C.SUB_TV_ARD),
    )
    assert d.context == C.CTX_TV
    assert d.subcontext == C.SUB_TV_ARD
    assert "atv_system_app_rollback" in d.active_reasons


def test_audio_only_stays_idle_not_streaming():
    # Reines Audio (HomePods-Musik) ist KEIN Screen-Szenario → idle, NICHT
    # streaming. Sonst kippt der Lichtkontext (light_policy) faelschlich auf
    # Cinema. Gerät wird trotzdem erkannt; Owner/Volume macht media_policy.
    d = L.decide(_inp(homepods_playing=True))
    assert d.context == C.CTX_IDLE
    assert d.entertainment_active is False
    assert d.device == C.DEV_HOMEPODS
    assert "audio_only_idle" in d.active_reasons


# ----------------------------------------------------------- B2-Gate (PC)


def test_pc_plug_alone_is_not_gaming():
    # Der B2-Bug: Plug-Wattage allein darf KEIN Gaming auslösen.
    d = L.decide(_inp(pc_active=True))
    assert d.context == C.CTX_IDLE


def test_pc_no_game_raw_is_not_gaming():
    # Live verifiziert: pc_raw="No Game" bei pc_enum=0 → kein Spiel.
    d = L.decide(_inp(pc_active=True, pc_raw="No Game", pc_enum=0))
    assert d.context == C.CTX_IDLE


def test_pc_title_with_enum_zero_is_valid_game():
    # Enum 0 ist gültiges Spiel (gaming_default) — "Enum >= 1"-Gate verworfen.
    d = L.decide(_inp(pc_active=True, pc_raw="Stardew Valley", pc_enum=0))
    assert d.context == C.CTX_GAMING
    assert d.subcontext == C.SUB_GAME_DEFAULT
    assert d.gaming_platform == C.GP_PC
    assert d.gaming_source == C.GS_PC
    assert d.headset_active is False


def test_pc_headset_enum():
    d = L.decide(_inp(pc_raw="Overwatch 2", pc_enum=2))
    assert d.context == C.CTX_GAMING
    assert d.subcontext == C.SUB_GAME_HEADSET
    assert d.headset_active is True


# ------------------------------------------------------------- PS5 + R6


def test_ps5_title_enum_grind():
    d = L.decide(_inp(ps5_on=True, ps5_raw="Helldivers 2", ps5_enum=1))
    assert d.context == C.CTX_GAMING
    assert d.subcontext == C.SUB_GAME_GRIND
    assert d.gaming_platform == C.GP_PS5
    assert d.gaming_source == C.GS_TV


def test_ps5_title_enum_zero_is_default():
    d = L.decide(_inp(ps5_on=True, ps5_raw="Horizon Zero Dawn", ps5_enum=0))
    assert d.subcontext == C.SUB_GAME_DEFAULT


def test_r6_ps5_menu_defaults_to_grind():
    # PS5 an, kein Titel (Menü) → gaming_grind, NICHT gaming_default.
    d = L.decide(_inp(ps5_on=True, ps5_raw="No Game"))
    assert d.context == C.CTX_GAMING
    assert d.subcontext == C.SUB_GAME_GRIND


def test_r6_title_drop_during_session_is_sticky():
    # Titel fällt WÄHREND der Session weg → letzter Subcontext bleibt.
    d = L.decide(_inp(ps5_on=True), sticky_gaming_sub=C.SUB_GAME_HEADSET)
    assert d.subcontext == C.SUB_GAME_HEADSET
    assert d.headset_active is True


def test_ps5_psn_title_fallback_used_when_raw_missing():
    # Kein ETM-Raw gebunden → PSN-Now-Playing als Titel-Fallback.
    d = L.decide(_inp(ps5_on=True, ps5_title="Returnal", ps5_enum=0))
    assert d.subcontext == C.SUB_GAME_DEFAULT  # Titel da → enum-basiert, kein R6


def test_switch_dock_is_gaming_default():
    d = L.decide(_inp(switch_dock=True))
    assert d.context == C.CTX_GAMING
    assert d.subcontext == C.SUB_GAME_DEFAULT
    assert d.gaming_platform == C.GP_SWITCH


# -------------------------------------------------- Quiet entkoppelt (FLEET-31)


def test_quiet_does_not_switch_context():
    # Toolbox-Kopplung quiet → CTX_PRIVATE ist gestrichen: TV bleibt TV.
    d = L.decide(_inp(tv_active=True, door_open=True))
    assert d.quiet_mode is True
    assert d.quiet_mode_reason == "door_open"
    assert d.context == C.CTX_TV
    assert d.entertainment_active is True


def test_quiet_reasons_priority():
    d = L.decide(_inp(call_active=True, door_open=True))
    assert d.quiet_mode_reason == "call_active"


def test_quiet_media_mute_enum():
    d = L.decide(_inp(media_enum=2))
    assert d.quiet_mode is True
    assert d.quiet_mode_reason == "classifier_media_mute"


def test_quiet_external_false_suppresses_heuristics():
    d = L.decide(_inp(quiet_external=False, door_open=True, call_active=True))
    assert d.quiet_mode is False
    assert d.quiet_mode_reason is None


def test_quiet_external_true_wins():
    d = L.decide(_inp(quiet_external=True))
    assert d.quiet_mode is True
    assert d.quiet_mode_reason == "quiet_mode_external"


# ------------------------------------------------- private_time (FLEET-31)


def test_private_via_stash_streams():
    d = L.decide(_inp(stash_streams=2))
    assert d.context == C.CTX_PRIVATE
    assert "private:stash_streams" in d.active_reasons
    assert d.entertainment_active is False


def test_private_via_stash_classifier_enum():
    # FLEET-43: Stash-Enum >= 1 ⇔ Titel vorhanden ⇒ aktiv.
    d = L.decide(_inp(stash_enum=1))
    assert d.context == C.CTX_PRIVATE
    assert "private:stash_classifier" in d.active_reasons


def test_private_via_manual_switch():
    d = L.decide(_inp(private_manual=True))
    assert d.context == C.CTX_PRIVATE
    assert "private:manual_switch" in d.active_reasons


def test_private_beats_gaming():
    # Priorität: private_time > gaming (Stash läuft auf dem PC — der PC-Titel
    # darf das Szenario nicht kapern).
    d = L.decide(_inp(stash_streams=1, pc_active=True, pc_raw="Overwatch 2", pc_enum=2))
    assert d.context == C.CTX_PRIVATE
    assert d.subcontext == C.SUB_NONE


def test_zero_stash_streams_is_not_private():
    d = L.decide(_inp(stash_streams=0, stash_enum=0))
    assert d.context == C.CTX_IDLE


def test_gaming_beats_tv():
    d = L.decide(_inp(tv_active=True, ps5_on=True, ps5_raw="Helldivers 2", ps5_enum=1))
    assert d.context == C.CTX_GAMING
