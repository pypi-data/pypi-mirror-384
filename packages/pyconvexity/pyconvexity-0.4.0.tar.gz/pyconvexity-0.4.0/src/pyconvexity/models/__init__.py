"""
Model management module for PyConvexity.

Contains high-level operations for networks, components, and attributes.
"""

from pyconvexity.models.components import (
    get_component_type, get_component, list_components_by_type,
    insert_component, create_component, update_component, delete_component,
    list_component_attributes, get_default_carrier_id, get_bus_name_to_id_map,
    get_component_by_name, get_component_id, component_exists, get_component_carrier_map
)

from pyconvexity.models.attributes import (
    set_static_attribute, set_timeseries_attribute, get_attribute, delete_attribute,
    get_timeseries, get_timeseries_metadata
)

from pyconvexity.models.network import (
    create_network, get_network_info, get_network_time_periods, list_networks,
    create_carrier, get_network_config, set_network_config,
    get_component_counts, get_master_scenario_id, resolve_scenario_id,
    get_first_network, get_network_by_name
)

# Import from new modules
from pyconvexity.models.scenarios import (
    list_scenarios,
    get_scenario_by_name, get_scenario_by_id, get_master_scenario,
    Scenario
)

from pyconvexity.models.results import (
    get_solve_results, get_yearly_results,
    SolveResults, YearlyResults
)

from pyconvexity.models.carriers import (
    list_carriers,
    get_carrier_by_name, get_carrier_by_id, get_carrier_colors,
    Carrier
)

# Backward compatibility aliases
def get_scenario(conn, scenario_id):
    """Backward compatible alias for get_scenario_by_id."""
    return get_scenario_by_id(conn, scenario_id)

def create_scenario(conn, network_id, name, description=None, is_master=False):
    """
    Create a new scenario.
    
    Args:
        conn: Database connection
        network_id: Network ID
        name: Scenario name
        description: Optional description
        is_master: Whether this is the master scenario (will demote existing master)
        
    Returns:
        Scenario ID
    """
    cursor = conn.execute("""
        INSERT INTO scenarios (network_id, name, description, is_master)
        VALUES (?, ?, ?, ?)
    """, (network_id, name, description, is_master))
    
    scenario_id = cursor.lastrowid
    return scenario_id

def delete_scenario(conn, scenario_id):
    """
    Delete a scenario (cannot delete master scenario).
    
    Args:
        conn: Database connection
        scenario_id: Scenario ID to delete
        
    Raises:
        ValidationError: If trying to delete master scenario or scenario doesn't exist
    """
    from pyconvexity.core.errors import ValidationError
    
    # Check if it's a master scenario
    scenario = get_scenario_by_id(conn, scenario_id)
    if scenario.is_master:
        raise ValidationError("Cannot delete master scenario")
    
    # Delete the scenario
    cursor = conn.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
    
    if cursor.rowcount == 0:
        raise ValidationError(f"Scenario with ID {scenario_id} not found")

__all__ = [
    # Component operations
    "get_component_type", "get_component", "list_components_by_type",
    "insert_component", "create_component", "update_component", "delete_component",
    "list_component_attributes", "get_default_carrier_id", "get_bus_name_to_id_map",
    "get_component_by_name", "get_component_id", "component_exists", "get_component_carrier_map",
    
    # Attribute operations
    "set_static_attribute", "set_timeseries_attribute", "get_attribute", "delete_attribute",
    "get_timeseries", "get_timeseries_metadata",
    
    # Network operations
    "create_network", "get_network_info", "get_network_time_periods", "list_networks",
    "create_carrier", "list_carriers", "get_network_config", "set_network_config",
    "get_component_counts", "get_master_scenario_id", "resolve_scenario_id",
    "get_first_network", "get_network_by_name",
    
    # Scenario operations (backward compatible)
    "create_scenario", "list_scenarios", "get_scenario", "delete_scenario",
    "get_scenario_by_name", "get_scenario_by_id", "get_master_scenario",
    "Scenario",
    
    # Results operations
    "get_solve_results", "get_yearly_results",
    "SolveResults", "YearlyResults",
    
    # Carrier operations
    "get_carrier_by_name", "get_carrier_by_id", "get_carrier_colors",
    "Carrier",
]
