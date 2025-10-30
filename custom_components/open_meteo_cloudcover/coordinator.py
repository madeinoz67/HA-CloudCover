"""DataUpdateCoordinator for Open-Meteo CloudCover integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    API_URL,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class OpenMeteoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Open-Meteo CloudCover data."""

    def __init__(
        self,
        hass: HomeAssistant,
        latitude: float,
        longitude: float,
        forecast_days: int = 2,
    ) -> None:
        """Initialize the coordinator."""
        self.latitude = latitude
        self.longitude = longitude
        self.forecast_days = forecast_days

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Open-Meteo API."""
        # Use Home Assistant's configured timezone
        timezone = str(self.hass.config.time_zone)

        # Calculate date range: from today to forecast_days in the future
        now = dt_util.now()
        start_date = now.strftime("%Y-%m-%d")
        end_date = (now + timedelta(days=self.forecast_days)).strftime("%Y-%m-%d")

        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": start_date,
            "end_date": end_date,
            "timezone": timezone,  # Request data in HA timezone
            "hourly": ",".join([
                "evapotranspiration",
                "soil_temperature_0cm",
                "soil_moisture_0_to_1cm",
                "et0_fao_evapotranspiration",
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
            ]),
        }

        try:
            async with async_timeout.timeout(30):
                async with aiohttp.ClientSession() as session:
                    async with session.get(API_URL, params=params) as response:
                        response.raise_for_status()
                        data = await response.json()

                        # Transform the data to make it easier to work with
                        # Group hourly forecast data by day
                        hourly = data.get("hourly", {})
                        times = hourly.get("time", [])

                        if not times:
                            raise UpdateFailed("No data received from Open-Meteo API")

                        # Build sensor data grouped by day and metric
                        sensor_data = self._group_by_day(times, hourly)

                        # Add metadata
                        sensor_data["_metadata"] = {
                            "latitude": data.get("latitude"),
                            "longitude": data.get("longitude"),
                            "timezone": data.get("timezone"),
                            "elevation": data.get("elevation"),
                        }

                        return sensor_data

        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error communicating with Open-Meteo API: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error fetching data: {err}") from err

    def _group_by_day(self, times: list[str], hourly: dict[str, list]) -> dict[str, Any]:
        """Group hourly forecast data by day for each metric."""
        from collections import defaultdict
        from datetime import timezone

        # Get current time for finding closest hour (timezone-aware)
        now = dt_util.now()

        # Group times and values by date
        daily_data = defaultdict(lambda: defaultdict(list))

        for idx, time_str in enumerate(times):
            # Parse the timestamp - Open-Meteo returns ISO format strings
            # in the timezone we requested (HA's timezone)
            try:
                # Try parsing with fromisoformat first
                dt = datetime.fromisoformat(time_str)

                # If it's naive (no timezone), the API returned it in our requested timezone
                # So we need to attach HA's timezone to it (not convert, just attach)
                if dt.tzinfo is None:
                    # The timestamp is already in HA's timezone, just make it aware
                    dt = dt_util.as_local(dt)

            except Exception as err:
                _LOGGER.warning("Failed to parse timestamp %s: %s", time_str, err)
                continue

            date_key = dt.date()

            # Store each metric's value for this hour
            for metric in [
                "evapotranspiration",
                "soil_temperature_0cm",
                "soil_moisture_0_to_1cm",
                "et0_fao_evapotranspiration",
                "cloud_cover",
                "cloud_cover_low",
                "cloud_cover_mid",
                "cloud_cover_high",
            ]:
                values = hourly.get(metric, [])
                if idx < len(values) and values[idx] is not None:
                    daily_data[date_key][metric].append({
                        "time": time_str,
                        "value": values[idx],
                        "datetime": dt,
                    })

        # Calculate daily aggregates and assign day offsets
        sensor_data = {}

        # Use current date (today) as the reference for day offset calculation
        today = now.date()

        for date_key in sorted(daily_data.keys()):
            # Calculate day offset from today (0=today, 1=tomorrow, etc.)
            day_offset = (date_key - today).days

            for metric, hourly_values in daily_data[date_key].items():
                if not hourly_values:
                    continue

                # Extract just the numeric values for calculations
                values = [h["value"] for h in hourly_values]

                # Find the current hour's value (closest to now without going into the past)
                current_value = None
                if day_offset == 0:  # Only for today
                    # Find the value for current or next hour
                    for h in hourly_values:
                        if h["datetime"] >= now:
                            current_value = h["value"]
                            break
                    # If no future hour found, use the last hour of today
                    if current_value is None and hourly_values:
                        current_value = hourly_values[-1]["value"]
                else:
                    # For future days, use first hour of the day
                    current_value = hourly_values[0]["value"] if hourly_values else None

                # Build the sensor data key: metric_dayoffset
                sensor_key = f"{metric}_{day_offset}"

                sensor_data[sensor_key] = {
                    "date": str(date_key),
                    "day_offset": day_offset,
                    "current": current_value,
                    "hourly_forecast": {
                        "times": [h["time"] for h in hourly_values],
                        "values": values,
                    },
                    "min": round(min(values), 2) if values else None,
                    "max": round(max(values), 2) if values else None,
                    "avg": round(sum(values) / len(values), 2) if values else None,
                }

        return sensor_data
