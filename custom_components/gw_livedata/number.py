"""Number: polling interval control."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GatewayConfigEntry
from .const import MAX_SCAN_INTERVAL, MIN_SCAN_INTERVAL
from .coordinator import LiveDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GatewayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([PollingIntervalNumber(entry.runtime_data)])


class PollingIntervalNumber(NumberEntity):
    """Polling interval in seconds."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_name = "polling_interval"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = NumberDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = MIN_SCAN_INTERVAL
    _attr_native_max_value = MAX_SCAN_INTERVAL
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: LiveDataCoordinator) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_polling_interval"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float:
        return self._coordinator.scan_interval

    async def async_set_native_value(self, value: float) -> None:
        self._coordinator.set_scan_interval(int(value))
        self.async_write_ha_state()
