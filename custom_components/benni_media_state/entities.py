"""Entity-Basis + Roster-Beschreibungen für benni_media_state.

Description-getrieben: das vorläufige Roster lebt hier als Daten (SENSORS /
BINARY_SENSORS), die Plattform-Dateien sensor.py / binary_sensor.py bauen daraus
die Entities. Alle lesen aus `coordinator.data` und liefern stabile Defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_PROFILE,
    CONTEXT_ATTRS,
    DEFAULT_PROFILE,
    DOMAIN,
    PROFILE_LABELS,
    UID_AWAY_GATE,
    UID_CONTEXT,
    UID_DEVICE,
    UID_ENTERTAINMENT_ACTIVE,
    UID_GAMING_PLATFORM,
    UID_GAMING_SOURCE,
    UID_HEADSET_ACTIVE,
    UID_PRESENCE_STATE,
    UID_QUIET_MODE,
    UID_QUIET_MODE_REASON,
    UID_SUBCONTEXT,
    unique_id,
)
from .coordinator import MediaStateCoordinator


@dataclass(frozen=True)
class FieldDesc:
    """Beschreibt eine Output-Entity: data-Key → Entity."""

    key: str            # Feld in coordinator.data
    uid: str            # unique_id-Suffix (auch object_id-Basis)
    name: str           # friendly name (Entity-Teil; has_entity_name=True)
    icon: str | None = None
    attrs: tuple[str, ...] = field(default_factory=tuple)  # zusätzliche Attribut-Keys


SENSORS: tuple[FieldDesc, ...] = (
    FieldDesc("context", UID_CONTEXT, "Media Context", "mdi:multimedia", CONTEXT_ATTRS),
    FieldDesc("subcontext", UID_SUBCONTEXT, "Media Subcontext", "mdi:format-list-bulleted"),
    FieldDesc("device", UID_DEVICE, "Media Device", "mdi:devices"),
    FieldDesc("gaming_source", UID_GAMING_SOURCE, "Gaming Source", "mdi:gamepad-variant"),
    FieldDesc("gaming_platform", UID_GAMING_PLATFORM, "Gaming Platform", "mdi:controller-classic"),
    # Quiet bleibt L1 (FLEET-31): Begründung als Freitext-Sensor.
    FieldDesc("quiet_mode_reason", UID_QUIET_MODE_REASON, "Quiet Mode Reason", "mdi:comment-question-outline"),
    # Presence-Gate (FLEET-212): sichtbarer Presence-State (zuhause/abwesend/
    # unknown) + Roh-Quelle & Away-Gate als Diagnose-Attribute.
    FieldDesc(
        "presence_state", UID_PRESENCE_STATE, "Presence State", "mdi:home-account",
        ("presence_source", "away_gate"),
    ),
)

BINARY_SENSORS: tuple[FieldDesc, ...] = (
    FieldDesc("headset_active", UID_HEADSET_ACTIVE, "Headset Active", "mdi:headset"),
    FieldDesc("entertainment_active", UID_ENTERTAINMENT_ACTIVE, "Entertainment Active", "mdi:television-play"),
    # Quiet bleibt L1 (FLEET-31).
    FieldDesc("quiet_mode", UID_QUIET_MODE, "Quiet Mode", "mdi:volume-low"),
    # Presence-Gate (FLEET-212): Away-Gate als eigener Binary (deaktiviert die
    # Medienlogik bei Abwesenheit — leicht als Automations-Trigger nutzbar).
    FieldDesc("away_gate", UID_AWAY_GATE, "Away Gate", "mdi:home-export-outline"),
)


def device_info(entry: ConfigEntry) -> dict[str, Any]:
    # Der Device-Name bestimmt bei has_entity_name den Entity-Slug:
    #   "Benni Media State"  → sensor.benni_media_state_*
    #   "Eltern Media State" → sensor.eltern_media_state_*
    profile = entry.data.get(CONF_PROFILE, DEFAULT_PROFILE)
    label = PROFILE_LABELS.get(profile, "Benni")
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": f"{label} Media State",
        "manufacturer": "Benni",
        "model": f"Media State · {label}",
    }


class MediaStateEntity(CoordinatorEntity[MediaStateCoordinator]):
    """Gemeinsame Basis: liest aus coordinator.data via FieldDesc."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: MediaStateCoordinator, entry: ConfigEntry, desc: FieldDesc
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = unique_id(entry.entry_id, desc.uid)
        self._attr_name = desc.name
        # Kein suggested_object_id: der Slug kommt aus dem profil-getriebenen
        # Device-Namen (has_entity_name) → <profil>_media_state_<type>.
        if desc.icon:
            self._attr_icon = desc.icon
        self._attr_device_info = device_info(entry)

    @property
    def _value(self) -> Any:
        return (self.coordinator.data or {}).get(self._desc.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self._desc.attrs:
            return None
        data = self.coordinator.data or {}
        return {attr: data.get(attr) for attr in self._desc.attrs}
