# PyConvexity

**Energy system modeling library for optimization and analysis.**

PyConvexity provides the core functionality of the [Convexity](https://github.com/bayesian-energy/convexity-js) desktop application as a reusable, pip-installable Python library.

## Installation

```bash
pip install pyconvexity
```

## Quick Start

```python
import pyconvexity as px

# Create a new energy system model database
px.create_database_with_schema("my_model.db")

# Create a network
with px.database_context("my_model.db") as conn:
    network_req = px.CreateNetworkRequest(
        name="My Energy Network",
        description="Example renewable energy system",
        start_time="2024-01-01 00:00:00",
        end_time="2024-01-02 00:00:00",
        time_resolution="H"
    )
    network_id = px.create_network(conn, network_req)
    
    # Create carriers (energy types)
    ac_carrier = px.create_carrier(conn, network_id, "AC")
    
    # Create components
    bus_id = px.create_component(
        conn, network_id, "BUS", "Main Bus",
        latitude=40.7128, longitude=-74.0060,
        carrier_id=ac_carrier
    )
    
    # Set component attributes
    px.set_static_attribute(conn, bus_id, "v_nom", px.StaticValue(230.0))
    
    conn.commit()

print(f"✅ Created network {network_id} with bus {bus_id}")
```

## Features

- **Database Management**: SQLite-based energy system model storage
- **Component Modeling**: Buses, generators, loads, lines, storage, etc.
- **Time Series Support**: Efficient storage and retrieval of temporal data
- **Validation**: Built-in validation rules for energy system components
- **PyPSA Integration**: Compatible with PyPSA energy system modeling
- **Type Safety**: Full type hints and data validation

## Core Concepts

### Networks
Energy system models organized as networks with time periods and carriers.

### Components
Physical and virtual elements: buses, generators, loads, transmission lines, storage units, etc.

### Attributes
Component properties that can be static values or time series data.

### Scenarios
Different parameter sets for the same network topology.

## Documentation

- **Full Documentation**: [Convexity Documentation](https://github.com/bayesian-energy/convexity-js)
- **API Reference**: See docstrings in the code
- **Examples**: Check the `examples/` directory

## Development

PyConvexity is developed as part of the [Convexity](https://github.com/bayesian-energy/convexity-js) project by [Bayesian Energy](https://bayesianenergy.com).

## License

MIT License - see [LICENSE](https://github.com/bayesian-energy/convexity-js/blob/main/LICENSE) file for details.

## Related Projects

- **[Convexity](https://github.com/bayesian-energy/convexity-js)**: Desktop application for energy system modeling
- **[PyPSA](https://pypsa.org/)**: Python for Power System Analysis
- **[Linopy](https://linopy.readthedocs.io/)**: Linear optimization with Python