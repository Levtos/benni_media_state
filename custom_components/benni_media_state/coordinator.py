"""Media-State-Coordinator (Single-Instance, event-driven + Debounce).

DataUpdateCoordinator ohne Polling (`update_interval=None`): State-Changes der
gebundenen Quell-Entities werden über einen Debounce (Default 4 s, Option)
gesammelt und dann EINMAL neu gerechnet — wie der Toolbox-Vorgänger, aber ohne
dessen 30-s-Poll.

Profil-Hub (benni/eltern) + Auto-Bind (core_state-Blaupause):
Binding-Auflösung = options ▶ data ▶ PROFILE_PREFILL[profile].

Phase 3 (FLEET-30): baut den vollen Context-Snapshot (TV/ATV/PS5/Switch/PC/
Denon/HomePods + ETM-Raw/Enum + Quiet- und private_time-Inputs) und hält die
zwei zustandsbehafteten Krücken, damit logic.decide() pure bleibt:
- `_pre_atv`: letztes Nicht-ATV-Szenario (System-App-Rollback),
- `_sticky_gaming_sub`: letzter PS5-Subcontext der laufenden Session (R6-Edge).
"""
from __future__ import annotations

import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import logic
from .const import (
    AWAY_DEBOUNCE_SECONDS,
    CONF_ACTIVITY_STATE,
    CONF_APPLETV_MASTER,
    CONF_APPLETV_PLAYER,
    CONF_BIO_STATE,
    CONF_CALL,
    CONF_DAY_STATE,
    CONF_DEBOUNCE,
    CONF_DEBOUNCE_MAX_WAIT,
    CONF_DENON_ACTIVE,
    CONF_DENON_PLAYER,
    CONF_DOOR,
    CONF_HOMEPODS_PLAYER,
    CONF_HOUSEHOLD,
    CONF_MEDIA_ENUM,
    CONF_PC_ACTIVE,
    CONF_PC_ENUM,
    CONF_PC_RAW,
    CONF_PRESENCE,
    CONF_PROFILE,
    CONF_PS5_ACTIVE,
    CONF_PS5_ENUM,
    CONF_PS5_PLAYER,
    CONF_PS5_RAW,
    CONF_PS5_TITLE,
    CONF_QUIET_EXTERNAL,
    CONF_STASH_ENUM,
    CONF_STASH_STREAMS,
    CONF_SWITCH_ACTIVE,
    CONF_TRANSITION,
    CONF_TV_ACTIVE,
    CONF_TV_MASTER,
    CONF_TV_PLAYER,
    CONF_TV_POWER,
    CTX_GAMING,
    CTX_STREAMING,
    DEFAULT_DEBOUNCE,
    DEFAULT_DEBOUNCE_MAX_WAIT,
    DEFAULT_PROFILE,
    DEV_APPLETV,
    DOMAIN,
    GP_PS5,
    LEGACY_ENTITY_REPOINTS,
    PRIVATE_MANUAL_TIMEOUT_SECONDS,
    PROFILE_PREFILL,
    PROFILES,
    PS5_DROPOUT_HOLD_SECONDS,
    TV_START_STABILIZATION_SECONDS,
    WATCH_KEYS,
)

_LOGGER = logging.getLogger(__name__)
_STORE_VERSION = 1

_TRUE_STATES = frozenset({"on", "true", "1", "home", "active", "playing", "open"})


def _bool(s: str | None) -> bool:
    return s is not None and s.lower() in _TRUE_STATES


def _opt_bool(s: str | None) -> bool | None:
    """None bleibt None (= Entity nicht gebunden/unavailable)."""
    if s is None:
        return None
    return s.lower() in _TRUE_STATES


def _int(s: str | None, default: int = 0) -> int:
    if s is None:
        return default
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return default


def _opt_int(s: str | None) -> int | None:
    if s is None:
        return None
    try:
        return int(float(s))
    except (TypeError, ValueError):
        return None


class MediaStateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Eine Instanz pro Config-Entry (Single-Instance-Modell)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        profile = entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
        self._profile = profile if profile in PROFILES else DEFAULT_PROFILE
        self._cancel_debounce: CALLBACK_TYPE | None = None
        # benni_media#13: Startzeit des laufenden Debounce-Fensters (monotone
        # Uhr) fuer den Anti-Starvation-Deckel; ueberlebt das Re-Arm.
        self._debounce_started: float | None = None
        # OQ-2: Pre-ATV-Snapshot über Neustarts persistieren (R7-Rollback überlebt
        # HA-Restart, statt nur RAM). Debounced-Save via Store.
        self._store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}_{entry.entry_id}_state")
        # Zustandskrücken für die pure decide() (siehe Modul-Docstring).
        self._pre_atv: tuple[str, str] | None = None
        self._sticky_gaming_sub: str | None = None
        # Manueller Subcontext-Override (Service-Fläche, optional).
        self._manual_nudge: str | None = None
        # Away-Gate ON-Debounce: monotone Startzeit des aktuellen Away-Fensters.
        self._away_since: float | None = None
        # PS5-Gaming OFF-Hold (FLEET-262): Monotone des letzten echten ps5_on —
        # überbrückt PlayStation-media_player-Dropouts (~30 s), damit Gaming die
        # Audio-/Licht-Kette nicht abreißt. Siehe logic.hold_ps5_on.
        self._ps5_on_since: float | None = None
        # TV-Start-Stabilisierung: ein TV-Signal wird erst nach 20 s als TV-
        # Kontext zugelassen; ein sauberes Off verwirft das Fenster.
        self._tv_start_since: float | None = None
        # Nativer private_time-Manual-Latch (FLEET-44/98): Zustand + Auto-Clear.
        # Gesetzt/gelesen über die switch-Entität (switch.py); Auto-Clear bei
        # Einschlaf-Flanke (bio_state) und nach Timeout.
        self._private_manual: bool = False
        self._private_timeout_unsub: CALLBACK_TYPE | None = None
        self._last_bio_state: str | None = None
        # control#3: PC-Aus-Flanke räumt den manuellen private_time-Latch.
        self._last_pc_active: bool | None = None

    # ----- profile / binding -----
    @property
    def profile(self) -> str:
        return self._profile

    @property
    def _opts(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    @property
    def debounce_seconds(self) -> float:
        try:
            return max(0.0, float(self._opts.get(CONF_DEBOUNCE, DEFAULT_DEBOUNCE)))
        except (TypeError, ValueError):
            return DEFAULT_DEBOUNCE

    @property
    def debounce_max_wait_seconds(self) -> float:
        """benni_media#13: Obergrenze fuers Verlaengern des Debounce-Fensters."""
        try:
            return max(
                0.0,
                float(self._opts.get(CONF_DEBOUNCE_MAX_WAIT, DEFAULT_DEBOUNCE_MAX_WAIT)),
            )
        except (TypeError, ValueError):
            return DEFAULT_DEBOUNCE_MAX_WAIT

    def _entity_id(self, key: str) -> Any:
        """Auto-Bind (core_state-Blaupause): options ▶ data ▶ PROFILE_PREFILL[profile]."""
        val = (
            self.entry.options.get(key)
            or self.entry.data.get(key)
            or PROFILE_PREFILL.get(self._profile, {}).get(key)
        )
        if isinstance(val, str):
            return LEGACY_ENTITY_REPOINTS.get(val, val)
        return val

    def _watched_entities(self) -> list[str]:
        ids: list[str] = []
        for key in WATCH_KEYS:
            val = self._entity_id(key)
            if isinstance(val, str) and val:
                ids.append(val)
            elif isinstance(val, (list, tuple)):
                ids.extend(e for e in val if isinstance(e, str) and e)
        return list(dict.fromkeys(ids))

    def bindings(self) -> dict[str, Any]:
        """Aktuelle Auflösung aller WATCH_KEYS — für Panel/Diagnose."""
        return {key: self._entity_id(key) for key in WATCH_KEYS}

    # ----- persistence (OQ-2: Pre-ATV-Snapshot) -----
    async def async_load_persisted(self) -> None:
        """Persistierten Pre-ATV-Snapshot laden (vor dem ersten Refresh aufrufen)."""
        try:
            data = await self._store.async_load()
        except Exception as err:  # noqa: BLE001 — Persistenz darf Setup nie blocken
            _LOGGER.warning("media_state: pre_atv load failed: %s", err)
            return
        pa = data.get("pre_atv") if isinstance(data, dict) else None
        if isinstance(pa, (list, tuple)) and len(pa) == 2:
            self._pre_atv = (str(pa[0]), str(pa[1]))
            _LOGGER.debug("media_state: pre_atv restored = %s", self._pre_atv)

    @callback
    def _persist_pre_atv(self) -> None:
        """Debounced-Save (5 s) — schreibt nur nach Ruhephasen, nicht pro Tick."""
        self._store.async_delay_save(
            lambda: {"pre_atv": list(self._pre_atv) if self._pre_atv else None}, 5.0
        )

    # ----- lifecycle -----
    @callback
    def async_start(self) -> None:
        watched = self._watched_entities()
        if watched:
            self.entry.async_on_unload(
                async_track_state_change_event(self.hass, watched, self._on_state_change)
            )
        self.entry.async_on_unload(self._cancel_pending)
        self.entry.async_on_unload(self._cancel_private_timeout)

    @callback
    def _cancel_pending(self) -> None:
        if self._cancel_debounce is not None:
            self._cancel_debounce()
            self._cancel_debounce = None
        self._debounce_started = None

    @callback
    def _on_state_change(self, _event: Event) -> None:
        """Debounce: Änderungs-Burst sammeln, dann einmal rechnen.

        benni_media#13: Das Fenster wird weiterhin bei jedem Event neu angestossen
        (so buendelt es den Burst), ABER nur bis `debounce_max_wait_seconds`. Ein
        anhaltender Aenderungsstrom kann den compute damit nicht mehr unbegrenzt
        verschieben — der Uebergang ist nach oben begrenzt und deterministisch.
        """
        delay = self.debounce_seconds
        if delay <= 0:
            self._cancel_pending()
            self.async_set_updated_data(self._compute())
            return
        now = time.monotonic()
        age = None if self._debounce_started is None else now - self._debounce_started
        if not logic.debounce_rearm(
            self._cancel_debounce is not None, age, self.debounce_max_wait_seconds
        ):
            # Deckel erreicht: laufendes Fenster NICHT verlaengern.
            return
        started = self._debounce_started
        self._cancel_pending()
        self._debounce_started = started if started is not None else now
        self._cancel_debounce = async_call_later(self.hass, delay, self._on_debounce)

    @callback
    def _on_debounce(self, _now) -> None:
        self._cancel_debounce = None
        self._debounce_started = None
        self.async_set_updated_data(self._compute())

    # ----- service surface -----
    async def async_set_manual_nudge(self, subcontext: str | None) -> None:
        self._manual_nudge = subcontext or None
        self.async_set_updated_data(self._compute())

    # ----- private_time manual latch (native switch, FLEET-44/98) -----
    @property
    def private_manual(self) -> bool:
        return self._private_manual

    def restore_private_manual(self, on: bool) -> None:
        """Persistenten Zustand beim Start übernehmen (aus RestoreEntity)."""
        self._private_manual = on
        if on:
            self._schedule_private_timeout()
        self.async_set_updated_data(self._compute())

    async def async_set_private_manual(self, on: bool) -> None:
        """Von der switch-Entität aufgerufen (turn_on/off)."""
        self._private_manual = on
        self._cancel_private_timeout()
        if on:
            self._schedule_private_timeout()
        self.async_set_updated_data(self._compute())

    @callback
    def _schedule_private_timeout(self) -> None:
        self._cancel_private_timeout()
        if PRIVATE_MANUAL_TIMEOUT_SECONDS <= 0:   # 0 = nur Einschlaf-Clear
            return
        self._private_timeout_unsub = async_call_later(
            self.hass, PRIVATE_MANUAL_TIMEOUT_SECONDS, self._on_private_timeout
        )

    @callback
    def _cancel_private_timeout(self) -> None:
        if self._private_timeout_unsub is not None:
            self._private_timeout_unsub()
            self._private_timeout_unsub = None

    @callback
    def _on_private_timeout(self, _now) -> None:
        self._private_timeout_unsub = None
        if self._private_manual:
            _LOGGER.info("media_state: private_time-Latch Timeout → auto-clear")
            self._private_manual = False
            self.async_set_updated_data(self._compute())

    # ----- reads -----
    def _state(self, key: str) -> str | None:
        eid = self._entity_id(key)
        if not eid:
            return None
        st = self.hass.states.get(eid)
        if st is None or st.state in ("unknown", "unavailable"):
            return None
        return st.state

    def _raw_state(self, key: str) -> str | None:
        """Roh-State inkl. unknown/unavailable (None nur wenn Entität fehlt/ungebunden).

        Anders als `_state` behält dies die Unterscheidung ``off`` (sauberes Aus)
        vs. ``unavailable``/``unknown`` (Quell-Dropout) — nötig für den PS5-Hold
        (FLEET-262), damit ein echtes Ausschalten sofort räumt, ein Integrations-
        Aussetzer aber überbrückt wird.
        """
        eid = self._entity_id(key)
        if not eid:
            return None
        st = self.hass.states.get(eid)
        return st.state if st is not None else None

    def _attr(self, key: str, attr: str) -> str | None:
        eid = self._entity_id(key)
        if not eid:
            return None
        st = self.hass.states.get(eid)
        if st is None:
            return None
        val = st.attributes.get(attr)
        return str(val) if val is not None else None

    def _attr_float(self, key: str, attr: str) -> float | None:
        raw = self._attr(key, attr)
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _tv_active(self) -> tuple[bool, bool | None]:
        """TV-Aktiv-Wahrheit (FLEET-112).

        Primär = core_devices-Master (sensor.benni_master_tv, Attribut
        `is_active`): fusioniert Watt-Schwelle + Player in EINEM Owner. Ersetzt
        den alten Eigen-Schwellwert raw_watt>0, der das TV-Standby-Plateau
        (~35–39 W) bis 0 W als „an" hielt und den Szenario-Wechsel ~7 Min
        verschleppte. Die EINE Watt-Schwelle lebt im Master (FLEET-126).

        Fallback (Master nicht gebunden/verfügbar, z. B. fremde Anlage) = Player
        plus TV-Watt-Fallback ab 50 W. Returns (tv_active, tv_power); tv_power
        ist nur im Fallback gesetzt, sonst None (Master entscheidet).
        """
        master = _opt_bool(self._attr(CONF_TV_MASTER, "is_active"))
        if master is not None:
            return master, None
        tv_player_state = self._state(CONF_TV_PLAYER)
        active = _bool(self._state(CONF_TV_ACTIVE)) or tv_player_state in (
            "on", "playing", "paused",
        )
        tv_power_w = self._state(CONF_TV_POWER)
        try:
            tv_power = logic.tv_watt_active(float(tv_power_w)) if tv_power_w is not None else None
        except (TypeError, ValueError):
            tv_power = None
        return active, tv_power

    def _atv(self) -> tuple[str | None, str | None]:
        """Apple-TV-Wahrheit: native LAN-Quelle ist autoritativ.

        Der Core-Devices-Master sowie die MA-Entität sind keine Power-/Playback-
        Fallbacks. Ist der native LAN-Player gebunden, werden auch unknown /
        unavailable nicht durch einen veralteten Master ersetzt. Ein Master-
        Fallback bleibt nur für Profile ohne native Player-Binding.
        Returns (atv_state, atv_app_id) — atv_state ∈ playing/paused/idle/off/…
        """
        native_eid = self._entity_id(CONF_APPLETV_PLAYER)
        if native_eid:
            state = self._state(CONF_APPLETV_PLAYER)
            app = (
                self._attr(CONF_APPLETV_PLAYER, "app_id")
                or self._attr(CONF_APPLETV_PLAYER, "app_name")
            )
            return logic.select_appletv_source(True, state, app, None, None, None)

        master_active = _opt_bool(self._attr(CONF_APPLETV_MASTER, "is_active"))
        if master_active is not None:
            state = self._attr(CONF_APPLETV_MASTER, "player_state")
            app = (
                self._attr(CONF_APPLETV_MASTER, "app_id")
                or self._attr(CONF_APPLETV_MASTER, "app_name")
            )
            return logic.select_appletv_source(
                False, None, None, master_active, state, app or None
            )
        state = self._state(CONF_APPLETV_PLAYER)
        app = (
            self._attr(CONF_APPLETV_PLAYER, "app_id")
            or self._attr(CONF_APPLETV_PLAYER, "app_name")
        )
        return logic.select_appletv_source(False, state, app, None, None, None)

    # ----- Geräte-Matrix / Now-Playing (reine Observability, kein decide) -----
    def _artwork(self, player_key: str, classifier_key: str | None = None, *, music_assistant: bool = False) -> dict[str, Any]:
        """Geordnete Artwork-Kandidaten; die UI fällt bei Ladefehlern weiter."""
        attrs = ("media_image_url", "entity_picture") if music_assistant else ("entity_picture", "media_image_url")
        candidates: list[dict[str, str]] = []
        for attr in attrs:
            value = self._attr(player_key, attr)
            if isinstance(value, str) and value and not any(item["url"] == value for item in candidates):
                candidates.append({"url": value, "source": "music_assistant" if music_assistant and attr == "media_image_url" else attr})
        if classifier_key:
            value = self._attr(classifier_key, "artwork")
            if isinstance(value, str) and value and not any(item["url"] == value for item in candidates):
                candidates.append({"url": value, "source": "title_classifier"})
        return {
            "artwork_url": candidates[0]["url"] if candidates else None,
            "artwork_candidates": candidates,
        }

    def _device_matrix(self) -> dict[str, Any]:
        """Was die Quellen gerade zeigen — für das Cockpit (UX-Layer rendert nur).
        Liest dieselben Player wie _build_inputs; ändert KEINE Entscheidung."""
        def dev(active: bool, state: str | None, icon: str, **extra: Any) -> dict[str, Any]:
            out = {"active": bool(active), "state": state or "off", "icon": icon}
            out.update({k: v for k, v in extra.items() if v is not None})
            return out

        tv_pl = self._state(CONF_TV_PLAYER)
        atv = self._state(CONF_APPLETV_PLAYER)
        atv_app = (
            self._attr(CONF_APPLETV_PLAYER, "app_id")
            or self._attr(CONF_APPLETV_PLAYER, "app_name")
        )
        ps5_pl = self._state(CONF_PS5_PLAYER)
        hp = self._state(CONF_HOMEPODS_PLAYER)
        denon_pl = self._state(CONF_DENON_PLAYER)
        return {
            "tv": dev(self._tv_active()[0],
                      tv_pl, "mdi:television", source=self._attr(CONF_TV_PLAYER, "source"), **self._artwork(CONF_TV_PLAYER)),
            "apple_tv": dev(
                logic.appletv_active(atv),
                atv,
                "mdi:apple",
                app=atv_app,
                title=(
                    self._attr(CONF_APPLETV_PLAYER, "current_title")
                    or self._attr(CONF_APPLETV_PLAYER, "media_title")
                ),
                **self._artwork(CONF_APPLETV_PLAYER),
            ),
            "ps5": dev(_bool(self._state(CONF_PS5_ACTIVE)) or ps5_pl in ("on", "playing", "paused"),
                       ps5_pl, "mdi:sony-playstation", title=self._attr(CONF_PS5_PLAYER, "media_title"), **self._artwork(CONF_PS5_PLAYER, CONF_PS5_ENUM)),
            "switch": dev(_bool(self._state(CONF_SWITCH_ACTIVE)), self._state(CONF_SWITCH_ACTIVE), "mdi:nintendo-switch",
                          ignored=True),
            "pc": dev(_bool(self._state(CONF_PC_ACTIVE)), self._state(CONF_PC_ACTIVE), "mdi:desktop-classic"),
            "homepods": dev(hp == "playing", hp, "mdi:speaker-multiple",
                            title=self._attr(CONF_HOMEPODS_PLAYER, "media_title"),
                            artist=self._attr(CONF_HOMEPODS_PLAYER, "media_artist"),
                            volume=self._attr_float(CONF_HOMEPODS_PLAYER, "volume_level"),
                            **self._artwork(CONF_HOMEPODS_PLAYER, CONF_MEDIA_ENUM, music_assistant=True)),
            "denon": dev(_bool(self._state(CONF_DENON_ACTIVE)) or denon_pl in ("on", "playing"),
                         denon_pl, "mdi:audio-video"),
        }

    _GAME_LABELS = {0: "gaming_default", 1: "gaming_grind", 2: "gaming_headset"}
    _MUSIC_LABELS = {0: "normal", 1: "boost", 2: "mute"}

    def _context_echo(self) -> dict[str, Any]:
        """core_state-Kontext fürs Cockpit (read-only Echo, keine Entscheidung)."""
        return {
            "bio_state": self._state(CONF_BIO_STATE),
            "presence": self._state(CONF_PRESENCE),
            "household": self._state(CONF_HOUSEHOLD),
            "transition": self._state(CONF_TRANSITION),
            "activity": self._state(CONF_ACTIVITY_STATE),
            "day_state": self._state(CONF_DAY_STATE),
        }

    def _classifiers(self) -> dict[str, Any]:
        """Title-Classifier-Enums + Labels (PS5/PC = Gaming, HomePods = Musik)."""
        def cl(key: str, table: dict[int, str]) -> dict[str, Any]:
            e = _opt_int(self._state(key))
            return {
                "enum": e,
                "label": table.get(e) if e is not None else None,
                "display_name": self._attr(key, "key"),
                "original_title": self._state(CONF_PS5_TITLE) if key == CONF_PS5_ENUM else self._state(CONF_PC_RAW) if key == CONF_PC_ENUM else self._attr(CONF_HOMEPODS_PLAYER, "media_title"),
                "platform": self._attr(key, "context"),
                "artwork_url": self._attr(key, "artwork"),
                "entry_id": self._attr(key, "current_entry_id"),
            }
        return {
            "ps5": cl(CONF_PS5_ENUM, self._GAME_LABELS),
            "pc": cl(CONF_PC_ENUM, self._GAME_LABELS),
            "homepods": cl(CONF_MEDIA_ENUM, self._MUSIC_LABELS),
        }

    def _now_playing(self) -> dict[str, Any] | None:
        """Aktiver Audio-Stream (für die Hero-Karte), falls HomePods spielen."""
        if self._state(CONF_HOMEPODS_PLAYER) != "playing":
            return None
        title = self._attr(CONF_HOMEPODS_PLAYER, "media_title")
        if not title:
            return None
        return {
            "device": "homepods",
            "title": title,
            "artist": self._attr(CONF_HOMEPODS_PLAYER, "media_artist"),
            "volume": self._attr_float(CONF_HOMEPODS_PLAYER, "volume_level"),
            **self._artwork(CONF_HOMEPODS_PLAYER, CONF_MEDIA_ENUM, music_assistant=True),
        }

    # ----- evaluation -----
    def _build_inputs(self) -> logic.Inputs:
        # TV (FLEET-112): Aktiv-Wahrheit aus dem core_devices-Master; Quelle für
        # den Subcontext weiterhin aus dem Player-`source`-Attribut.
        tv_active_raw, tv_power = self._tv_active()
        # TV-Start: Master/Player/Watt liefern nur ein Roh-Signal; der TV-
        # Kontext wird erst nach dem stabilen 20-s-Fenster freigegeben.
        tv_signal = tv_active_raw or tv_power is True
        tv_active, self._tv_start_since = logic.stabilize_tv_start(
            tv_signal,
            self._tv_start_since,
            time.monotonic(),
            TV_START_STABILIZATION_SECONDS,
        )
        if tv_power is not None:
            tv_power = tv_active

        # Apple TV (FLEET-212): native LAN player is authoritative.
        atv_state, atv_app_id = self._atv()

        # PS5: Plug-Active gewinnt, sonst Player-State.
        ps5_player_state = self._state(CONF_PS5_PLAYER)
        ps5_on_raw = _bool(self._state(CONF_PS5_ACTIVE)) or ps5_player_state in (
            "on", "playing", "paused",
        )
        # OFF-Hold (FLEET-262): bricht ps5_on ein, während die Aktiv-Quelle
        # (Master) oder der Player degradiert ist (unknown/unavailable = flaky
        # PlayStation-Integration), wird Gaming bis PS5_DROPOUT_HOLD_SECONDS
        # gehalten. Ein sauberes `off` beider Quellen räumt sofort (kein Hold).
        ps5_source_degraded = (
            self._raw_state(CONF_PS5_ACTIVE) in ("unknown", "unavailable")
            or self._raw_state(CONF_PS5_PLAYER) in ("unknown", "unavailable")
        )
        ps5_on, self._ps5_on_since = logic.hold_ps5_on(
            ps5_on_raw,
            ps5_source_degraded,
            self._ps5_on_since,
            time.monotonic(),
            PS5_DROPOUT_HOLD_SECONDS,
        )
        ps5_title = self._attr(CONF_PS5_PLAYER, "media_title") or self._state(CONF_PS5_TITLE)

        # Away-Gate: aus core_states presence_personal-Enum abgeleitet (stabile
        # Entity-ID, retained seit core_state v0.6.0) + ON-Debounce (kein
        # Fehl-Stop bei einem transienten Away-Dip). `_away_since` trägt das
        # Fenster. Keine eigene Klassifikation — strikt an core_states 3 Werte.
        away_raw = logic.away_from_presence(self._state(CONF_PRESENCE))
        away_gated, self._away_since = logic.gate_away(
            away_raw, self._away_since, time.monotonic(), AWAY_DEBOUNCE_SECONDS
        )

        return logic.Inputs(
            tv_active=tv_active,
            tv_source=self._attr(CONF_TV_PLAYER, "source"),
            tv_power=tv_power,
            atv_state=atv_state,
            atv_app_id=atv_app_id,
            ps5_on=ps5_on,
            ps5_title=ps5_title,
            ps5_raw=self._state(CONF_PS5_RAW),
            ps5_enum=_int(self._state(CONF_PS5_ENUM)),
            # FLEET-95: Switch-Steckdose vorübergehend NICHT als Kontext-Quelle.
            # Die Steckdose pulst im Standby kurz (~3 W) → core_devices flippt
            # `powered` → switch_dock kippte den Kontext auf gaming → media_apply
            # churnte den Radio-Stream. Bis echte idle/playing-Watt vorliegen und
            # `watt_threshold_on` in core_devices datenbasiert gesetzt ist, wird
            # der Switch-Dock hier hart ignoriert (Roh-State bleibt im Cockpit
            # sichtbar, treibt aber keine Entscheidung). Re-Enable: FLEET-95.
            switch_dock=False,
            pc_active=_bool(self._state(CONF_PC_ACTIVE)),
            pc_raw=self._state(CONF_PC_RAW),
            pc_enum=_int(self._state(CONF_PC_ENUM)),
            denon_active=_bool(self._state(CONF_DENON_ACTIVE))
            or self._state(CONF_DENON_PLAYER) in ("on", "playing"),
            homepods_playing=self._state(CONF_HOMEPODS_PLAYER) == "playing",
            media_enum=_int(self._state(CONF_MEDIA_ENUM)),
            quiet_external=_opt_bool(self._state(CONF_QUIET_EXTERNAL)),
            door_open=_bool(self._state(CONF_DOOR)),
            call_active=_bool(self._state(CONF_CALL)),
            activity_state=self._state(CONF_ACTIVITY_STATE),
            # Presence-Gate: core_state ist Owner. `presence` = Roh-Quelle nur
            # fürs Cockpit; die Away-Entscheidung kommt aus dem kanonischen
            # core_state-Gate, ON-debounced (siehe unten).
            presence=self._state(CONF_PRESENCE),
            away_raw=away_raw,
            away_gated=away_gated,
            stash_streams=_opt_int(self._state(CONF_STASH_STREAMS)),
            stash_enum=_opt_int(self._state(CONF_STASH_ENUM)),
            private_manual=self._private_manual,
            manual_nudge=self._manual_nudge,
        )

    def _compute(self) -> dict[str, Any]:
        # FLEET-98: manuellen private_time-Latch beim Einschlafen räumen
        # (Einschlaf-Flanke des bio_state). Vor dem Input-Bau, damit derselbe
        # Tick schon ohne private_time rechnet.
        bio = self._state(CONF_BIO_STATE)
        if logic.should_clear_private_on_sleep(bio, self._last_bio_state, self._private_manual):
            _LOGGER.info("media_state: private_time-Latch Einschlaf-Clear")
            self._private_manual = False
            self._cancel_private_timeout()
        self._last_bio_state = bio

        # control#3: manuellen private_time-Latch auf der PC-Aus-Flanke räumen
        # (manual = switch ∧ PC). Vor dem Input-Bau, damit derselbe Tick schon
        # ohne private_time rechnet.
        pc_active_now = _bool(self._state(CONF_PC_ACTIVE))
        if logic.should_clear_private_on_pc_off(
            pc_active_now, self._last_pc_active, self._private_manual
        ):
            _LOGGER.info("media_state: private_time-Latch PC-Off-Clear")
            self._private_manual = False
            self._cancel_private_timeout()
        self._last_pc_active = pc_active_now

        inputs = self._build_inputs()
        state = logic.decide(
            inputs,
            pre_atv=self._pre_atv,
            sticky_gaming_sub=self._sticky_gaming_sub,
        )
        # Pre-ATV-Szenario nachführen: solange das primäre Gerät NICHT der
        # Apple TV ist, ist das aktuelle Szenario der Rollback-Kandidat.
        if state.device != DEV_APPLETV:
            new_pre = (state.context, state.subcontext)
            if new_pre != self._pre_atv:
                self._pre_atv = new_pre
                self._persist_pre_atv()  # OQ-2: über Neustarts halten
        # R6-Sticky: laufende PS5-Session merkt sich ihren Subcontext;
        # Session-Ende setzt zurück (nächstes Menü startet wieder bei grind).
        if state.context == CTX_GAMING and state.gaming_platform == GP_PS5:
            self._sticky_gaming_sub = state.subcontext
        else:
            self._sticky_gaming_sub = None
        data = state.as_dict()
        # Observability-Anreicherung (UX-Cockpit): Geräte-Matrix + Now-Playing.
        data["devices"] = self._device_matrix()
        data["now_playing"] = self._now_playing()
        data["context_cards"] = self._context_echo()
        data["classifiers"] = self._classifiers()
        data["bindings"] = self.bindings()

        # Activity-Context-Feed (FLEET-255): Media-Hälfte des Activity-States
        # für core_state. Additiv aus dem SCHON berechneten state + inputs —
        # ändert media_context/decide() nicht. Kein Rückgriff auf core_state
        # activity_state oder presence_effective.
        ac = logic.derive_activity_context(state, inputs)
        activity_attrs = dict(ac.attrs)
        # Optionale Consumer-Metadaten NUR aus bereits gelesenen Daten (keine
        # neuen Roh-Bindungen); fehlend → weglassen statt erzwingen.
        now_playing = data["now_playing"] or {}
        if now_playing.get("title"):
            activity_attrs["title"] = now_playing["title"]
        if now_playing.get("artist"):
            activity_attrs["artist"] = now_playing["artist"]
        if state.context == CTX_GAMING:
            if logic.title_present(inputs.ps5_raw):
                activity_attrs["game_title"] = inputs.ps5_raw
            elif inputs.ps5_title and str(inputs.ps5_title).strip():
                activity_attrs["game_title"] = inputs.ps5_title
            elif logic.title_present(inputs.pc_raw):
                activity_attrs["game_title"] = inputs.pc_raw
        if state.context == CTX_STREAMING and inputs.atv_app_id:
            activity_attrs["source_app"] = inputs.atv_app_id
        data["activity_context"] = ac.state
        data["activity_attrs"] = activity_attrs
        return data

    async def _async_update_data(self) -> dict[str, Any]:
        return self._compute()
