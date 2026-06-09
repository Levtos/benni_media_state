"""Konstanten von benni_media_state (L1 Context-Feeder).

Eigenständige HA-Integration (eigene Domain). Leitet aus Roh-Quellen einen
Media-Context ab — entscheidet NICHTS (kein Apply). Konsumiert ihre Quellen
AUSSCHLIESSLICH als HA-Entity-IDs aus dem Config-Flow — kein Cross-Modul-
Python-Import (insbesondere keiner zu benni_media_policy).

Step-1-Scaffold: Struktur gespiegelt von benni_light_policy (Hub + Auto-Bind +
WS-Contract + Vanilla-Panel). Fachlogik folgt in Step 2/3.

Lastenheft (Step 3): einhornzentrale/docs/lastenhefte/reviewed/media/
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
# Auto-Bind-Reihenfolge: Override (Config) ▶ Profil-Map (PROFILE_PREFILL) ▶ leer.
# --------------------------------------------------------------------------- #
CONF_PROFILE: Final[str] = "profile"
PROFILE_BENNI: Final[str] = "benni"
PROFILE_ELTERN: Final[str] = "eltern"
PROFILES: Final[list[str]] = [PROFILE_BENNI, PROFILE_ELTERN]
DEFAULT_PROFILE: Final[str] = PROFILE_BENNI
PROFILE_LABELS: Final[dict[str, str]] = {PROFILE_BENNI: "Benni", PROFILE_ELTERN: "Eltern"}

# --------------------------------------------------------------------------- #
# Config-Keys — Roh-Quellen (vorläufig, finalisiert das Lastenheft in Step 3).
# Alle als Entity-IDs aus dem Flow. TODO(step3-lastenheft): Quell-Contract festklopfen.
# --------------------------------------------------------------------------- #
CONF_MEDIA_PLAYERS: Final[str] = "media_player_entities"   # beobachtete media_player.*
CONF_TITLE_CLASSIFIER: Final[str] = "title_classifier_entity"  # Titel→Enum (Gaming-Gate B2)
CONF_HEADSET: Final[str] = "headset_entity"                # Headset-Aktiv-Roh-Signal

# Keys, deren gebundene Entities der Coordinator beobachtet (event-driven).
WATCH_KEYS: Final[tuple[str, ...]] = (
    CONF_MEDIA_PLAYERS,
    CONF_TITLE_CLASSIFIER,
    CONF_HEADSET,
)

# --------------------------------------------------------------------------- #
# Profil-Map (Auto-Bind). Greift nur, wenn die Entity in HA existiert → auf
# fremden Anlagen schadlos. Roh-Geräte sind installations-spezifisch → vorläufig
# leer; der Coordinator fällt sauber auf "leer" zurück (Override ▶ Map ▶ leer).
# TODO(step3-lastenheft): pro Profil die echten Roh-Quellen vorbelegen.
# --------------------------------------------------------------------------- #
PROFILE_PREFILL: Final[dict[str, dict[str, Any]]] = {
    PROFILE_BENNI: {},
    PROFILE_ELTERN: {},
}

# --------------------------------------------------------------------------- #
# Options (Stub — Step-1-Gerüst, leere/Platzhalter-Karten).
# --------------------------------------------------------------------------- #
CONF_DIAGNOSTICS_VERBOSE: Final[str] = "diagnostics_verbose"
DEFAULT_DIAGNOSTICS_VERBOSE: Final[bool] = False

# --------------------------------------------------------------------------- #
# Default-data (bis die Logik existiert — Step 2). Spiegelt das Entity-Roster.
# --------------------------------------------------------------------------- #
DEFAULT_CONTEXT: Final[str] = "idle"
DEFAULT_DATA: Final[dict[str, Any]] = {
    "context": DEFAULT_CONTEXT,
    "subcontext": None,
    "device": None,
    "gaming_source": None,
    "gaming_platform": None,
    "headset_active": False,
    "entertainment_active": False,
    "active_reasons": [],
    # Quiet bleibt L1 (FLEET-31) — Detektion folgt in Phase 3, hier Stub-Defaults.
    "quiet_mode": False,
    "quiet_mode_reason": None,
}

# --------------------------------------------------------------------------- #
# Output-Entity-Roster (vorläufig). uid = unique_id-Suffix, key = Feld in data,
# object_id = gewünschte entity_id (ohne Domain-Prefix der Plattform).
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
