"""
PyConvexity - Python library for energy system modeling and optimization.

This library provides the core functionality of the Convexity desktop application
as a reusable, pip-installable package for building and solving energy system models.
"""

# Version information
from pyconvexity._version import __version__

__author__ = "Convexity Team"

# Core imports - always available
from pyconvexity.core.errors import (
    PyConvexityError,
    DatabaseError,
    ValidationError,
    ComponentNotFound,
    AttributeNotFound,
)

from pyconvexity.core.types import (
    StaticValue,
    Timeseries,
    TimeseriesMetadata,
    Component,
    Network,
    CreateNetworkRequest,
    CreateComponentRequest,
)

from pyconvexity.core.database import (
    create_database_with_schema,
    database_context,
    open_connection,
    validate_database,
    # Database maintenance functions
    vacuum_database,
    analyze_database,
    optimize_database,
    get_database_size_info,
    should_optimize_database,
)

# Import main API functions
from pyconvexity.models import (
    # Component operations
    get_component, create_component, update_component, delete_component,
    list_components_by_type, list_component_attributes,
    
    # Attribute operations  
    set_static_attribute, set_timeseries_attribute, get_attribute, delete_attribute,
    
    # Network operations
    create_network, get_network_info, get_network_time_periods, list_networks,
    create_carrier, list_carriers, get_network_config, set_network_config,
    get_master_scenario_id, resolve_scenario_id,
    
    # Scenario operations
    create_scenario, list_scenarios, get_scenario, delete_scenario,
)

from pyconvexity.validation import (
    get_validation_rule, list_validation_rules, validate_timeseries_alignment
)

# High-level timeseries API - recommended for new code
from pyconvexity.timeseries import (
    get_timeseries, set_timeseries, get_timeseries_metadata,
    get_multiple_timeseries, timeseries_to_numpy, numpy_to_timeseries
)

# High-level API functions
__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core types
    "StaticValue",
    "Timeseries",
    "TimeseriesMetadata", 
    "Component",
    "Network",
    "CreateNetworkRequest",
    "CreateComponentRequest",
    
    # Database operations
    "create_database_with_schema",
    "database_context", 
    "open_connection",
    "validate_database",
    
    # Database maintenance
    "vacuum_database",
    "analyze_database", 
    "optimize_database",
    "get_database_size_info",
    "should_optimize_database",
    
    # Exceptions
    "PyConvexityError",
    "DatabaseError",
    "ValidationError",
    "ComponentNotFound",
    "AttributeNotFound",
    
    # Component operations
    "get_component", "create_component", "update_component", "delete_component",
    "list_components_by_type", "list_component_attributes",
    
    # Attribute operations
    "set_static_attribute", "set_timeseries_attribute", "get_attribute", "delete_attribute",
    
    # Network operations
    "create_network", "get_network_info", "get_network_time_periods", "list_networks",
    "create_carrier", "list_carriers", "get_network_config", "set_network_config",
    "get_master_scenario_id", "resolve_scenario_id",
    
    # Scenario operations
    "create_scenario", "list_scenarios", "get_scenario", "delete_scenario",
    
    # Validation
    "get_validation_rule", "list_validation_rules", "validate_timeseries_alignment",
    
    # High-level timeseries API
    "get_timeseries", "set_timeseries", "get_timeseries_metadata",
    "get_multiple_timeseries", "timeseries_to_numpy", "numpy_to_timeseries",
]

# Data module imports
try:
    from pyconvexity import data
    __all__.append("data")
except ImportError:
    # Data dependencies not available
    pass

# Optional imports with graceful fallbacks
try:
    from pyconvexity.solvers.pypsa import (
        solve_network, build_pypsa_network, solve_pypsa_network,
        load_network_components, apply_constraints, store_solve_results
    )
    __all__.extend([
        "solve_network", "build_pypsa_network", "solve_pypsa_network",
        "load_network_components", "apply_constraints", "store_solve_results"
    ])
except ImportError:
    # PyPSA not available
    pass

# Excel I/O functionality
try:
    from pyconvexity.io import ExcelModelExporter, ExcelModelImporter
    __all__.extend([
        "ExcelModelExporter", "ExcelModelImporter"
    ])
except ImportError:
    # Excel dependencies not available
    pass


try:
    from pyconvexity.io import NetCDFModelExporter, NetCDFModelImporter
    __all__.extend(["NetCDFModelExporter", "NetCDFModelImporter"])
except ImportError:
    # NetCDF dependencies not available
    pass
