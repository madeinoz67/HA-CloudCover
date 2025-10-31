# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open-Meteo CloudCover is a custom Home Assistant integration that provides cloud cover, weather, and soil condition sensors using the Open-Meteo API. The integration polls the free Open-Meteo API at hourly boundaries (XX:00:05) and creates 342 sensor entities grouped under a single device (45 enabled by default, 297 disabled by default).

**Domain**: `open_meteo_cloudcover`
**Integration Type**: Cloud polling service (no API key required)
**Version**: 2025.10.1 (CalVer format: YYYY.MM.PATCH)

## Architecture

This is a standard Home Assistant custom integration following the modern coordinator pattern:

### Core Components

1. **`__init__.py`** - Integration entry point
   - Sets up the integration from config entries
   - Creates and stores the `OpenMeteoDataUpdateCoordinator` instance
   - Forwards setup to platform modules (sensor)

2. **`coordinator.py`** - Data fetching coordinator
   - `OpenMeteoDataUpdateCoordinator` extends Home Assistant's `DataUpdateCoordinator`
   - Fetches data from `https://api.open-meteo.com/v1/forecast` at hourly boundaries
   - Requests 7 days of hourly forecast data
   - Transforms API response into sensor-friendly format via three extraction passes
   - Dynamically calculates next update interval to align with hour boundaries
   - Handles API errors and raises `UpdateFailed` on failures

3. **`config_flow.py`** - UI configuration
   - `OpenMeteoConfigFlow` handles user setup via Home Assistant UI
   - Defaults to Home Assistant instance latitude/longitude
   - Validates coordinates by test API call before accepting
   - Creates unique_id from coordinates to prevent duplicates

4. **`sensor.py`** - Sensor entities
   - `OpenMeteoSensor` extends `CoordinatorEntity` and `SensorEntity`
   - Creates 342 sensor entities across multiple time formats:
     - 9 "This Hour" sensors (enabled by default)
     - 9 "Next Hour" sensors (enabled by default)
     - 216 hourly sensors: Hours 1-24 × 9 metrics (disabled by default)
     - 72 daily sensors: Days 0-7 × 9 metrics (Days 0-2 enabled, Days 3-7 disabled)
   - All sensors grouped under "Open-Meteo CloudCover" device
   - Daily sensors expose hourly forecast data, min/max/avg in attributes
   - Hourly sensors expose hour_offset attribute
   - Cloud Cover Low/Mid/High sensors disabled by default for all time periods

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
5. Coordinator polls API at hourly boundaries (XX:00:05) with dynamic interval calculation
6. Coordinator fetches 7 days of hourly forecast data
7. Coordinator extracts:
   - This Hour / Next Hour values for each metric
   - Hours 1-24 values from current time for each metric
   - Daily data grouped by day (0-7) with hourly forecasts
8. Each sensor reads its value from coordinator's cached data
9. Sensors update automatically when coordinator refreshes

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
- `direct_radiation`

The coordinator processes hourly data in multiple passes:
1. **First pass**: Extract This Hour and Next Hour values using hour boundary matching
2. **Second pass**: Group data by day, calculate daily aggregates (min/max/avg), build hourly forecast dictionaries
3. **Third pass**: Extract Hours 1-24 from current time using hour boundary matching

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
3. Add the metric to all three extraction passes in `_group_by_day()`:
   - First pass: This Hour / Next Hour extraction
   - Second pass: Daily aggregation
   - Third pass: Hourly extraction (Hours 1-24)
4. Update sensor creation loops in `sensor.py:async_setup_entry()`
5. Update sensor type handling in `OpenMeteoSensor.__init__()`

### Changing Update Interval

The integration uses dynamic interval calculation to align with hourly boundaries (XX:00:05).
This is implemented in `coordinator.py:_calculate_next_update_interval()`.
If you need to change the static fallback interval, modify `DEFAULT_SCAN_INTERVAL` in `const.py`.

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

- **manifest.json**: Update `version` when releasing (CalVer format: YYYY.MM.PATCH), update `requirements` if adding Python dependencies
- **strings.json**: Add translations here for any new config flow messages
- **const.py**: Central location for all magic numbers and configuration constants
- **coordinator.py**: Contains three data extraction passes - maintain all three when adding metrics
- **sensor.py**: Update sensor creation loops, type handling, and disabled-by-default logic when changing sensor architecture
- The integration respects API rate limits by polling at hour boundaries rather than continuous polling

## Integration Boundaries

This integration:
- ✅ Fetches and displays sensor data in multiple time formats
- ✅ Provides hourly forecast data (up to 24 hours ahead)
- ✅ Provides daily forecast data (up to 7 days ahead)
- ✅ Provides historical data within daily sensor attributes
- ✅ Auto-detects Home Assistant location
- ✅ Aligns polling to hour boundaries for optimal data freshness
- ✅ Supports selective enabling of 264 optional sensors via entity registry
- ❌ Does not require authentication (free API)
- ❌ Does not have services or actions (sensor-only)

## Home Assistant Conventions

The integration follows Home Assistant's official integration standards:
- Modern coordinator pattern for efficient data fetching
- Config flow for UI-based setup
- Proper entity naming and unique IDs
- Device registry integration with 304 sensors under one device
- State class for long-term statistics
- Async implementation throughout
- Entity registry enabled_default control for optional sensors
- Calendar versioning (CalVer) for release tracking
- Timezone-aware datetime handling throughout
