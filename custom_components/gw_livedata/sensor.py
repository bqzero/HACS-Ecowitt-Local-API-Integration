"""Sensors for the weather gateway."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GatewayConfigEntry
from .coordinator import LiveDataCoordinator

_NUM = re.compile(r"-?\d+(?:\.\d+)?")
MS_TO_KMH = 3.6


def _num(raw: Any) -> float | None:
    """Extract the first number from a value like '12.3 mm' or '45%'."""
    if raw is None:
        return None
    match = _NUM.search(str(raw))
    return float(match.group()) if match else None


def _common(index: int) -> Callable[[dict], Any]:
    return lambda d: d["common_list"][index]["val"]


def _piezo(index: int) -> Callable[[dict], Any]:
    return lambda d: d["piezoRain"][index]["val"]


def _wh25(key: str) -> Callable[[dict], Any]:
    return lambda d: d["wh25"][0][key]


@dataclass(frozen=True, kw_only=True)
class GatewaySensorDescription(SensorEntityDescription):
    """Sensor description with raw getter and scale."""

    raw: Callable[[dict], Any]
    scale: float = 1.0
    precision: int | None = None


SENSORS: tuple[GatewaySensorDescription, ...] = (
    GatewaySensorDescription(
        key="outdoortemp", name="outdoortemp", raw=_common(0),
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="outdoorhumid", name="outdoorhumid", raw=_common(1),
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="windspeed", name="windspeed", raw=_common(7), scale=MS_TO_KMH, precision=1,
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="windgust", name="windgust", raw=_common(8), scale=MS_TO_KMH, precision=1,
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="winddir", name="winddirection", raw=_common(11),
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    GatewaySensorDescription(
        key="solrad", name="solarradiation", raw=_common(9),
        device_class=SensorDeviceClass.IRRADIANCE,
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="uvindex", name="uvindex", raw=_common(10),
        native_unit_of_measurement="UV index",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:weather-sunny-alert",
    ),
    GatewaySensorDescription(
        key="rainrate", name="rain_rate", raw=_piezo(1),
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="rainrate_daily", name="rain_rate_daily", raw=_piezo(2),
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    GatewaySensorDescription(
        key="rainrate_weekly", name="rain_rate_weekly", raw=_piezo(3),
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    GatewaySensorDescription(
        key="rainrate_monthly", name="rain_rate_monthly", raw=_piezo(4),
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    GatewaySensorDescription(
        key="rainrate_yearly", name="rain_rate_yearly", raw=_piezo(5),
        device_class=SensorDeviceClass.PRECIPITATION,
        native_unit_of_measurement=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    GatewaySensorDescription(
        key="ab_press", name="absolute_pressure", raw=_wh25("abs"),
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="indoorhumid", name="indoorhumid", raw=_wh25("inhumi"),
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    GatewaySensorDescription(
        key="indoortemp", name="indoortemp", raw=_wh25("intemp"),
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: GatewayConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(GatewaySensor(coordinator, d) for d in SENSORS)


class GatewaySensor(CoordinatorEntity[LiveDataCoordinator], SensorEntity):
    """One value from the gateway."""

    entity_description: GatewaySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LiveDataCoordinator, description: GatewaySensorDescription
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        desc = self.entity_description
        try:
            value = _num(desc.raw(self.coordinator.data))
        except (KeyError, IndexError, TypeError):
            return None
        if value is None:
            return None
        value *= desc.scale
        return round(value, desc.precision) if desc.precision is not None else value
