"""Sensor platform for Open-Meteo CloudCover integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_FORECAST_DAYS, CONF_LATITUDE, CONF_LONGITUDE, DEFAULT_FORECAST_DAYS, DOMAIN, SENSOR_TYPES, get_day_name
from .coordinator import OpenMeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Open-Meteo CloudCover sensor entities."""
    coordinator: OpenMeteoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get the forecast days from config
    forecast_days = entry.data.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)

    # Create sensor entities for each sensor type and each day
    entities = []
    for sensor_type in SENSOR_TYPES:
        # Create a sensor for each day (0 = today, 1 = tomorrow, etc.)
        for day_offset in range(forecast_days + 1):  # +1 to include today
            entities.append(
                OpenMeteoSensor(
                    coordinator=coordinator,
                    entry=entry,
                    sensor_type=sensor_type,
                    day_offset=day_offset,
                )
            )

    async_add_entities(entities)


class OpenMeteoSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Open-Meteo CloudCover sensor."""

    def __init__(
        self,
        coordinator: OpenMeteoDataUpdateCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        day_offset: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_type = sensor_type
        self._day_offset = day_offset
        self._sensor_key = f"{sensor_type}_{day_offset}"

        # Build friendly name with day label
        day_name = get_day_name(day_offset)
        base_name = SENSOR_TYPES[sensor_type]["name"]
        self._attr_name = f"{base_name} {day_name}"

        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}_{day_offset}"
        self._attr_icon = SENSOR_TYPES[sensor_type]["icon"]

        # Set device class if available
        if SENSOR_TYPES[sensor_type]["device_class"]:
            self._attr_device_class = SENSOR_TYPES[sensor_type]["device_class"]

        # Set state class
        if SENSOR_TYPES[sensor_type]["state_class"]:
            self._attr_state_class = SENSOR_TYPES[sensor_type]["state_class"]

        # Device info to group all sensors under one device
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Open-Meteo CloudCover",
            manufacturer="Open-Meteo",
            model="CloudCover Station",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url="https://open-meteo.com",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor (current hour value for today, first hour for future days)."""
        if self.coordinator.data:
            sensor_data = self.coordinator.data.get(self._sensor_key)
            if sensor_data:
                return sensor_data.get("current")
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of measurement."""
        return SENSOR_TYPES[self._sensor_type]["unit"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}

        sensor_data = self.coordinator.data.get(self._sensor_key, {})
        metadata = self.coordinator.data.get("_metadata", {})

        attributes = {
            "date": sensor_data.get("date"),
            "day_offset": sensor_data.get("day_offset"),
            "day_name": get_day_name(self._day_offset),
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "timezone": metadata.get("timezone"),
            "elevation": metadata.get("elevation"),
        }

        # Add hourly forecast data for this day
        hourly_forecast = sensor_data.get("hourly_forecast", {})
        if hourly_forecast:
            attributes["hourly_forecast"] = hourly_forecast
            attributes["min"] = sensor_data.get("min")
            attributes["max"] = sensor_data.get("max")
            attributes["avg"] = sensor_data.get("avg")

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._sensor_key in self.coordinator.data
        )
