"""Config- und Options-Flow für benni_media_state.

Profil-Mechanik 1:1 aus benni_core_state (gelockte Blaupause, FLEET-29):
- Schritt `user`: Profil-SelectSelector (benni/eltern).
- Schritt `entities`: Quell-Slots, vorbefüllt mit der Profil-Map (Auto-Bind
  sichtbar), gespeichert werden aber **nur Abweichungen** (`_entity_overrides`).
  `_prefill_defaults` filtert auf Entities, die in dieser HA existieren.
- Single-Instance: nur ein Config-Entry (`_async_current_entries()`-Gate).
- Auto-Bind `options ▶ data ▶ PROFILE_PREFILL[profile]` lebt im Coordinator
  (`_entity_id`).

HA erkennt den Config-Flow nur unter `config_flow.py` (Pflicht-Modulname).
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DIAGNOSTICS_VERBOSE,
    CONF_HEADSET,
    CONF_MEDIA_PLAYERS,
    CONF_PROFILE,
    CONF_TITLE_CLASSIFIER,
    DEFAULT_DIAGNOSTICS_VERBOSE,
    DEFAULT_PROFILE,
    DOMAIN,
    NAME,
    PROFILE_LABELS,
    PROFILE_PREFILL,
    PROFILES,
    WATCH_KEYS,
)

# --- Selektoren (ungefiltert, volle Flexibilität) ---
_ENTITY = selector.EntitySelector(selector.EntitySelectorConfig())
_PLAYERS = selector.EntitySelector(
    selector.EntitySelectorConfig(domain="media_player", multiple=True)
)
_BOOL = selector.BooleanSelector()

SELECTORS: dict[str, Any] = {
    CONF_MEDIA_PLAYERS: _PLAYERS,
    CONF_TITLE_CLASSIFIER: _ENTITY,
    CONF_HEADSET: _ENTITY,
}

# Entity-Slots (Override-fähig) = die Quell-Keys aus WATCH_KEYS.
_ENTITY_SLOT_KEYS: tuple[str, ...] = WATCH_KEYS


def _entities_schema(defaults: dict[str, Any]) -> vol.Schema:
    fields: dict[Any, Any] = {}
    for key in _ENTITY_SLOT_KEYS:
        d = defaults.get(key)
        marker = vol.Optional(key, default=d) if d else vol.Optional(key)
        fields[marker] = SELECTORS[key]
    return vol.Schema(fields)


def _entity_overrides(profile: str, user_input: dict[str, Any]) -> dict[str, Any]:
    """Nur echte Abweichungen vom Profil-Map als Override speichern.

    Leere Felder und Werte, die dem Code-Default entsprechen, werden NICHT
    gespeichert → Map-Updates aus dem Repo propagieren weiter.
    """
    code = PROFILE_PREFILL.get(profile, {})
    out: dict[str, Any] = {}
    for key in _ENTITY_SLOT_KEYS:
        v = user_input.get(key)
        if v and v != code.get(key):
            out[key] = v
    return out


def _override_or_map(profile: str, data: dict[str, Any]) -> dict[str, Any]:
    """Anzeige-Defaults: gespeicherter Override sonst Profil-Map-Default."""
    code = PROFILE_PREFILL.get(profile, {})
    out: dict[str, Any] = {}
    for key in _ENTITY_SLOT_KEYS:
        v = data.get(key) or code.get(key)
        if v:
            out[key] = v
    return out


def _profile_schema(default: str) -> vol.Schema:
    return vol.Schema({
        vol.Required(CONF_PROFILE, default=default): selector.SelectSelector(
            selector.SelectSelectorConfig(
                mode=selector.SelectSelectorMode.LIST,
                options=[
                    selector.SelectOptionDict(value=p, label=PROFILE_LABELS[p])
                    for p in PROFILES
                ],
            )
        )
    })


class MediaStateConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._profile: str = DEFAULT_PROFILE
        self._entities: dict[str, Any] = {}

    def _prefill_defaults(self) -> dict[str, Any]:
        """Profil-Prefill, gefiltert auf Entities, die in dieser HA existieren.

        Profil "eltern" hat (vorerst) keine Defaults → alle Slots leer.
        """
        prefill = PROFILE_PREFILL.get(self._profile, {})
        return {
            key: eid
            for key, eid in prefill.items()
            if isinstance(eid, str) and self.hass.states.get(eid) is not None
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Single-Instance-Gate (eine Route pro HA; saubere Entity-IDs).
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=_profile_schema(DEFAULT_PROFILE),
            )
        self._profile = user_input[CONF_PROFILE]
        return await self.async_step_entities()

    async def async_step_entities(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        # Override-Step: vorbefüllt mit der Profil-Map (so sieht man die
        # Auto-Bindung), gespeichert werden nur Abweichungen. Leer = Auto-Bind.
        if user_input is None:
            return self.async_show_form(
                step_id="entities", data_schema=_entities_schema(self._prefill_defaults()),
            )
        self._entities = _entity_overrides(self._profile, user_input)
        return self.async_create_entry(
            title=f"{NAME} ({PROFILE_LABELS[self._profile]})",
            data={CONF_PROFILE: self._profile, **self._entities},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return MediaStateOptionsFlow()


class MediaStateOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(step_id="init", menu_options=["entities", "diagnostics"])

    async def async_step_entities(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        profile = self.config_entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
        if user_input is not None:
            overrides = _entity_overrides(profile, user_input)
            new_data = {
                k: v for k, v in self.config_entry.data.items()
                if k not in _ENTITY_SLOT_KEYS
            }
            new_data.update(overrides)
            new_data[CONF_PROFILE] = profile
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data=dict(self.config_entry.options))
        return self.async_show_form(
            step_id="entities",
            data_schema=_entities_schema(_override_or_map(profile, self.config_entry.data)),
        )

    async def async_step_diagnostics(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data={**self.config_entry.options, **user_input})
        defaults = {**self.config_entry.data, **self.config_entry.options}
        schema = vol.Schema({
            vol.Optional(
                CONF_DIAGNOSTICS_VERBOSE,
                default=bool(defaults.get(CONF_DIAGNOSTICS_VERBOSE, DEFAULT_DIAGNOSTICS_VERBOSE)),
            ): _BOOL,
        })
        return self.async_show_form(step_id="diagnostics", data_schema=schema)
