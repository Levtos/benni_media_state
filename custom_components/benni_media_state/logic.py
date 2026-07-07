"""HA-freie Ableitungs-Engine für benni_media_state (L1 Context-Feeder).

Phase 3 (FLEET-30): Context-Teil aus bennis_toolbox/benni_media_context
gecarvt — detect_devices, detect_gaming, detect_streaming, detect_tv und der
Context-Teil von decide. Policy-Teile (compute_volumes, evaluate_subwoofer,
_denon_audio_path, Orchestratoren) sind bewusst NICHT hier (FLEET-5/34).

Abweichungen vom Toolbox-Original (verbindlich per Board):
- B2-Gate FINAL: PC-Gaming ⇔ ETM-Raw-Titel vorhanden ∧ ≠ "No Game"
  (Titel-Ebene). Enum wählt NUR den Sound-Mode-Subcontext (0/1/2) —
  „Enum >= 1 als Gate" ist verworfen.
- R6: PS5 an + Titel leer (Menü) → gaming_grind als Default. Titel leer
  WÄHREND einer Session → letzter Subcontext sticky (Coordinator reicht ihn
  als `sticky_gaming_sub` herein).
- FLEET-31: Quiet ist vom Szenario ENTKOPPELT — evaluate_quiet liefert nur
  quiet_mode/_reason, schaltet aber KEINEN Context mehr (die Toolbox-Kopplung
  quiet → CTX_PRIVATE ist gestrichen).
- FLEET-31: private_time hat eine eigene Trigger-Quelle, ODER-verknüpft:
  Stash-Streams > 0 ODER ETM-Stash-Enum >= 1 (FLEET-43) ODER manueller
  Schalter. Priorität: private_time > gaming > streaming/tv > idle.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .const import (
    ACTX_ENTERTAINMENT,
    ACTX_GAMING,
    ACTX_IDLE,
    ACTX_MUSIC,
    ACTX_PRIVATE,
    APPLETV_SYSTEM_APPS,
    CTX_GAMING,
    CTX_IDLE,
    CTX_PRIVATE,
    CTX_STREAMING,
    CTX_TV,
    HOLD_HARD,
    HOLD_NONE,
    HOLD_SOFT,
    DEFAULT_APPLETV_APP_MAP,
    DEV_APPLETV,
    DEV_DENON,
    DEV_HOMEPODS,
    DEV_NONE,
    DEV_PC,
    DEV_PS5,
    DEV_SWITCH,
    DEV_TV,
    ENUM_GAME_GRIND,
    ENUM_GAME_HEADSET,
    ENUM_MEDIA_MUTE,
    GP_NONE,
    GP_PC,
    GP_PS5,
    GP_SWITCH,
    GS_NONE,
    GS_PC,
    GS_TV,
    BIO_SLEEP_VALUES,
    NO_TITLE_VALUES,
    PRES_AWAY,
    PRES_HOME,
    PRES_UNKNOWN,
    SUB_GAME_DEFAULT,
    SUB_GAME_GRIND,
    SUB_GAME_HEADSET,
    SUB_NONE,
    SUB_STR_DEFAULT,
    SUB_TV_DEFAULT,
    TV_SOURCE_MAP,
)


@dataclass(frozen=True)
class Inputs:
    """Snapshot der Roh-Quellen für eine Ableitung. None = unknown/nicht gebunden."""

    # TV
    tv_active: bool = False
    tv_source: Optional[str] = None
    tv_power: Optional[bool] = None
    # Apple TV
    atv_state: Optional[str] = None        # playing/paused/idle/off/standby
    atv_app_id: Optional[str] = None
    # PS5
    ps5_on: bool = False
    ps5_title: Optional[str] = None        # PSN-Now-Playing (Fallback zur ETM-Raw)
    ps5_raw: Optional[str] = None          # ETM Raw-Title
    ps5_enum: int = 0
    # Switch
    switch_dock: bool = False
    # PC
    pc_active: bool = False                # Plug-Plausibilität (Device-Ebene)
    pc_raw: Optional[str] = None           # ETM Raw-Title (B2-Gate)
    pc_enum: int = 0
    # Denon / HomePods
    denon_active: bool = False
    homepods_playing: bool = False
    # Musik-/Media-Enum (musikkatalog): 2 = Mute → Quiet
    media_enum: int = 0
    # Quiet-Inputs
    quiet_external: Optional[bool] = None  # None = nicht konfiguriert → Heuristik
    door_open: bool = False
    call_active: bool = False
    activity_state: Optional[str] = None
    # Presence-Gate: core_state ist alleiniger Owner. `presence` = Roh-Quelle
    # (core_state presence_personal) NUR fürs Cockpit-Display. Die Entscheidung
    # kommt aus `binary_sensor.benni_core_state_away`: `away_raw` = dessen roher
    # Boolean (None = ungebunden/unknown → kein Gate), `away_gated` = derselbe
    # Boolean nach ON-Debounce (Coordinator). Nur `away_gated` schaltet.
    presence: Optional[str] = None
    away_raw: Optional[bool] = None
    away_gated: bool = False
    # private_time-Trigger (FLEET-31)
    stash_streams: Optional[int] = None
    stash_enum: Optional[int] = None
    private_manual: bool = False
    # Manueller Subcontext-Override (Service, optional)
    manual_nudge: Optional[str] = None


@dataclass
class MediaState:
    """Abgeleiteter Media-Context. Spiegelt das Entity-Roster."""

    context: str = CTX_IDLE
    subcontext: str = SUB_NONE
    device: str = DEV_NONE
    gaming_source: str = GS_NONE
    gaming_platform: str = GP_NONE
    headset_active: bool = False
    entertainment_active: bool = False
    active_reasons: list = field(default_factory=list)
    # Quiet bleibt L1 (FLEET-31) — entkoppelt vom Szenario.
    quiet_mode: bool = False
    quiet_mode_reason: Optional[str] = None
    # Presence-Gate (FLEET-212): normalisierter Presence-State + Roh-Quelle +
    # ob Abwesenheit die Medienlogik gerade hart deaktiviert (Diagnose).
    presence_state: str = PRES_UNKNOWN
    presence_source: Optional[str] = None
    away_gate: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "context": self.context,
            "subcontext": self.subcontext,
            "device": self.device,
            "gaming_source": self.gaming_source,
            "gaming_platform": self.gaming_platform,
            "headset_active": self.headset_active,
            "entertainment_active": self.entertainment_active,
            "active_reasons": list(self.active_reasons),
            "quiet_mode": self.quiet_mode,
            "quiet_mode_reason": self.quiet_mode_reason,
            "presence_state": self.presence_state,
            "presence_source": self.presence_source,
            "away_gate": self.away_gate,
        }


# --------------------------------------------------------------------------- #
# Titel-Ebene (B2-Gate)
# --------------------------------------------------------------------------- #
def title_present(raw: Optional[str]) -> bool:
    """True, wenn der ETM-Raw-Sensor einen echten Titel zeigt.

    "No Game" ist der ETM-Leerlauf-/Offline-Fallback (live verifiziert) —
    zählt wie unknown/unavailable/leer als „kein Titel"."""
    if raw is None:
        return False
    return str(raw).strip().lower() not in NO_TITLE_VALUES


# --------------------------------------------------------------------------- #
# Presence-Gate — echo core_state, no own classification.
# --------------------------------------------------------------------------- #
def away_from_presence(presence: Optional[str]) -> Optional[bool]:
    """core_state presence_personal → Away-Boolean. KEINE eigene Detektion.

    Bindet sich strikt an core_states 3-Wert-Enum (`zuhause`/`bei_eltern`/
    `abwesend`) statt an eine breite Fallback-Menge — so kann media_state nie
    von core_states Entscheidung abweichen (Wurzel des alten bei_eltern-Bugs).
    `abwesend` → away; `zuhause`/`bei_eltern` → home; alles andere (None/
    unknown/unavailable/Fremdwert) → None = kein Gate (kein Fehl-Stop).
    """
    if presence is None:
        return None
    v = str(presence).strip().lower()
    if v == PRES_AWAY:
        return True
    if v in (PRES_HOME, "bei_eltern"):
        return False
    return None


def gate_away(
    raw_away: Optional[bool],
    away_since: Optional[float],
    now: float,
    debounce_s: float,
) -> tuple[bool, Optional[float]]:
    """ON-Debounce für den Away-Gate. Pure + testbar.

    Away (`raw_away is True`) muss ``debounce_s`` durchgehend anliegen, bevor
    das Gate greift — ein transienter Away-Dip reißt so die Audio-Kette nicht
    ab. Jeder Nicht-Away-Tick (`False`/`None`) setzt den Timer zurück und öffnet
    das Gate sofort (Musik-Resume bei Rückkehr wirkt ohne Verzögerung).

    Return: ``(gated_away, new_away_since)`` — ``away_since`` als monotone
    Startzeit weiterreichen (Coordinator hält sie als Instanz-State).
    """
    if raw_away is True:
        since = away_since if away_since is not None else now
        return (now - since) >= debounce_s, since
    return False, None


def presence_state_from_away(raw_away: Optional[bool], gated_away: bool) -> str:
    """Cockpit-Presence-State aus dem core_state-Away-Gate.

    `gated_away` → abwesend. Sonst: ungebunden/unknown (`raw_away is None`) →
    unknown (kein Fehl-Stop), sonst zuhause. Keine eigene Semantik — bei_eltern
    ist bereits im core_state-Gate als home (off) kodiert.
    """
    if gated_away:
        return PRES_AWAY
    if raw_away is None:
        return PRES_UNKNOWN
    return PRES_HOME


def should_clear_private_on_sleep(
    bio_state: Optional[str], last_bio_state: Optional[str], private_manual: bool
) -> bool:
    """FLEET-98: Der manuelle private_time-Latch wird beim Einschlafen geräumt
    (du schläfst = kein Dating/Besuch). Nur auf der FLANKE in einen Sleep-Wert,
    damit ein durchgehender Sleep-State ihn nicht dauerhaft blockiert."""
    if not private_manual:
        return False
    b = (bio_state or "").strip().lower()
    lb = (last_bio_state or "").strip().lower()
    return b in BIO_SLEEP_VALUES and lb not in BIO_SLEEP_VALUES


# --------------------------------------------------------------------------- #
# Quiet (Detection bleibt L1 — schaltet KEIN Szenario, FLEET-31)
# --------------------------------------------------------------------------- #
def evaluate_quiet(inp: Inputs) -> tuple[bool, Optional[str]]:
    # Explizites externes Signal (wenn konfiguriert) gewinnt über die Heuristik.
    if inp.quiet_external is True:
        return True, "quiet_mode_external"
    if inp.quiet_external is False:
        return False, None
    if inp.call_active:
        return True, "call_active"
    if inp.door_open:
        return True, "door_open"
    if inp.media_enum == ENUM_MEDIA_MUTE:
        return True, "classifier_media_mute"
    if inp.activity_state in ("sleep", "asleep", "quiet"):
        return True, f"activity_{inp.activity_state}"
    return False, None


# --------------------------------------------------------------------------- #
# private_time (FLEET-31: zustandsbasiert ODER manuell — ODER-verknüpft)
# --------------------------------------------------------------------------- #
def detect_private(inp: Inputs) -> Optional[str]:
    """Trigger-Grund für private_time oder None."""
    if inp.stash_streams is not None and inp.stash_streams > 0:
        return "stash_streams"
    if inp.stash_enum is not None and inp.stash_enum >= 1:
        return "stash_classifier"
    if inp.private_manual:
        return "manual_switch"
    return None


# --------------------------------------------------------------------------- #
# Geräte-Priorität (höchstes gewinnt für das primäre "device")
# Reihenfolge: ATV > TV > PS5 > Switch > PC > Denon > HomePods
# --------------------------------------------------------------------------- #
APPLETV_ACTIVE_STATES = ("playing", "paused", "idle")


def appletv_active(state: Optional[str]) -> bool:
    return state in APPLETV_ACTIVE_STATES


def detect_devices(inp: Inputs) -> list[str]:
    devs = []
    if appletv_active(inp.atv_state):
        devs.append(DEV_APPLETV)
    if inp.tv_active or inp.tv_power:
        devs.append(DEV_TV)
    if inp.ps5_on:
        devs.append(DEV_PS5)
    if inp.switch_dock:
        devs.append(DEV_SWITCH)
    if inp.pc_active:
        devs.append(DEV_PC)
    if inp.denon_active:
        devs.append(DEV_DENON)
    if inp.homepods_playing:
        devs.append(DEV_HOMEPODS)
    return devs


# --------------------------------------------------------------------------- #
# Gaming (B2 FINAL + R6)
# --------------------------------------------------------------------------- #
def _sub_from_enum(enum_val: int) -> str:
    if enum_val == ENUM_GAME_GRIND:
        return SUB_GAME_GRIND
    if enum_val == ENUM_GAME_HEADSET:
        return SUB_GAME_HEADSET
    return SUB_GAME_DEFAULT


def detect_gaming(
    inp: Inputs, sticky_gaming_sub: Optional[str] = None
) -> Optional[tuple[str, str, str, bool]]:
    """Return (subcontext, gaming_source, gaming_platform, headset_active) oder None.

    - PS5: Gerät an ⇒ Gaming-Szenario (Geräte-Ebene). Titel/Enum verfeinern nur
      den Subcontext. R6: kein Titel (Menü) → gaming_grind; lief schon eine
      Session (sticky_gaming_sub gesetzt) → letzten Subcontext halten.
    - Switch: gedockt ⇒ gaming_default (kein Titel-Signal).
    - PC: NUR über die Titel-Ebene — ETM-Raw vorhanden ∧ ≠ "No Game" (B2-Gate).
      pc_active (Plug) allein ist KEIN Gaming (das war der B2-Bug).
    """
    if inp.ps5_on:
        has_title = title_present(inp.ps5_raw) or bool(
            inp.ps5_title and str(inp.ps5_title).strip()
        )
        if has_title:
            sub = _sub_from_enum(inp.ps5_enum)
        elif sticky_gaming_sub is not None:
            # R6-Edge: Titel fällt WÄHREND der Session weg → sticky halten.
            sub = sticky_gaming_sub
        else:
            # R6: PS5 an, kein Titel (Menü) → grind, nicht default.
            sub = SUB_GAME_GRIND
        return sub, GS_TV, GP_PS5, sub == SUB_GAME_HEADSET
    if inp.switch_dock:
        return SUB_GAME_DEFAULT, GS_TV, GP_SWITCH, False
    if title_present(inp.pc_raw):
        sub = _sub_from_enum(inp.pc_enum)
        return sub, GS_PC, GP_PC, sub == SUB_GAME_HEADSET
    return None


# --------------------------------------------------------------------------- #
# Streaming via Apple TV
# --------------------------------------------------------------------------- #
def detect_streaming(inp: Inputs, app_map: dict[str, str]) -> Optional[str]:
    if not appletv_active(inp.atv_state):
        return None
    app = inp.atv_app_id
    if app is None:
        return SUB_STR_DEFAULT
    if app in APPLETV_SYSTEM_APPS:
        return None  # signalisiert Rollback aufs Pre-ATV-Szenario
    return app_map.get(app, SUB_STR_DEFAULT)


# --------------------------------------------------------------------------- #
# TV (Broadcast)
# --------------------------------------------------------------------------- #
def detect_tv(inp: Inputs) -> Optional[str]:
    if not (inp.tv_active or inp.tv_power):
        return None
    if inp.tv_source and inp.tv_source in TV_SOURCE_MAP:
        return TV_SOURCE_MAP[inp.tv_source]
    return SUB_TV_DEFAULT


# --------------------------------------------------------------------------- #
# Master-Entscheidung (nur Context — keine Volumes/Subwoofer, FLEET-5/34)
# --------------------------------------------------------------------------- #
def decide(
    inp: Inputs,
    app_map: Optional[dict[str, str]] = None,
    pre_atv: Optional[tuple[str, str]] = None,
    sticky_gaming_sub: Optional[str] = None,
) -> MediaState:
    """Leitet den Media-Context aus den Roh-Quellen ab. Entscheidet keine Aktion.

    `pre_atv` = (context, subcontext) vor ATV-Aktivierung (System-App-Rollback);
    `sticky_gaming_sub` = letzter Gaming-Subcontext der laufenden PS5-Session
    (R6-Edge). Beides hält der Coordinator — die Funktion bleibt pure.
    """
    if app_map is None:
        app_map = DEFAULT_APPLETV_APP_MAP
    d = MediaState()
    reasons: list[str] = []

    # Quiet: nur Detection — schaltet KEIN Szenario (FLEET-31).
    quiet, qreason = evaluate_quiet(inp)
    d.quiet_mode = quiet
    d.quiet_mode_reason = qreason
    if quiet:
        reasons.append(f"quiet:{qreason}")

    devices = detect_devices(inp)
    d.device = devices[0] if devices else DEV_NONE

    # Presence-Gate: Abwesenheit deaktiviert JEDE aktive Medienlogik. Höchste
    # Priorität — überstimmt private_time/gaming/streaming/tv. Das Gerät bleibt
    # zur Observability erkannt (Cockpit sieht, dass z.B. der TV noch an ist),
    # aber Szenario→idle + entertainment_active=False signalisieren dem
    # Apply-Layer, laufende Musik/Entertainment zu stoppen. Die Away-Wahrheit ist
    # der debouncte core_state-Gate (`away_gated`); `unknown`/nicht gebunden
    # greift NICHT (kein Fehl-Stop bei Sensor-Aussetzern).
    d.presence_state = presence_state_from_away(inp.away_raw, inp.away_gated)
    d.presence_source = inp.presence
    if inp.away_gated:
        d.away_gate = True
        d.context = CTX_IDLE
        d.subcontext = SUB_NONE
        d.gaming_source = GS_NONE
        d.gaming_platform = GP_NONE
        d.headset_active = False
        d.entertainment_active = False
        reasons.append("away_gate")
        d.active_reasons = reasons
        return d

    # private_time hat höchste Szenario-Priorität (Lastenheft:
    # private_time > gaming > streaming/tv > idle).
    private_reason = detect_private(inp)
    if private_reason is not None:
        d.context = CTX_PRIVATE
        d.subcontext = SUB_NONE
        reasons.append(f"private:{private_reason}")
    elif inp.manual_nudge:
        d.subcontext = inp.manual_nudge
        if inp.manual_nudge.startswith("tv_"):
            d.context = CTX_TV
        elif inp.manual_nudge.startswith("streaming_"):
            d.context = CTX_STREAMING
        elif inp.manual_nudge.startswith("gaming_"):
            d.context = CTX_GAMING
        reasons.append(f"manual_nudge:{inp.manual_nudge}")

    if d.context == CTX_IDLE:
        # Gaming gewinnt über passives TV/Streaming.
        g = detect_gaming(inp, sticky_gaming_sub)
        if g is not None:
            sub, gs, gp, headset = g
            d.context = CTX_GAMING
            d.subcontext = sub
            d.gaming_source = gs
            d.gaming_platform = gp
            d.headset_active = headset
            reasons.append(f"gaming:{gp}")
        else:
            stream_sub = detect_streaming(inp, app_map)
            if stream_sub is not None:
                d.context = CTX_STREAMING
                d.subcontext = stream_sub
                reasons.append(f"streaming:{inp.atv_app_id}")
            elif (
                appletv_active(inp.atv_state)
                and inp.atv_app_id in APPLETV_SYSTEM_APPS
            ):
                # System-App → Rollback aufs Pre-ATV-Szenario.
                if pre_atv is not None:
                    d.context, d.subcontext = pre_atv
                    reasons.append("atv_system_app_rollback")
                else:
                    d.context = CTX_IDLE
                    reasons.append("atv_system_app_no_prior")
            else:
                tv_sub = detect_tv(inp)
                if tv_sub is not None:
                    d.context = CTX_TV
                    d.subcontext = tv_sub
                    reasons.append(f"tv:{inp.tv_source}")
                elif inp.homepods_playing or inp.denon_active:
                    # Reines Audio (HomePods-/Denon-Musik) ist KEIN Screen-Szenario
                    # → idle. Owner/Volume regelt media_policy über homepods_playing;
                    # entertainment_active bleibt false → kein Cinema/TV-Glare im Licht.
                    # (streaming = TV+AppleTV, §4.1 — Audio darf den Lichtkontext nicht
                    # auf Cinema kippen. FLEET-36 Cut-over hat den Fehlmapping aufgedeckt.)
                    d.context = CTX_IDLE
                    d.subcontext = SUB_NONE
                    reasons.append("audio_only_idle")
                else:
                    d.context = CTX_IDLE
                    d.subcontext = SUB_NONE

    d.entertainment_active = d.context in (CTX_TV, CTX_STREAMING, CTX_GAMING)
    d.active_reasons = reasons
    return d


# --------------------------------------------------------------------------- #
# Activity-Context-Feed (FLEET-255) — Media-Hälfte des Activity-States für
# core_state. Additiv: leitet aus dem BEREITS berechneten MediaState + den
# Roh-Inputs ab, ändert media_context/decide() nicht.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ActivityContext:
    """Ergebnis des Media-Activity-Feeds: State + Diagnose + Consumer-Attribute."""

    state: str
    reason: str
    hold_strength: str
    attrs: dict[str, Any]


def derive_activity_context(state: MediaState, inp: Inputs) -> ActivityContext:
    """Media-Hälfte des Activity-States für core_state (FLEET-255).

    Feed-interne Priorität: private_time > gaming > entertainment > music > idle.

    Der einzige inhaltliche Unterschied zu ``media_context``: reines Audio
    (HomePods playing / Denon active), das ``decide()`` bewusst als ``idle`` /
    ``audio_only_idle`` führt (Licht-/Scene-Schutz, §4.1), wird HIER als
    ``music`` sichtbar. Alle Screen-Szenarien werden 1:1 aus dem schon
    berechneten ``state`` übernommen — keine Zweit-Detektion.

    Der Away-Gate hat Vorrang (→ ``idle``), spiegelt ``media_context``: bei
    Abwesenheit ist die Medienlogik hart deaktiviert.

    Kein Rückgriff auf core_state ``activity_state`` oder ``presence_effective``
    — nur ``state`` (aus Roh-Media + rohem Away-Gate) und ``inp`` fließen ein.
    """
    music_active = bool(inp.homepods_playing or inp.denon_active)
    private_active = state.context == CTX_PRIVATE and not state.away_gate

    def _result(feed_state: str, reason: str, hold: str) -> ActivityContext:
        attrs = {
            "reason": reason,
            "hold_strength": hold,
            "device": state.device,
            "media_device": state.device,
            "media_context": state.context,
            "media_subcontext": state.subcontext,
            "gaming_platform": state.gaming_platform,
            "gaming_source": state.gaming_source,
            "private_time_active": private_active,
            "entertainment_active": bool(state.entertainment_active),
            "music_active": music_active,
            "homepods_playing": bool(inp.homepods_playing),
            "denon_active": bool(inp.denon_active),
        }
        return ActivityContext(feed_state, reason, hold, attrs)

    # Away-Gate zuerst: spiegelt media_context (alles idle bei Abwesenheit).
    if state.away_gate:
        return _result(ACTX_IDLE, "away_gate", HOLD_NONE)
    # private_time: reiche bestehende Erkennung (Stash-Streams/-Enum/Manual)
    # steckt schon in decide() → state.context == CTX_PRIVATE. Grund aus den
    # bestehenden active_reasons durchreichen.
    if state.context == CTX_PRIVATE:
        reason = next(
            (r for r in state.active_reasons if r.startswith("private:")),
            "private:context",
        )
        return _result(ACTX_PRIVATE, reason, HOLD_HARD)
    if state.context == CTX_GAMING:
        return _result(ACTX_GAMING, f"gaming:{state.gaming_platform}", HOLD_HARD)
    if state.context in (CTX_TV, CTX_STREAMING):
        return _result(ACTX_ENTERTAINMENT, f"entertainment:{state.context}", HOLD_SOFT)
    if music_active:
        reason = "music:homepods" if inp.homepods_playing else "music:denon"
        return _result(ACTX_MUSIC, reason, HOLD_SOFT)
    return _result(ACTX_IDLE, "idle", HOLD_NONE)
