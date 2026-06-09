"""Media-State-Coordinator (Single-Instance, event-driven).

DataUpdateCoordinator ohne Polling (`update_interval=None`): er rechnet nur bei
State-Changes der gebundenen Quell-Entities (oder manuellem Refresh) neu.

Profil-Hub (benni/eltern) + Auto-Bind wie light_policy/core_devices:
Binding-Auflösung = Override (Config) ▶ Profil-Map (PROFILE_PREFILL) ▶ leer.

Step-1-Scaffold: `_compute()` ruft `logic.decide()` (Stub) und liefert die
Default-data. Inputs werden bereits aus den gebundenen States gelesen, der
Ableitungs-Body kommt in Step 2.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import logic
from .const import (
    CONF_HEADSET,
    CONF_MEDIA_PLAYERS,
    CONF_PROFILE,
    CONF_TITLE_CLASSIFIER,
    DEFAULT_PROFILE,
    DOMAIN,
    PROFILE_PREFILL,
    PROFILES,
    WATCH_KEYS,
)

_LOGGER = logging.getLogger(__name__)


def _state(hass: HomeAssistant, eid: str | None) -> str | None:
    if not eid:
        return None
    st = hass.states.get(eid)
    if st is None or st.state in ("unknown", "unavailable"):
        return None
    return st.state


class MediaStateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Eine Instanz pro Config-Entry (Single-Instance-Modell)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=None)
        self.entry = entry
        profile = entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
        self._profile = profile if profile in PROFILES else DEFAULT_PROFILE
        self._unsub_state = None

    # ----- profile / binding -----
    @property
    def profile(self) -> str:
        return self._profile

    @property
    def _opts(self) -> dict[str, Any]:
        return {**self.entry.data, **self.entry.options}

    def bound_entity(self, key: str) -> Any:
        """Auto-Bind: Override (Config) ▶ Profil-Map ▶ leer."""
        override = self._opts.get(key)
        if override:
            return override
        return PROFILE_PREFILL.get(self._profile, {}).get(key)

    def _watched_entities(self) -> list[str]:
        ids: list[str] = []
        for key in WATCH_KEYS:
            val = self.bound_entity(key)
            if isinstance(val, str) and val:
                ids.append(val)
            elif isinstance(val, (list, tuple)):
                ids.extend(e for e in val if isinstance(e, str) and e)
        # Duplikate raus, Reihenfolge erhalten.
        return list(dict.fromkeys(ids))

    def bindings(self) -> dict[str, Any]:
        """Aktuelle Auflösung aller WATCH_KEYS — für Panel/Diagnose."""
        return {key: self.bound_entity(key) for key in WATCH_KEYS}

    # ----- lifecycle -----
    @callback
    def async_start(self) -> None:
        watched = self._watched_entities()
        if watched:
            self._unsub_state = async_track_state_change_event(
                self.hass, watched, self._on_state_change
            )
            self.entry.async_on_unload(self._unsub_state)

    @callback
    def _on_state_change(self, _event: Event) -> None:
        self.async_set_updated_data(self._compute())

    # ----- evaluation -----
    def _build_inputs(self) -> logic.Inputs:
        players = self.bound_entity(CONF_MEDIA_PLAYERS) or []
        if isinstance(players, str):
            players = [players]
        player_states = {p: s for p in players if (s := _state(self.hass, p)) is not None}
        return logic.Inputs(
            media_players=tuple(players),
            player_states=player_states,
            title_classifier=_state(self.hass, self.bound_entity(CONF_TITLE_CLASSIFIER)),
            headset=_state(self.hass, self.bound_entity(CONF_HEADSET)),
        )

    def _compute(self) -> dict[str, Any]:
        return logic.decide(self._build_inputs()).as_dict()

    async def _async_update_data(self) -> dict[str, Any]:
        return self._compute()
