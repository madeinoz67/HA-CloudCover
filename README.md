# Open-Meteo CloudCover Integration for Home Assistant

A custom Home Assistant integration that provides cloud cover, weather, and soil condition sensors using the Open-Meteo API.

## Features

This integration creates sensors for:

- **Evapotranspiration** - Water evaporation from soil and plants (mm)
- **Soil Temperature (0cm)** - Surface soil temperature (°C)
- **Soil Moisture (0-1cm)** - Surface soil moisture content (m³/m³)
- **FAO Evapotranspiration** - Reference evapotranspiration using FAO method (mm)
- **Cloud Cover** - Total cloud coverage (%)
- **Cloud Cover Low** - Low-altitude cloud coverage (%)
- **Cloud Cover Mid** - Mid-altitude cloud coverage (%)
- **Cloud Cover High** - High-altitude cloud coverage (%)
- **Direct Radiation** - Direct solar radiation (W/m²)

The integration creates sensors for each metric in multiple time formats:
- **This Hour** - Current hour block value (e.g., at 11:30, shows 11:00 forecast)
- **Next Hour** - Next hour block value (e.g., at 11:30, shows 12:00 forecast)
- **Hourly Sensors** - Hours 1-24 from current time (disabled by default)
- **Daily Sensors** - Days 0-7 (Today through Day 7)
  - Days 0-2 (Today, Tomorrow, Day 2) enabled by default
  - Days 3-7 disabled by default

Each daily sensor includes:
- Daily average value
- Hourly forecast data for the day
- Min/max/average values
- Location metadata (latitude, longitude, timezone, elevation)

Each hourly sensor includes:
- Specific hour forecast value
- Hour offset from current time
- Location metadata

## Installation

### Manual Installation

1. Copy the `custom_components/open_meteo_cloudcover` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Open-Meteo CloudCover"
5. Click "Submit" to use your Home Assistant instance location (or modify the coordinates if needed)

### HACS Installation (Future)

This integration may be added to HACS in the future for easier installation.

## Configuration

The integration uses a config flow for setup:

1. **Latitude** - Defaults to your Home Assistant instance location
2. **Longitude** - Defaults to your Home Assistant instance location

You can simply click "Submit" without changing anything to use your Home Assistant's configured location.

## Data Updates

The integration fetches data from the Open-Meteo API at hourly boundaries (XX:00:05). This alignment ensures fresh data is available at the start of each hour while respecting the API's free tier.

## Sensors

All sensors are grouped under a single device called "Open-Meteo CloudCover" for easy organization.

**Total Sensors**: 342 sensors (45 enabled by default)
- This Hour sensors: 9 (enabled)
- Next Hour sensors: 9 (enabled)
- Hourly sensors: 216 (24 hours × 9 metrics, disabled by default)
- Daily sensors (Days 0-2): 27 (enabled)
- Extended daily sensors (Days 3-7): 45 (disabled by default)

**Disabled by Default**:
- Cloud Cover Low, Mid, and High sensors (all time periods)
- All hourly forecast sensors (Hours 1-24)
- Extended daily forecast sensors (Days 3-7)

All disabled sensors can be enabled via the entity registry in Home Assistant.

### Example Daily Sensor Attributes

```yaml
state: 45.5
date: "2025-10-30"
day_offset: 0
day_name: "Today"
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
forecast_data:
  "2025-10-30T00:00": 42
  "2025-10-30T01:00": 43
  "2025-10-30T02:00": 44
  # ... (hourly data for the day)
  "2025-10-30T23:00": 48
min: 35
max: 58
avg: 45.5
```

### Example This Hour / Next Hour Sensor Attributes

```yaml
state: 45
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
```

### Example Hourly Sensor Attributes

```yaml
state: 47
hour_offset: 5
latitude: -33.375
longitude: 115.625
timezone: "Australia/Perth"
elevation: 3.0
```

## API Information

This integration uses the free Open-Meteo API:
- **API Endpoint**: https://api.open-meteo.com/v1/forecast
- **Rate Limits**: The free tier should be sufficient for typical home use
- **Documentation**: https://open-meteo.com/en/docs

No API key is required.

## Use Cases

This integration is perfect for:

- **Garden Automation** - Use soil moisture and temperature to trigger irrigation
- **Cloud Coverage Monitoring** - Track cloud cover for solar panel optimization
- **Evapotranspiration Tracking** - Calculate water needs for plants
- **Weather Monitoring** - Keep tabs on detailed weather conditions

### Example Automation

```yaml
automation:
  - alias: "Water Garden Based on Soil Moisture"
    trigger:
      - platform: numeric_state
        entity_id: sensor.soil_moisture_0_1cm
        below: 0.15
    condition:
      - condition: numeric_state
        entity_id: sensor.evapotranspiration
        above: 0.5
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garden_irrigation
```

## Troubleshooting

### No Data Received

If sensors show as unavailable:
1. Check your internet connection
2. Verify the Open-Meteo API is accessible: https://api.open-meteo.com
3. Check Home Assistant logs for error messages

### Invalid Coordinates

Ensure your coordinates are valid:
- Latitude: -90 to 90
- Longitude: -180 to 180

### API Errors

If you see API errors in the logs:
1. Check if the Open-Meteo service is operational
2. Verify network connectivity
3. Consider increasing the update interval if rate limits are an issue

## Development

This integration follows Home Assistant's best practices:

- Uses `DataUpdateCoordinator` for efficient API polling
- Implements proper error handling and retry logic
- Provides comprehensive device and sensor information
- Uses async/await patterns throughout
- Includes proper typing hints

## Credits

- Weather data provided by [Open-Meteo](https://open-meteo.com)
- Integration developed using Home Assistant's integration guidelines

## License

This integration is provided as-is for personal use.

## Support

For issues or feature requests, please open an issue on the GitHub repository.
