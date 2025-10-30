"""Diagnostics support for Open-Meteo CloudCover integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OpenMeteoDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: OpenMeteoDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get coordinator data
    coordinator_data = coordinator.data if coordinator.data else {}

    # Build diagnostics data
    diagnostics_data = {
        "entry": {
            "title": entry.title,
            "data": {
                "latitude": entry.data.get("latitude"),
                "longitude": entry.data.get("longitude"),
                "forecast_days": entry.data.get("forecast_days"),
            },
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "last_update_time": coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None,
            "update_interval": coordinator.update_interval.total_seconds()
            if coordinator.update_interval
            else None,
            "forecast_days": coordinator.forecast_days,
        },
        "data_summary": {
            "sensor_count": len([k for k in coordinator_data.keys() if k != "_metadata"]),
            "metadata": coordinator_data.get("_metadata", {}),
        },
        "sensors": {},
    }

    # Add sample data from each sensor (sanitized)
    for key, value in coordinator_data.items():
        if key == "_metadata":
            continue

        if isinstance(value, dict):
            # Sanitize sensor data - include structure but limit array sizes
            sensor_info = {
                "date": value.get("date"),
                "day_offset": value.get("day_offset"),
                "current": value.get("current"),
                "min": value.get("min"),
                "max": value.get("max"),
                "avg": value.get("avg"),
            }

            # Include hourly forecast structure but limit to first few entries
            hourly = value.get("hourly_forecast", {})
            if hourly:
                times = hourly.get("times", [])
                values = hourly.get("values", [])
                sensor_info["hourly_forecast_sample"] = {
                    "count": len(times),
                    "first_3": {
                        "times": times[:3] if times else [],
                        "values": values[:3] if values else [],
                    },
                    "last_3": {
                        "times": times[-3:] if times else [],
                        "values": values[-3:] if values else [],
                    },
                }

            diagnostics_data["sensors"][key] = sensor_info

    return diagnostics_data
