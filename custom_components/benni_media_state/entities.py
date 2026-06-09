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
    CONTEXT_ATTRS,
    DOMAIN,
    NAME,
    UID_CONTEXT,
    UID_DEVICE,
    UID_ENTERTAINMENT_ACTIVE,
    UID_GAMING_PLATFORM,
    UID_GAMING_SOURCE,
    UID_HEADSET_ACTIVE,
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
)

BINARY_SENSORS: tuple[FieldDesc, ...] = (
    FieldDesc("headset_active", UID_HEADSET_ACTIVE, "Headset Active", "mdi:headset"),
    FieldDesc("entertainment_active", UID_ENTERTAINMENT_ACTIVE, "Entertainment Active", "mdi:television-play"),
)


def device_info(entry: ConfigEntry) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": NAME,
        "manufacturer": "Benni",
        "model": "Media State (Context-Feeder)",
    }


class MediaStateEntity(CoordinatorEntity[MediaStateCoordinator]):
    """Gemeinsame Basis: liest aus coordinator.data via FieldDesc."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: MediaStateCoordinator, entry: ConfigEntry, desc: FieldDesc
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = unique_id(desc.uid)
        self._attr_name = desc.name
        self._attr_suggested_object_id = unique_id(desc.uid)
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
