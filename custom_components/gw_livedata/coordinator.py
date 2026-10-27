"""Data coordinator."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_HOST,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    LIVEDATA_PATH,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


async def async_fetch_livedata(hass: HomeAssistant, host: str) -> dict[str, Any]:
    """Fetch live data JSON from the gateway."""
    session = async_get_clientsession(hass)
    async with session.get(
        f"http://{host}{LIVEDATA_PATH}",
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
    ) as resp:
        resp.raise_for_status()
        return await resp.json(content_type=None)


class LiveDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls the gateway."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=self._interval_from(entry)),
        )
        self.host: str = entry.data[CONF_HOST]

    @staticmethod
    def _interval_from(entry: ConfigEntry) -> int:
        value = int(entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        return max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, value))

    @property
    def scan_interval(self) -> int:
        return self._interval_from(self.config_entry)

    @property
    def device_info(self) -> DeviceInfo:
        suffix = self.host.split(".")[-1] if self.host.count(".") == 3 else self.host
        return DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=f"{suffix} Weather Gateway",
            manufacturer="bqzero",
            model="Local HTTP live data Ecowitt-compatible",
            configuration_url=f"http://{self.host}",
        )

    def set_scan_interval(self, seconds: int) -> None:
        """Persist and apply a new polling interval."""
        seconds = max(MIN_SCAN_INTERVAL, min(MAX_SCAN_INTERVAL, int(seconds)))
        self.hass.config_entries.async_update_entry(
            self.config_entry,
            options={**self.config_entry.options, CONF_SCAN_INTERVAL: seconds},
        )
        self.update_interval = timedelta(seconds=seconds)

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await async_fetch_livedata(self.hass, self.host)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise UpdateFailed(f"Error talking to {self.host}: {err}") from err
        if not isinstance(data, dict):
            raise UpdateFailed("Unexpected response")
        return data
