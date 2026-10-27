"""Weather Gateway Live Data integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import LiveDataCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER]

type GatewayConfigEntry = ConfigEntry[LiveDataCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: GatewayConfigEntry) -> bool:
    coordinator = LiveDataCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GatewayConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
