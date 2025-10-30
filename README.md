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

Each sensor includes:
- Current value
- 24-hour historical data
- Min/max/average values for the last 24 hours
- Location metadata (latitude, longitude, timezone, elevation)

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

The integration fetches data from the Open-Meteo API every hour (3600 seconds). This is a reasonable interval for weather and soil condition monitoring while respecting the API's free tier.

## Sensors

All sensors are grouped under a single device called "Open-Meteo CloudCover" for easy organization.

### Example Sensor Attributes

```yaml
state: 45
latest_update: "2025-10-30T12:00"
latitude: -33.375
longitude: 115.625
timezone: GMT
elevation: 3.0
history_24h:
  times:
    - "2025-10-29T13:00"
    - "2025-10-29T14:00"
    # ... (24 hours of data)
  values:
    - 42
    - 44
    # ... (24 hours of data)
min_24h: 35
max_24h: 58
avg_24h: 45.5
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
