# PyConvexity Data Module

The `pyconvexity.data` module provides functions for loading external energy data and integrating it with PyConvexity models. This is a simple, expert-friendly toolbox for working with real-world energy data.

## Installation

Install PyConvexity with data dependencies:

```bash
pip install pyconvexity[data]
```

## Current Data Sources

### Global Energy Monitor (GEM)

Load power plant data from GEM's Global Integrated Power dataset.

**Setup:**
1. Download the GEM Excel file: `Global-Integrated-Power-August-2025.xlsx`
2. Place it in a `data/raw/global-energy-monitor/` directory, or set the path manually

**Usage:**

```python
import pyconvexity as px

# Load generators for a specific country
generators = px.data.get_generators_from_gem(
    country="USA",  # ISO 3-letter country code
    technology_types=["solar", "wind", "nuclear"],  # Optional filter
    min_capacity_mw=100.0  # Optional minimum capacity
)

# Create a network and add generators
px.create_database_with_schema("my_model.db")

with px.database_context("my_model.db") as conn:
    network_id = px.create_network(conn, network_req)
    
    # Create carriers
    carriers = {}
    for carrier_name in generators['carrier'].unique():
        carriers[carrier_name] = px.create_carrier(conn, network_id, carrier_name)
    
    # Add generators to network
    generator_ids = px.data.add_gem_generators_to_network(
        conn, network_id, generators, carrier_mapping=carriers
    )
```

## Data Output Format

The `get_generators_from_gem()` function returns a pandas DataFrame with these columns:

- `plant_name`: Name of the power plant
- `country_iso_3`: ISO 3-letter country code
- `category`: Energy category (nuclear, thermal, renewables, storage, etc.)
- `carrier`: Energy carrier (coal, gas, solar, wind, nuclear, etc.)
- `type`: Technology type (subcritical, combined-cycle, photovoltaic, etc.)
- `capacity_mw`: Capacity in megawatts
- `start_year`: Year the plant started operation
- `latitude`: Latitude coordinate
- `longitude`: Longitude coordinate

## Technology Mapping

GEM technologies are automatically mapped to a standardized schema:

- **Nuclear**: pressurized-water-reactor, boiling-water-reactor, small-modular-reactor
- **Thermal**: subcritical, supercritical, combined-cycle, gas-turbine
- **Renewables**: photovoltaic, thermal (solar), onshore/offshore (wind), run-of-river (hydro)
- **Storage**: lithium-ion (battery), pumped-hydro
- **Bioenergy**: biomass, biogas

## Caching

Data is automatically cached for 7 days to improve performance. You can:

```python
# Disable caching
generators = px.data.get_generators_from_gem(country="USA", use_cache=False)

# Clear cache
cache = px.data.DataCache()
cache.clear_cache('gem_generators')
```

## Examples

See `examples/gem_data_example.py` for a complete working example.

## Future Data Sources

The framework is designed to be extensible. Planned additions include:

- IRENA Global Energy Atlas (renewable resource data)
- World Bank energy statistics
- IEA World Energy Outlook data
- OpenStreetMap transmission infrastructure
- NASA weather data for renewable profiles
