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

from .const import CONF_LATITUDE, CONF_LONGITUDE, DOMAIN, SENSOR_TYPES
from .coordinator import OpenMeteoDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Open-Meteo CloudCover sensor entities."""
    coordinator: OpenMeteoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Create sensor entities for each sensor type
    entities = []
    for sensor_type in SENSOR_TYPES:
        entities.append(
            OpenMeteoSensor(
                coordinator=coordinator,
                entry=entry,
                sensor_type=sensor_type,
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
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_type = sensor_type
        self._attr_name = f"{SENSOR_TYPES[sensor_type]['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
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
        """Return the state of the sensor."""
        if self.coordinator.data:
            sensor_data = self.coordinator.data.get(self._sensor_type)
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

        sensor_data = self.coordinator.data.get(self._sensor_type, {})
        metadata = self.coordinator.data.get("_metadata", {})

        attributes = {
            "latest_update": sensor_data.get("latest_time"),
            "latitude": metadata.get("latitude"),
            "longitude": metadata.get("longitude"),
            "timezone": metadata.get("timezone"),
            "elevation": metadata.get("elevation"),
        }

        # Add historical data (last 24 hours for quick access)
        history = sensor_data.get("history", [])
        if history:
            # Get last 24 hours of data
            recent_history = history[-24:]
            attributes["history_24h"] = {
                "times": [item[0] for item in recent_history],
                "values": [item[1] for item in recent_history],
            }

            # Add min/max for the period
            values = [item[1] for item in recent_history if item[1] is not None]
            if values:
                attributes["min_24h"] = min(values)
                attributes["max_24h"] = max(values)
                attributes["avg_24h"] = round(sum(values) / len(values), 2)

        return attributes

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._sensor_type in self.coordinator.data
        )
