"""Switch-Plattform: nativer Private-Time-Manual-Trigger (FLEET-44).

Ersetzt den externen `input_boolean.media_private_time_manual` durch eine
integration-eigene Schalt-Entität — nativ, ohne YAML-Helfer. media_state hält
den Zustand (coordinator-backed, über RestoreEntity persistent) und liest ihn
intern als private_time-Trigger. Kein externes Binding → keine `system_`-
Entity-ID-Falle. Auto-Löschung (Einschlafen + Timeout) lebt im Coordinator.

NB: Das ist NICHT die Nintendo Switch (die ist `sensor.benni_master_switch`
über CONF_SWITCH_ACTIVE gebunden). Dieser Slug ist `*_private_time_manual`.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, UID_PRIVATE_MANUAL, unique_id
from .coordinator import MediaStateCoordinator
from .entities import device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coord = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([PrivateTimeManualSwitch(coord, entry)])


class PrivateTimeManualSwitch(
    CoordinatorEntity[MediaStateCoordinator], SwitchEntity, RestoreEntity
):
    """Manueller private_time-Schalter (Dating/Besuch). Zustand im Coordinator."""

    _attr_has_entity_name = True
    _attr_name = "Private Time Manual"
    _attr_icon = "mdi:account-lock"

    def __init__(
        self, coordinator: MediaStateCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id(entry.entry_id, UID_PRIVATE_MANUAL)
        self._attr_device_info = device_info(entry)

    @property
    def is_on(self) -> bool:
        return self.coordinator.private_manual

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Persistenten Zustand über Neustart wiederherstellen (wie der alte
        # input_boolean). on → Coordinator übernimmt + Timeout re-scheduled.
        last = await self.async_get_last_state()
        if last is not None and last.state == "on":
            self.coordinator.restore_private_manual(True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_private_manual(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_private_manual(False)
