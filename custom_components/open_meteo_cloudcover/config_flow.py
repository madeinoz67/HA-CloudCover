"""Config flow for Open-Meteo CloudCover integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    API_URL,
    CONF_FORECAST_DAYS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DEFAULT_FORECAST_DAYS,
    DOMAIN,
    MAX_FORECAST_DAYS,
    MIN_FORECAST_DAYS,
)

_LOGGER = logging.getLogger(__name__)


async def validate_coordinates(
    hass: HomeAssistant, latitude: float, longitude: float
) -> dict[str, Any]:
    """Validate the coordinates by making a test API call."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "cloud_cover",
    }

    try:
        async with async_timeout.timeout(10):
            async with aiohttp.ClientSession() as session:
                async with session.get(API_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if "hourly" not in data:
                        raise ValueError("Invalid response from API")

                    return {"title": f"Open-Meteo CloudCover ({latitude}, {longitude})"}

    except aiohttp.ClientError:
        raise CannotConnect
    except Exception as err:
        _LOGGER.exception("Unexpected exception: %s", err)
        raise UnknownError from err


class OpenMeteoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Open-Meteo CloudCover."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                info = await validate_coordinates(
                    self.hass,
                    user_input[CONF_LATITUDE],
                    user_input[CONF_LONGITUDE],
                )

                # Check if already configured
                await self.async_set_unique_id(
                    f"{user_input[CONF_LATITUDE]}_{user_input[CONF_LONGITUDE]}"
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_coords"
            except UnknownError:
                errors["base"] = "unknown"

        # Show form with defaults from Home Assistant configuration
        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_LATITUDE,
                    default=self.hass.config.latitude,
                ): vol.Coerce(float),
                vol.Required(
                    CONF_LONGITUDE,
                    default=self.hass.config.longitude,
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_FORECAST_DAYS,
                    default=DEFAULT_FORECAST_DAYS,
                ): vol.All(vol.Coerce(int), vol.Range(min=MIN_FORECAST_DAYS, max=MAX_FORECAST_DAYS)),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class UnknownError(Exception):
    """Error to indicate an unknown error occurred."""
