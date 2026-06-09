"""Sensor-Plattform: Media-Context (rich) + Subcontext / Device / Gaming-Source/-Platform."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATOR, DOMAIN
from .entities import SENSORS, MediaStateEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coord = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities(MediaStateSensor(coord, entry, desc) for desc in SENSORS)


class MediaStateSensor(MediaStateEntity, SensorEntity):
    @property
    def native_value(self):
        return self._value
