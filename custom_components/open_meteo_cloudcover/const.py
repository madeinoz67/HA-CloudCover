"""Constants for the Open-Meteo CloudCover integration."""

DOMAIN = "open_meteo_cloudcover"

# Configuration
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_FORECAST_DAYS = "forecast_days"

# Defaults
DEFAULT_NAME = "Open-Meteo CloudCover"
DEFAULT_SCAN_INTERVAL = 3600  # 1 hour in seconds
DEFAULT_FORECAST_DAYS = 2  # Current day + next day
MIN_FORECAST_DAYS = 1
MAX_FORECAST_DAYS = 7

# API
API_URL = "https://api.open-meteo.com/v1/forecast"

# Sensor types
SENSOR_TYPES = {
    "evapotranspiration": {
        "name": "Evapotranspiration",
        "unit": "mm",
        "icon": "mdi:water-outline",
        "device_class": None,
        "state_class": "measurement",
    },
    "soil_temperature_0cm": {
        "name": "Soil Temperature (0cm)",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "soil_moisture_0_to_1cm": {
        "name": "Soil Moisture (0-1cm)",
        "unit": "m³/m³",
        "icon": "mdi:water-percent",
        "device_class": None,
        "state_class": "measurement",
    },
    "et0_fao_evapotranspiration": {
        "name": "FAO Evapotranspiration",
        "unit": "mm",
        "icon": "mdi:water-outline",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover": {
        "name": "Cloud Cover",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_low": {
        "name": "Cloud Cover Low",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_mid": {
        "name": "Cloud Cover Mid",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
    "cloud_cover_high": {
        "name": "Cloud Cover High",
        "unit": "%",
        "icon": "mdi:cloud",
        "device_class": None,
        "state_class": "measurement",
    },
}
