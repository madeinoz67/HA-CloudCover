"""DataUpdateCoordinator for Open-Meteo CloudCover integration."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

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
    ) -> None:
        """Initialize the coordinator."""
        self.latitude = latitude
        self.longitude = longitude

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Open-Meteo API."""
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "forecast_days": 2,  # Current day + next day
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
                        # Extract the latest (most recent) value for each sensor
                        hourly = data.get("hourly", {})
                        times = hourly.get("time", [])

                        if not times:
                            raise UpdateFailed("No data received from Open-Meteo API")

                        # Get the index of the most recent time entry
                        latest_idx = len(times) - 1

                        # Build sensor data with current value and historical data
                        sensor_data = {}
                        for key in [
                            "evapotranspiration",
                            "soil_temperature_0cm",
                            "soil_moisture_0_to_1cm",
                            "et0_fao_evapotranspiration",
                            "cloud_cover",
                            "cloud_cover_low",
                            "cloud_cover_mid",
                            "cloud_cover_high",
                        ]:
                            values = hourly.get(key, [])
                            if values and len(values) > latest_idx:
                                sensor_data[key] = {
                                    "current": values[latest_idx],
                                    "history": list(zip(times, values)),
                                    "latest_time": times[latest_idx],
                                }

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
