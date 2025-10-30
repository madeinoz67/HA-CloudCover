# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-Meteo CloudCover is a custom Home Assistant integration that provides cloud cover, weather, and soil condition sensors using the Open-Meteo API. The integration polls the free Open-Meteo API every hour and creates 8 sensor entities grouped under a single device.

**Domain**: `open_meteo_cloudcover`
**Integration Type**: Cloud polling service (no API key required)
**Version**: 1.0.0

## Architecture

This is a standard Home Assistant custom integration following the modern coordinator pattern:

### Core Components

1. **`__init__.py`** - Integration entry point
   - Sets up the integration from config entries
   - Creates and stores the `OpenMeteoDataUpdateCoordinator` instance
   - Forwards setup to platform modules (sensor)

2. **`coordinator.py`** - Data fetching coordinator
   - `OpenMeteoDataUpdateCoordinator` extends Home Assistant's `DataUpdateCoordinator`
   - Fetches data from `https://api.open-meteo.com/v1/forecast` every hour
   - Transforms API response into sensor-friendly format
   - Extracts latest values and builds 24-hour history for each metric
   - Handles API errors and raises `UpdateFailed` on failures

3. **`config_flow.py`** - UI configuration
   - `OpenMeteoConfigFlow` handles user setup via Home Assistant UI
   - Defaults to Home Assistant instance latitude/longitude
   - Validates coordinates by test API call before accepting
   - Creates unique_id from coordinates to prevent duplicates

4. **`sensor.py`** - Sensor entities
   - `OpenMeteoSensor` extends `CoordinatorEntity` and `SensorEntity`
   - Creates 8 sensor entities (one per metric)
   - All sensors grouped under "Open-Meteo CloudCover" device
   - Exposes 24-hour historical data, min/max/avg in attributes

5. **`const.py`** - Constants and configuration
   - Domain, configuration keys, API URL
   - `SENSOR_TYPES` dict defines all 8 sensors with metadata (name, unit, icon, device_class, state_class)

6. **`strings.json`** - UI translations
   - Configuration flow text and error messages

7. **`manifest.json`** - Integration metadata
   - Domain, name, version, dependencies, requirements
   - IoT class, documentation links

### Data Flow

1. User adds integration via Home Assistant UI (config flow)
2. Config flow validates coordinates with test API call
3. `__init__.py` creates coordinator with validated coordinates
4. Coordinator fetches initial data on setup
5. Coordinator polls API every 3600 seconds (1 hour)
6. Each sensor reads its value from coordinator's cached data
7. Sensors update automatically when coordinator refreshes

### API Integration

The integration calls:
```
GET https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly={params}
```

**Hourly parameters requested:**
- `evapotranspiration`
- `soil_temperature_0cm`
- `soil_moisture_0_to_1cm`
- `et0_fao_evapotranspiration`
- `cloud_cover`
- `cloud_cover_low`
- `cloud_cover_mid`
- `cloud_cover_high`

The coordinator extracts the **latest** value from each hourly array and stores the full history for sensor attributes.

## Development Workflow

### Testing the Integration

1. **Copy to Home Assistant**:
   ```bash
   cp -r custom_components/open_meteo_cloudcover /path/to/homeassistant/custom_components/
   ```

2. **Restart Home Assistant**:
   - Settings → System → Restart
   - Or via CLI: `ha core restart`

3. **Add Integration**:
   - Settings → Devices & Services → Add Integration
   - Search for "Open-Meteo CloudCover"
   - Accept default coordinates or enter custom location

4. **Monitor Logs**:
   - Settings → System → Logs
   - Or tail log file: `tail -f /config/home-assistant.log`
   - Enable debug logging in `configuration.yaml`:
     ```yaml
     logger:
       default: info
       logs:
         custom_components.open_meteo_cloudcover: debug
     ```

5. **Reload Integration** (after code changes):
   - Settings → Devices & Services → Open-Meteo CloudCover → Reload
   - Or restart Home Assistant

### Modifying Sensors

To add/remove/modify sensors:

1. Update `SENSOR_TYPES` in `const.py`
2. Add the parameter name to the `hourly` list in `coordinator.py:_async_update_data()`
3. Update sensor extraction logic if the data format differs

### Changing Update Interval

Modify `DEFAULT_SCAN_INTERVAL` in `const.py` (value in seconds).

### API Changes

If the Open-Meteo API changes:
- Update the `API_URL` constant in `const.py`
- Modify parameter names in `coordinator.py`
- Adjust data extraction logic in `_async_update_data()` method

## Key Patterns to Follow

### Home Assistant Integration Standards

- Use `DataUpdateCoordinator` for all API polling (already implemented)
- Never poll API directly from sensors - always use the coordinator
- Set proper `device_class`, `state_class`, and `unit_of_measurement` for sensors
- Group related sensors under a single device using `DeviceInfo`
- Use async/await throughout (all I/O operations must be async)
- Handle errors gracefully and raise `UpdateFailed` in coordinator

### Configuration

- Always use config flow (UI-based) rather than YAML configuration
- Validate user input before accepting (see `validate_coordinates()`)
- Set unique_id for both the config entry and individual sensors
- Use `self.hass.config.latitude` for default values

### Error Handling

- Wrap all network calls in try/except with specific error types
- Use `UpdateFailed` exception in coordinator for fetch failures
- Log errors at appropriate severity levels (`_LOGGER.error`, `_LOGGER.warning`)
- Return `None` for unavailable sensor values rather than raising

## File Modification Notes

- **manifest.json**: Update `version` when releasing, update `requirements` if adding Python dependencies
- **strings.json**: Add translations here for any new config flow messages
- **const.py**: Central location for all magic numbers and configuration constants
- Do not modify coordinator update interval below 600 seconds to respect API rate limits

## Integration Boundaries

This integration:
- ✅ Fetches and displays sensor data
- ✅ Provides historical data in attributes
- ✅ Auto-detects Home Assistant location
- ❌ Does not forecast future values (displays only what API returns)
- ❌ Does not require authentication (free API)
- ❌ Does not have services or actions (sensor-only)

## Home Assistant Conventions

The integration follows Home Assistant's official integration standards:
- Modern coordinator pattern for efficient data fetching
- Config flow for UI-based setup
- Proper entity naming and unique IDs
- Device registry integration
- State class for long-term statistics
- Async implementation throughout
