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

        # Group times and values by date
        daily_data = defaultdict(lambda: defaultdict(list))

        for idx, time_str in enumerate(times):
            # Parse the timestamp to get the date
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
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
                    })

        # Calculate daily aggregates and assign day offsets
        sensor_data = {}
        start_date = min(daily_data.keys()) if daily_data else None

        if not start_date:
            return sensor_data

        for date_key in sorted(daily_data.keys()):
            # Calculate day offset from start date
            day_offset = (date_key - start_date).days

            for metric, hourly_values in daily_data[date_key].items():
                if not hourly_values:
                    continue

                # Extract just the numeric values for calculations
                values = [h["value"] for h in hourly_values]

                # Build the sensor data key: metric_dayoffset
                sensor_key = f"{metric}_{day_offset}"

                sensor_data[sensor_key] = {
                    "date": str(date_key),
                    "day_offset": day_offset,
                    "hourly_forecast": {
                        "times": [h["time"] for h in hourly_values],
                        "values": values,
                    },
                    "min": round(min(values), 2) if values else None,
                    "max": round(max(values), 2) if values else None,
                    "avg": round(sum(values) / len(values), 2) if values else None,
                }

        return sensor_data
