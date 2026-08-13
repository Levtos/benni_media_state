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

# --------------------------------------------------------------------------- #
# Activity-Context-Feed (FLEET-255): die Media-HÄLFTE des Activity-States für
# core_state. Additiv — ändert media_context NICHT. Wo media_context Audio
# bewusst als idle/audio_only_idle führt (Licht/Scene-Schutz), surfacet dieser
# Feed dasselbe Audio als `music`. Der finale Gesamt-Activity-State bleibt bei
# core_state (sleep > waking > private_time > gaming > entertainment > music >
# work_home > household > pc_active > free_time > idle). Feed-interne Priorität:
# private_time > gaming > entertainment > music > idle. Kein Rückgriff auf
# core_state activity_state oder presence_effective (Zyklus-Freiheit).
# --------------------------------------------------------------------------- #
ACTX_IDLE: Final = "idle"
ACTX_MUSIC: Final = "music"
ACTX_ENTERTAINMENT: Final = "entertainment"
ACTX_GAMING: Final = "gaming"
ACTX_PRIVATE: Final = "private_time"
ALL_ACTIVITY_CONTEXTS: Final = [
    ACTX_PRIVATE, ACTX_GAMING, ACTX_ENTERTAINMENT, ACTX_MUSIC, ACTX_IDLE,
]

# Hold-Strength-Hinweis (nur Consumer-Attribut, entscheidet hier nichts):
# hard = wahrscheinlich bewusste lokale Nutzung (private_time/gaming),
# soft = ambient/vergessbar (entertainment/music), none = idle.
HOLD_HARD: Final = "hard"
HOLD_SOFT: Final = "soft"
HOLD_NONE: Final = "none"

# --------------------------------------------------------------------------- #
# Presence-Gate. media_state klassifiziert NICHT mehr selbst home/away — die
# Presence-Semantik hat genau EINEN Owner: core_state. media_state leitet den
# Away-Gate strikt aus core_states `presence_personal`-Enum ab (`abwesend` →
# away; `zuhause`/`bei_eltern` → home; sonst → kein Gate) — stabile Entity-ID,
# retained seit core_state v0.6.0, keine breite Fallback-Menge, die abweichen
# könnte. Ein kurzer ON-Debounce (AWAY_DEBOUNCE_SECONDS) glättet Rest-
# Transienten, damit ein Sub-N-Sekunden-Dip die Audio-Kette nicht abreißt.
#
# Normalisierte Ausgabe-States des presence_state-Sensors (Contract unverändert):
PRES_HOME: Final = "zuhause"
PRES_AWAY: Final = "abwesend"
PRES_UNKNOWN: Final = "unknown"
# ON-Debounce für den Away-Gate (Sekunden): Away muss so lange stabil anliegen,
# bevor das Media-Gate greift. Rückkehr (→home) wirkt sofort (Musik-Resume).
AWAY_DEBOUNCE_SECONDS: Final = 25.0

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

# PS5-Gaming OFF-Hold (FLEET-262): die Sony-PlayStation-media_player-Integration
# fällt beim Zocken periodisch ~30–35 s auf `unavailable`; der gebundene
# core_devices-Master `sensor.benni_master_ps5` folgt (nicht watt-primär) auf
# `unknown` — obwohl die PS5-Steckdose durchgehend ~200 W meldet. `ps5_on`
# bricht dann kurz ein und reißt Gaming-Szenario + Audio-/Licht-Kette ab. Solange
# der Einbruch NUR aus einer degradierten Quelle (unknown/unavailable) stammt,
# hält der Coordinator `ps5_on` so lange (symmetrisch zu AWAY_DEBOUNCE_SECONDS,
# nur als OFF- statt ON-Debounce). Ein SAUBERES Aus (Quelle meldet definit off)
# räumt sofort. 90 s > beobachtete ~35-s-Dropouts mit Reserve; ein echtes Aus
# während eines Dropouts verzögert das Gaming-Ende um max. dieses Fenster.
# Die eigentliche Wurzel (Master watt-primär) ist FLEET-263 (core_devices/Codex).
PS5_DROPOUT_HOLD_SECONDS: Final = 90.0

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
# der historische ETM-Leerlauf-Fallback; "idle" ist der konfigurierbare
# ETM-Idle-Sentinel ab title_classifier v2.11.0 (Default) — beide zählen wie
# unknown/unavailable/leer als „kein Titel". Fehlte "idle" hier, wertete der
# PC-Gaming-Gate (nur Titel-Ebene) den Leerlauf-String als echten Titel und
# löste fälschlich gaming:pc → entertainment_active → Bias Light aus (v2.11.0).
NO_TITLE_VALUES: Final = frozenset(
    {"", "no game", "idle", "unknown", "unavailable", "none"}
)

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
# FLEET-112: TV-Aktiv-Wahrheit aus dem core_devices-Master (sensor.benni_master_tv).
# Attribut `is_active` fusioniert Watt-Schwelle + Player in EINEM Owner. Ersetzt den
# Eigen-Schwellwert (raw_watt > 0); CONF_TV_ACTIVE/CONF_TV_POWER bleiben nur Fallback.
CONF_TV_MASTER: Final = "tv_master_entity"
# Apple TV
# FLEET-212: sauber getrennt — nativer Media-Player (media_player-Domain) UND
# der core_devices-Master (sensor-Domain). Der Master ist die Aktiv-Wahrheit
# (Attribut `is_active`, spiegelt Player-State + app_id), der Player nur
# Fallback für fremde Anlagen ohne Master. Vorher trug EIN Feld
# (appletv_player_entity) den Master-Sensor, weshalb der media_player-gefilterte
# Selector `sensor.benni_master_appletv` als falsche Domain ablehnte.
CONF_APPLETV_PLAYER: Final = "appletv_player_entity"
CONF_APPLETV_MASTER: Final = "appletv_master_entity"
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
# presence_personal (core_state) = DIE Presence-Entscheidung. media_state leitet
# den Away-Gate strikt aus diesem 3-Wert-Enum ab (kein eigenes Klassifizieren).
CONF_PRESENCE: Final = "presence_entity"
CONF_HOUSEHOLD: Final = "household_entity"
CONF_TRANSITION: Final = "transition_entity"
CONF_DAY_STATE: Final = "day_state_entity"
# private_time-Trigger (FLEET-31: zustandsbasiert ODER manuell). Der MANUELLE
# Trigger ist jetzt eine native switch-Entität dieser Integration (switch.py),
# kein externes input_boolean-Binding mehr → siehe UID_PRIVATE_MANUAL.
CONF_STASH_STREAMS: Final = "stash_streams_entity"
CONF_STASH_ENUM: Final = "stash_enum_entity"      # ETM Stash-Enum (FLEET-43)

# ReBind (FLEET-54): old core_devices Atomics/Combineds are obsolete once a
# device master exists. Keep this map so saved ConfigEntry data/options that
# still contain old source IDs resolve to the canonical master immediately.
LEGACY_ENTITY_REPOINTS: Final[dict[str, str]] = {
    # FLEET-212: `media_player.living_appletv` NICHT mehr auf den Master
    # repointen — das ist jetzt der native Player-Slot (CONF_APPLETV_PLAYER).
    # Ein value-basierter Repoint würde einen korrekt gewählten Player wieder
    # in den Sensor-Master umschreiben und die Domain-Validierung erneut brechen.
    "sensor.benni_device_living_appletv": "sensor.benni_master_appletv",
    "sensor.benni_device_living_tv": "sensor.benni_master_tv",
    "sensor.benni_device_ps5": "sensor.benni_master_ps5",
    "sensor.benni_device_living_switch_plug": "sensor.benni_master_switch",
    "sensor.benni_device_living_pc": "sensor.benni_master_pc",
    "sensor.benni_device_living_avr": "sensor.benni_master_denon",
}

# Keys, deren gebundene Entities der Coordinator beobachtet (event-driven).
WATCH_KEYS: Final[tuple[str, ...]] = (
    CONF_TV_PLAYER, CONF_TV_ACTIVE, CONF_TV_POWER, CONF_TV_MASTER,
    CONF_APPLETV_PLAYER, CONF_APPLETV_MASTER,
    CONF_PS5_PLAYER, CONF_PS5_ACTIVE, CONF_PS5_TITLE, CONF_PS5_RAW, CONF_PS5_ENUM,
    CONF_SWITCH_ACTIVE,
    CONF_PC_ACTIVE, CONF_PC_RAW, CONF_PC_ENUM,
    CONF_DENON_PLAYER, CONF_DENON_ACTIVE,
    CONF_HOMEPODS_PLAYER,
    CONF_MEDIA_ENUM,
    CONF_QUIET_EXTERNAL, CONF_DOOR, CONF_CALL, CONF_ACTIVITY_STATE,
    CONF_STASH_STREAMS, CONF_STASH_ENUM,
    CONF_BIO_STATE, CONF_PRESENCE, CONF_HOUSEHOLD, CONF_TRANSITION, CONF_DAY_STATE,
)

# --------------------------------------------------------------------------- #
# Selector-Domain-Contract (FLEET-212). HA-frei, damit der Config-/Options-Flow
# die Slots konsistent typisiert UND das Verhalten pure testbar ist.
#   PLAYER_KEYS  → native Media-Player: nur `media_player` (lehnt sensor ab).
#   MASTER_KEYS  → core_devices-Master / Aktiv-Quellen: `sensor`/`binary_sensor`
#                  (akzeptiert sensor.benni_master_* UND fremde Bool-Sensoren).
#   Rest         → ungefiltert (volle Flexibilität für fremde Anlagen).
# --------------------------------------------------------------------------- #
PLAYER_DOMAIN: Final[str] = "media_player"
MASTER_DOMAINS: Final[tuple[str, ...]] = ("sensor", "binary_sensor")

PLAYER_KEYS: Final[tuple[str, ...]] = (
    CONF_TV_PLAYER,
    CONF_APPLETV_PLAYER,
    CONF_PS5_PLAYER,
    CONF_DENON_PLAYER,
    CONF_HOMEPODS_PLAYER,
)
MASTER_KEYS: Final[tuple[str, ...]] = (
    CONF_TV_MASTER,
    CONF_APPLETV_MASTER,
    CONF_PS5_ACTIVE,
    CONF_SWITCH_ACTIVE,
    CONF_PC_ACTIVE,
    CONF_DENON_ACTIVE,
)


def source_domain_filter(key: str) -> tuple[str, ...] | None:
    """Erlaubte Entity-Domains für einen Quell-Slot (Selector-Contract).

    None = ungefiltert. Player-Slots liefern nur `media_player` (→ sensor wird
    abgelehnt), Master-Slots `sensor`/`binary_sensor` (→ core_devices-Master
    werden akzeptiert). Bildet 1:1 die EntitySelector-Domain-Filter ab, ist aber
    HA-frei und damit ohne HA-Import testbar.
    """
    if key in PLAYER_KEYS:
        return (PLAYER_DOMAIN,)
    if key in MASTER_KEYS:
        return MASTER_DOMAINS
    return None


# --------------------------------------------------------------------------- #
# Profil-Map (Auto-Bind). benni = Live-IDs der Einhornzentrale.
# Greift nur, wenn die Entity in HA existiert → auf fremden Anlagen schadlos.
# eltern bewusst leer (Anlage existiert noch nicht).
#
# FLEET-52/64/54-Repoint: Die `*_active`-Slots zeigen auf Core-Devices-Master,
# sobald ein Master existiert. Der State ist _bool-kompatibel (active/playing
# = True, off/standby/none = False); gerätespezifische Rohlogik lebt im Master.
# - TV_MASTER (FLEET-112/126): sensor.benni_master_tv ist die Aktiv-Wahrheit;
#   der Coordinator liest `is_active`. TV_ACTIVE bleibt nur manueller Fallback
#   für fremde Anlagen ohne Master und wird im Benni-Profil nicht auto-gebunden.
# - QUIET_EXTERNAL entfällt: Quiet-Detection ist L1 in media_state selbst
#   (FLEET-31); ohne Bindung → quiet_external=None → interne Heuristik greift.
# - ACTIVITY_STATE: Toolbox-Sensor (deprecated) → core_state.
# --------------------------------------------------------------------------- #
PROFILE_PREFILL: Final[dict[str, dict[str, Any]]] = {
    PROFILE_BENNI: {
        CONF_TV_PLAYER: "media_player.living_lgtv",
        CONF_TV_POWER: "sensor.living_tv_plug_power",
        CONF_TV_MASTER: "sensor.benni_master_tv",
        # Apple TV: nativer LAN-Player (Geräte-Wahrheit für Kontext/Verfügbarkeit)
        # + core_devices-Master (Aktiv-Fusion). benni_media#16: die frühere ID
        # `media_player.living_appletv` existiert nach dem Rename nicht mehr (live
        # 404) — Prefill auf die native LAN-Entität `media_player.living_appletv_lan`
        # (Plattform apple_tv) umgestellt. Die MA-geroutete Wiedergabe läuft über
        # `media_player.living_appletv_ma` und ist NICHT die Kontext-/Geräte-Quelle
        # hier; der Master `sensor.benni_master_appletv` ist core_devices-owned
        # (außerhalb dieses Scopes). Hinweis: Prefill wirkt nur für Neu-Bindungen;
        # eine bestehende Live-Bindung auf die alte ID muss Benni per Options-
        # Re-Save nachziehen (Live-Gate).
        CONF_APPLETV_PLAYER: "media_player.living_appletv_lan",
        CONF_APPLETV_MASTER: "sensor.benni_master_appletv",
        CONF_PS5_PLAYER: "media_player.living_ps5",
        CONF_PS5_ACTIVE: "sensor.benni_master_ps5",
        CONF_PS5_TITLE: "sensor.psn_now_playing",
        CONF_PS5_RAW: "sensor.title_classifier_ps5_raw",
        CONF_PS5_ENUM: "sensor.title_classifier_ps5_enum",
        CONF_SWITCH_ACTIVE: "sensor.benni_master_switch",
        CONF_PC_ACTIVE: "sensor.benni_master_pc",
        CONF_PC_RAW: "sensor.title_classifier_pc_raw",
        CONF_PC_ENUM: "sensor.title_classifier_pc_enum",
        CONF_DENON_PLAYER: "media_player.living_denon",
        CONF_DENON_ACTIVE: "sensor.benni_master_denon",
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
        # Dating-/Besuch-Schalter (FLEET-44): jetzt native switch-Entität
        # (switch.py), kein input_boolean-Binding mehr.
    },
    PROFILE_ELTERN: {},
}

# --------------------------------------------------------------------------- #
# Options.
# --------------------------------------------------------------------------- #
CONF_DEBOUNCE: Final = "debounce_seconds"
# benni_media#13 — Trailing-Debounce fuer Aenderungs-Bursts. Er ist KEIN
# Korrektheits-Gate (die Detektion selbst ist zustandsbehaftet und idempotent),
# sondern ein Churn-Schutz: er buendelt einen Burst zu EINEM compute, damit
# media_policy/media_apply nicht pro Einzel-Event neu rechnen.
#
# Belegte Kosten (Recorder, 2026-07-31, TV-Start): sensor.benni_master_tv wurde
# 22:23:39.860 aktiv, media_context wechselte erst 22:23:43.864 auf `tv` — genau
# EIN volles Fenster (4.004 s) auf dem kritischen Pfad, ohne dass ein Burst
# vorlag. Zigbee/Z2M liefert die Leistungs-Reports auf einem 10-s-Raster; die
# Attribut-Updates EINES Geraets treffen innerhalb weniger Millisekunden ein.
# 2.0 s buendeln einen realen Burst also weiterhin vollstaendig, kosten aber
# 2 s weniger Uebergangslatenz.
DEFAULT_DEBOUNCE: Final = 2.0
# TV-only fallback and startup arbitration. Watt is never a primary source
# while the Core Devices TV master is available.
TV_WATT_THRESHOLD_ON: Final[float] = 50.0
TV_START_STABILIZATION_SECONDS: Final[float] = 20.0
# Anti-Starvation-Deckel: jedes Event stiess das Fenster bisher NEU an, ein
# anhaltender Aenderungsstrom konnte den compute daher unbegrenzt verschieben.
# Ab diesem Alter laeuft das Fenster aus, statt weiter verlaengert zu werden —
# der Uebergang wird dadurch deterministisch nach oben begrenzt.
CONF_DEBOUNCE_MAX_WAIT: Final = "debounce_max_wait_seconds"
DEFAULT_DEBOUNCE_MAX_WAIT: Final = 6.0
CONF_DIAGNOSTICS_VERBOSE: Final[str] = "diagnostics_verbose"
DEFAULT_DIAGNOSTICS_VERBOSE: Final[bool] = False

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
    # Presence-Gate (FLEET-212).
    "presence_state": PRES_UNKNOWN,
    "presence_source": None,
    "away_gate": False,
    # Activity-Context-Feed (FLEET-255) — additiv, eigener Sensor + Attr-Bündel.
    "activity_context": ACTX_IDLE,
    "activity_attrs": {},
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
# Activity-Context-Feed (FLEET-255): Media-Hälfte des Activity-States für core_state.
UID_ACTIVITY_CONTEXT: Final[str] = "activity_context"
# binary_sensors
UID_HEADSET_ACTIVE: Final[str] = "headset_active"
UID_ENTERTAINMENT_ACTIVE: Final[str] = "entertainment_active"
UID_QUIET_MODE: Final[str] = "quiet_mode"
# quiet_mode_reason ist ein Sensor (Freitext-Begründung), kein Binary.
UID_QUIET_MODE_REASON: Final[str] = "quiet_mode_reason"
# Presence-Gate (FLEET-212): sichtbarer Presence-State-Sensor + Away-Gate-Binary.
UID_PRESENCE_STATE: Final[str] = "presence_state"
UID_AWAY_GATE: Final[str] = "away_gate"
# Nativer Private-Time-Manual-Schalter (FLEET-44) — ersetzt den externen
# input_boolean. NICHT die Nintendo Switch (die ist CONF_SWITCH_ACTIVE).
UID_PRIVATE_MANUAL: Final[str] = "private_time_manual"
# Auto-Löschung des manuellen private_time-Latch nach Timeout (FLEET-98).
# 0 = nur Einschlaf-Clear, kein Timeout. 4 h wie zuvor in media_apply.
PRIVATE_MANUAL_TIMEOUT_SECONDS: Final[float] = 14400.0
# bio_state-Werte, die als „Einschlafen" den private_time-Latch räumen.
BIO_SLEEP_VALUES: Final[frozenset[str]] = frozenset({"sleep", "asleep"})

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
    # Presence-Gate (FLEET-212) — auch am Haupt-Sensor sichtbar.
    "presence_state",
    "presence_source",
    "away_gate",
    # Private-Time-Diagnose (control#3) — am Haupt-Sensor sichtbar machen:
    # aktiv/inaktiv, Quelle (auto/manual), Eintrittsgrund, blockierter Eintritt.
    "private_time_active",
    "private_source",
    "private_reason",
    "private_blocked_reason",
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
