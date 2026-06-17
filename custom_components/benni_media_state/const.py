"""Konstanten von benni_media_state (L1 Context-Feeder).

Eigenständige HA-Integration (eigene Domain). Leitet aus Roh-Quellen einen
Media-Context ab — entscheidet NICHTS (kein Apply). Konsumiert ihre Quellen
AUSSCHLIESSLICH als HA-Entity-IDs aus dem Config-Flow — kein Cross-Modul-
Python-Import (insbesondere keiner zu benni_media_policy).

Phase 3 (FLEET-30): Context-Teil aus bennis_toolbox/benni_media_context
gecarvt. Policy-Teile (Volumes, Subwoofer, Orchestratoren) bleiben draußen
(FLEET-5/34). B2-Gate final: Spiel ja/nein = Titel-Ebene (ETM-Raw),
Enum = Sound-Mode-Subcontext. Quiet ist vom Szenario ENTKOPPELT (FLEET-31).

Lastenheft: einhornzentrale/docs/lastenhefte/reviewed/media/ (v3.1)
"""
from __future__ import annotations

from typing import Any, Final

DOMAIN: Final[str] = "benni_media_state"
MODULE_ID: Final[str] = "media_state"
NAME: Final[str] = "Benni Media State"

# Datenwurzel in hass.data[DOMAIN].
DATA_COORDINATOR: Final[str] = "coordinator"

STORAGE_VERSION: Final[int] = 1


def unique_id(entry_id: str, suffix: str) -> str:
    """Domain- + entry-scoped unique_id (core_state-Blaupause, kollisionsfrei)."""
    return f"{DOMAIN}_{entry_id}_{suffix}"


# --------------------------------------------------------------------------- #
# Profil-Hub (benni / eltern) — wie benni_core_devices / light_policy.
# Auto-Bind-Reihenfolge: Override (options ▶ data) ▶ Profil-Map ▶ leer.
# --------------------------------------------------------------------------- #
CONF_PROFILE: Final[str] = "profile"
PROFILE_BENNI: Final[str] = "benni"
PROFILE_ELTERN: Final[str] = "eltern"
PROFILES: Final[list[str]] = [PROFILE_BENNI, PROFILE_ELTERN]
DEFAULT_PROFILE: Final[str] = PROFILE_BENNI
PROFILE_LABELS: Final[dict[str, str]] = {PROFILE_BENNI: "Benni", PROFILE_ELTERN: "Eltern"}

# --------------------------------------------------------------------------- #
# Context-Werte (1:1 aus der Toolbox — Konsumenten-Contract stabil halten).
# --------------------------------------------------------------------------- #
CTX_IDLE: Final = "idle"
CTX_TV: Final = "tv"
CTX_STREAMING: Final = "streaming"
CTX_GAMING: Final = "gaming"
CTX_PRIVATE: Final = "private_time"
ALL_CONTEXTS: Final = [CTX_IDLE, CTX_TV, CTX_STREAMING, CTX_GAMING, CTX_PRIVATE]

SUB_NONE: Final = "none"

SUB_TV_DEFAULT: Final = "tv_default"
SUB_TV_ARD: Final = "tv_ard"
SUB_TV_ZDF: Final = "tv_zdf"
SUB_TV_PRO7: Final = "tv_pro7"
SUB_TV_RTL: Final = "tv_rtl"

SUB_STR_DEFAULT: Final = "streaming_default"
SUB_STR_NETFLIX: Final = "streaming_netflix"
SUB_STR_DISNEY: Final = "streaming_disney"
SUB_STR_PRIME: Final = "streaming_prime"
SUB_STR_MAGENTA: Final = "streaming_magentatv"
SUB_STR_ARD: Final = "streaming_ard"
SUB_STR_ZDF: Final = "streaming_zdf"
SUB_STR_YOUTUBE: Final = "streaming_youtube"
SUB_STR_PLEX: Final = "streaming_plex"
SUB_STR_JELLYFIN: Final = "streaming_jellyfin"
SUB_STR_APPLETV: Final = "streaming_appletv"
SUB_STR_RTL: Final = "streaming_rtl"

SUB_GAME_DEFAULT: Final = "gaming_default"
SUB_GAME_GRIND: Final = "gaming_grind"
SUB_GAME_HEADSET: Final = "gaming_headset"

# ---- Geräte ----
DEV_NONE: Final = "none"
DEV_TV: Final = "tv"
DEV_APPLETV: Final = "appletv"
DEV_PS5: Final = "ps5"
DEV_SWITCH: Final = "switch"
DEV_PC: Final = "pc"
DEV_HOMEPODS: Final = "homepods"
DEV_DENON: Final = "denon"

# ---- Gaming-Quelle / -Plattform ----
GS_NONE: Final = "none"
GS_TV: Final = "tv"
GS_PC: Final = "pc"

GP_NONE: Final = "none"
GP_PS5: Final = "ps5"
GP_SWITCH: Final = "switch"
GP_PC: Final = "pc"

# --------------------------------------------------------------------------- #
# B2-Gate FINAL (FLEET-30, Lastenheft v3.1 + ETM-Live-Verify 2026-06-10).
# Zwei getrennte Ebenen:
#   Spiel ja/nein  = Titel-Ebene: ETM-Raw-Sensor vorhanden ∧ ≠ "No Game".
#                    (ETM self-gated via online_entity/Plug — Raw fällt bei
#                    Gerät-aus sauber auf "No Game"/unavailable.)
#   Sound-Mode     = Enum-Ebene (verbindlich per KH-7): 0=gaming_default
#                    (Denon+Sub), 1=grind, 2=headset. Enum wählt NUR den
#                    Subcontext — "Enum >= 1 als Gate" ist VERWORFEN
#                    (Enum 0 ist gültiges Spiel).
# --------------------------------------------------------------------------- #
ENUM_GAME_DEFAULT: Final = 0
ENUM_GAME_GRIND: Final = 1
ENUM_GAME_HEADSET: Final = 2

# Musik-/Media-Enum (title_classifier musikkatalog): 2 = Mute → Quiet-Detection
# hier in media_state (FLEET-30/31); 1 = Boost ist Volume → media_policy.
ENUM_MEDIA_MUTE: Final = 2

# Raw-Werte, die als „kein Titel" gelten (lowercase-Vergleich). "No Game" ist
# der ETM-Offline-/Leerlauf-Fallback (live verifiziert: pc_raw="No Game").
NO_TITLE_VALUES: Final = frozenset({"", "no game", "unknown", "unavailable", "none"})

# Apple-TV-System-Apps → Rollback aufs Pre-ATV-Szenario (Home, Settings, …).
APPLETV_SYSTEM_APPS: Final = {
    "com.apple.TVHomeSharing",
    "com.apple.TVSettings",
    "com.apple.HomeKit",
    "com.apple.TVScreenSaver",
}

DEFAULT_APPLETV_APP_MAP: Final[dict[str, str]] = {
    "com.netflix.Netflix": SUB_STR_NETFLIX,
    "com.disney.disneyplus": SUB_STR_DISNEY,
    "com.amazon.aiv.AIVApp": SUB_STR_PRIME,
    "de.telekom.magentatv": SUB_STR_MAGENTA,
    "de.ard.ardmediathek": SUB_STR_ARD,
    "de.zdf.zdfmediathek": SUB_STR_ZDF,
    "com.google.ios.youtube": SUB_STR_YOUTUBE,
    "com.plexapp.plex": SUB_STR_PLEX,
    "org.jellyfin.swiftfin": SUB_STR_JELLYFIN,
    "com.apple.TVWatchList": SUB_STR_APPLETV,
    "de.rtl.rtlnow": SUB_STR_RTL,
}

# TV-Quelle → Subcontext.
TV_SOURCE_MAP: Final[dict[str, str]] = {
    "ARD": SUB_TV_ARD,
    "Das Erste": SUB_TV_ARD,
    "ZDF": SUB_TV_ZDF,
    "ProSieben": SUB_TV_PRO7,
    "Pro7": SUB_TV_PRO7,
    "RTL": SUB_TV_RTL,
}

# --------------------------------------------------------------------------- #
# Config-Keys — Quell-Entities (alle als Entity-IDs aus dem Flow).
# Nur das NEUE per-Device-Modell (kein Legacy-Fallback — frischer Start).
# --------------------------------------------------------------------------- #
# TV
CONF_TV_PLAYER: Final = "tv_player_entity"
CONF_TV_ACTIVE: Final = "tv_active_entity"
CONF_TV_POWER: Final = "tv_power_entity"
# Apple TV
CONF_APPLETV_PLAYER: Final = "appletv_player_entity"
# PS5
CONF_PS5_PLAYER: Final = "ps5_player_entity"
CONF_PS5_ACTIVE: Final = "ps5_active_entity"
CONF_PS5_TITLE: Final = "ps5_title_entity"        # PSN-Now-Playing (Fallback)
CONF_PS5_RAW: Final = "ps5_raw_entity"            # ETM Raw-Title (B2-Gate)
CONF_PS5_ENUM: Final = "ps5_enum_entity"          # ETM Enum (Sound-Mode)
# Switch
CONF_SWITCH_ACTIVE: Final = "switch_active_entity"
# PC
CONF_PC_ACTIVE: Final = "pc_active_entity"
CONF_PC_RAW: Final = "pc_raw_entity"              # ETM Raw-Title (B2-Gate)
CONF_PC_ENUM: Final = "pc_enum_entity"            # ETM Enum (Sound-Mode)
# Denon
CONF_DENON_PLAYER: Final = "denon_player_entity"
CONF_DENON_ACTIVE: Final = "denon_active_entity"
# HomePods
CONF_HOMEPODS_PLAYER: Final = "homepods_player_entity"
# Musik-/Media-Enum (musikkatalog — Mute→Quiet)
CONF_MEDIA_ENUM: Final = "media_enum_entity"
# Quiet-Inputs (Detection bleibt L1 — FLEET-31; Output quiet_mode/_reason)
CONF_QUIET_EXTERNAL: Final = "quiet_external_entity"
CONF_DOOR: Final = "entry_door_entity"
CONF_CALL: Final = "call_active_entity"
CONF_ACTIVITY_STATE: Final = "activity_state_entity"
# Kontext-Echo (FLEET-69): core_state-Felder fürs Cockpit anzeigen (read-only,
# keine Entscheidung — "State sieht den Kontext"). Auto-Bind via PROFILE_PREFILL.
CONF_BIO_STATE: Final = "bio_state_entity"
CONF_PRESENCE: Final = "presence_entity"
CONF_HOUSEHOLD: Final = "household_entity"
CONF_TRANSITION: Final = "transition_entity"
CONF_DAY_STATE: Final = "day_state_entity"
# private_time-Trigger (FLEET-31: zustandsbasiert ODER manuell)
CONF_STASH_STREAMS: Final = "stash_streams_entity"
CONF_STASH_ENUM: Final = "stash_enum_entity"      # ETM Stash-Enum (FLEET-43)
CONF_PRIVATE_MANUAL: Final = "private_manual_entity"

# Keys, deren gebundene Entities der Coordinator beobachtet (event-driven).
WATCH_KEYS: Final[tuple[str, ...]] = (
    CONF_TV_PLAYER, CONF_TV_ACTIVE, CONF_TV_POWER,
    CONF_APPLETV_PLAYER,
    CONF_PS5_PLAYER, CONF_PS5_ACTIVE, CONF_PS5_TITLE, CONF_PS5_RAW, CONF_PS5_ENUM,
    CONF_SWITCH_ACTIVE,
    CONF_PC_ACTIVE, CONF_PC_RAW, CONF_PC_ENUM,
    CONF_DENON_PLAYER, CONF_DENON_ACTIVE,
    CONF_HOMEPODS_PLAYER,
    CONF_MEDIA_ENUM,
    CONF_QUIET_EXTERNAL, CONF_DOOR, CONF_CALL, CONF_ACTIVITY_STATE,
    CONF_STASH_STREAMS, CONF_STASH_ENUM, CONF_PRIVATE_MANUAL,
    CONF_BIO_STATE, CONF_PRESENCE, CONF_HOUSEHOLD, CONF_TRANSITION, CONF_DAY_STATE,
)

# --------------------------------------------------------------------------- #
# Profil-Map (Auto-Bind). benni = Live-IDs der Einhornzentrale.
# Greift nur, wenn die Entity in HA existiert → auf fremden Anlagen schadlos.
# eltern bewusst leer (Anlage existiert noch nicht).
#
# FLEET-52/64-Repoint (2026-06-14): Die `*_active`-Slots zeigten noch auf in
# der Big-Bang-YAML-Retire (FLEET-54) gelöschte `*_plug_power_active_atomic`-
# /`*_atomic`-Combineds; der Player-Fallback hat das nur maskiert. Jetzt auf
# die core_devices-Haupt-Sensoren repointet (Live-Verify Einhornzentrale):
# - power_device (PC/Switch-Plug): State = watt-primäres `powered` (reale Last,
#   nicht Plug-Schalter) → _bool(state) ist die korrekte „läuft wirklich"-Wahrheit.
# - media_device/console_device/audio_endpoint (TV/PS5/AVR): State spiegelt
#   Player/Status (off/playing/…), ebenfalls _bool-kompatibel.
# - TV_POWER MUSS numerisch bleiben (_build_inputs floatet den State) → roher
#   Watt-Sensor sensor.living_tv_plug_power, NICHT der Device-Sensor (State=off).
# - QUIET_EXTERNAL entfällt: Quiet-Detection ist L1 in media_state selbst
#   (FLEET-31); ohne Bindung → quiet_external=None → interne Heuristik greift.
# - ACTIVITY_STATE: Toolbox-Sensor (deprecated) → core_state.
# --------------------------------------------------------------------------- #
PROFILE_PREFILL: Final[dict[str, dict[str, Any]]] = {
    PROFILE_BENNI: {
        CONF_TV_PLAYER: "media_player.living_lgtv",
        CONF_TV_ACTIVE: "sensor.benni_device_living_tv",
        CONF_TV_POWER: "sensor.living_tv_plug_power",
        CONF_APPLETV_PLAYER: "media_player.living_appletv",
        CONF_PS5_PLAYER: "media_player.living_ps5",
        CONF_PS5_ACTIVE: "sensor.benni_device_ps5",
        CONF_PS5_TITLE: "sensor.psn_now_playing",
        CONF_PS5_RAW: "sensor.title_classifier_ps5_raw",
        CONF_PS5_ENUM: "sensor.title_classifier_ps5_enum",
        CONF_SWITCH_ACTIVE: "sensor.benni_device_living_switch_plug",
        CONF_PC_ACTIVE: "sensor.benni_device_living_pc",
        CONF_PC_RAW: "sensor.title_classifier_pc_raw",
        CONF_PC_ENUM: "sensor.title_classifier_pc_enum",
        CONF_DENON_PLAYER: "media_player.living_denon",
        CONF_DENON_ACTIVE: "sensor.benni_device_living_avr",
        CONF_HOMEPODS_PLAYER: "media_player.living_homepods_ma_group",
        CONF_MEDIA_ENUM: "sensor.title_classifier_musikkatalog_enum",
        # CONF_QUIET_EXTERNAL bewusst NICHT gebunden — Quiet ist L1 (FLEET-31).
        # Quiet-Trigger: Etagentür (R20). Call-Monitor existiert in HA nicht
        # (keine Fritzbox-Call-Integration) → CONF_CALL bleibt unbound.
        CONF_DOOR: "binary_sensor.hall_entry_door_contact",
        CONF_ACTIVITY_STATE: "sensor.benni_core_state_activity_state",
        # Kontext-Echo (FLEET-69) → core_state.
        CONF_BIO_STATE: "sensor.benni_core_state_bio_state",
        CONF_PRESENCE: "sensor.benni_core_state_presence_personal",
        CONF_HOUSEHOLD: "sensor.benni_core_state_presence_household",
        CONF_TRANSITION: "sensor.benni_core_state_presence_transition",
        CONF_DAY_STATE: "sensor.benni_core_state_day_state",
        CONF_STASH_STREAMS: "sensor.stash_active_streams",
        # Existenz-Filter bindet automatisch, sobald die Entity in HA existiert.
        CONF_STASH_ENUM: "sensor.title_classifier_stash_enum",
        # Dating-/Besuch-Schalter (FLEET-44): manueller private_time-Trigger.
        CONF_PRIVATE_MANUAL: "input_boolean.media_private_time_manual",
    },
    PROFILE_ELTERN: {},
}

# --------------------------------------------------------------------------- #
# Options.
# --------------------------------------------------------------------------- #
CONF_DEBOUNCE: Final = "debounce_seconds"
DEFAULT_DEBOUNCE: Final = 4.0
CONF_DIAGNOSTICS_VERBOSE: Final[str] = "diagnostics_verbose"
DEFAULT_DIAGNOSTICS_VERBOSE: Final[bool] = False
# Workaround (FLEET): Anstiegs-Latch auf switch_dock. Die Switch-Steckdose
# pulst im Standby periodisch kurz (≈3–5 W, bis ~71 s) → core_devices flippt
# `powered` sofort, ohne Anstiegs-Filter. Hier muss die Last erst N Sekunden
# DURCHGEHEND anliegen, bevor switch_dock als aktiv gilt. Eigentlicher Fix
# gehört nach core_devices (generischer min-on-Filter beim Rewrite).
CONF_SWITCH_LATCH_SECONDS: Final[str] = "switch_latch_seconds"
DEFAULT_SWITCH_LATCH_SECONDS: Final[float] = 120.0

# --------------------------------------------------------------------------- #
# Default-data. Spiegelt das Entity-Roster (Felder = MediaState.as_dict()).
# --------------------------------------------------------------------------- #
DEFAULT_CONTEXT: Final[str] = CTX_IDLE
DEFAULT_DATA: Final[dict[str, Any]] = {
    "context": DEFAULT_CONTEXT,
    "subcontext": SUB_NONE,
    "device": DEV_NONE,
    "gaming_source": GS_NONE,
    "gaming_platform": GP_NONE,
    "headset_active": False,
    "entertainment_active": False,
    "active_reasons": [],
    # Quiet bleibt L1 (FLEET-31) — entkoppelt vom Szenario.
    "quiet_mode": False,
    "quiet_mode_reason": None,
}

# --------------------------------------------------------------------------- #
# Output-Entity-Roster. uid = unique_id-Suffix, key = Feld in data.
# --------------------------------------------------------------------------- #
# sensors
UID_CONTEXT: Final[str] = "media_context"
UID_SUBCONTEXT: Final[str] = "media_subcontext"
UID_DEVICE: Final[str] = "media_device"
UID_GAMING_SOURCE: Final[str] = "gaming_source"
UID_GAMING_PLATFORM: Final[str] = "gaming_platform"
# binary_sensors
UID_HEADSET_ACTIVE: Final[str] = "headset_active"
UID_ENTERTAINMENT_ACTIVE: Final[str] = "entertainment_active"
UID_QUIET_MODE: Final[str] = "quiet_mode"
# quiet_mode_reason ist ein Sensor (Freitext-Begründung), kein Binary.
UID_QUIET_MODE_REASON: Final[str] = "quiet_mode_reason"

# Attribute, die der reiche Context-Sensor zusätzlich zum State zeigt.
CONTEXT_ATTRS: Final[tuple[str, ...]] = (
    "subcontext",
    "device",
    "gaming_source",
    "gaming_platform",
    "headset_active",
    "entertainment_active",
    "active_reasons",
    "quiet_mode",
    "quiet_mode_reason",
)

# --------------------------------------------------------------------------- #
# Panel / WebSocket-API (eigenes Dashboard-Frontend, Vanilla, kein Build-Step).
# --------------------------------------------------------------------------- #
PANEL_URL_PATH: Final[str] = "benni_media_state"
PANEL_TITLE: Final[str] = "Media State"
PANEL_ICON: Final[str] = "mdi:multimedia"
FRONTEND_DIR_URL: Final[str] = "/benni_media_state_app"
FRONTEND_ENTRY: Final[str] = f"{FRONTEND_DIR_URL}/main.js"
PANEL_ELEMENT: Final[str] = "bms-app"

# WS-Commands (Namespace = Domain).
WS_GET_STATUS: Final[str] = f"{DOMAIN}/get_status"
