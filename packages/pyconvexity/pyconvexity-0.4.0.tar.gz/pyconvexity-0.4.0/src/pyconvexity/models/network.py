"""
Network management operations for PyConvexity.

Provides operations for creating, managing, and querying energy system networks
including time periods, carriers, and network configuration.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from pyconvexity.core.types import (
    CreateNetworkRequest, TimePeriod, Network
)
from pyconvexity.core.errors import (
    ValidationError, DatabaseError
)

logger = logging.getLogger(__name__)


def create_network(conn: sqlite3.Connection, request: CreateNetworkRequest) -> int:
    """
    Create a network record and return network ID.
    
    Args:
        conn: Database connection
        request: Network creation request
        
    Returns:
        ID of the newly created network
        
    Raises:
        ValidationError: If required fields are missing
        DatabaseError: If creation fails
    """
    
    # Validate required fields
    if not request.start_time:
        raise ValidationError("start_time is required")
    if not request.end_time:
        raise ValidationError("end_time is required")
    
    cursor = conn.execute("""
        INSERT INTO networks (name, description, time_start, time_end, time_interval, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
    """, (
        request.name,
        request.description or f"Created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        request.start_time,
        request.end_time,
        request.time_resolution or 'H'
    ))
    
    network_id = cursor.lastrowid
    if not network_id:
        raise DatabaseError("Failed to create network")
    
    # Master scenario is automatically created by database trigger
    # No need to call create_master_scenario() manually
    
    return network_id


def get_network_info(conn: sqlite3.Connection, network_id: int) -> Dict[str, Any]:
    """
    Get network information.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        Dictionary with network information
        
    Raises:
        ValidationError: If network doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, name, description, time_start, time_end, time_interval, created_at, updated_at
        FROM networks 
        WHERE id = ?
    """, (network_id,))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"Network with ID {network_id} not found")
    
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "time_start": row[3],
        "time_end": row[4],
        "time_interval": row[5],
        "created_at": row[6],
        "updated_at": row[7]
    }


def get_network_time_periods(
    conn: sqlite3.Connection,
    network_id: int
) -> List[TimePeriod]:
    """
    Get network time periods using optimized storage.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        List of TimePeriod objects ordered by period_index
    """
    cursor = conn.execute("""
        SELECT period_count, start_timestamp, interval_seconds 
        FROM network_time_periods 
        WHERE network_id = ?
    """, (network_id,))
    
    row = cursor.fetchone()
    if not row:
        return []  # No time periods defined
    
    period_count, start_timestamp, interval_seconds = row
    
    # Generate all time periods computationally
    periods = []
    for period_index in range(period_count):
        timestamp = start_timestamp + (period_index * interval_seconds)
        
        # Format timestamp as string for compatibility - ALWAYS use UTC to avoid DST duplicates
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        periods.append(TimePeriod(
            timestamp=timestamp,
            period_index=period_index,
            formatted_time=formatted_time
        ))
    
    return periods


def list_networks(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    List all networks.
    
    Args:
        conn: Database connection
        
    Returns:
        List of network dictionaries
    """
    cursor = conn.execute("""
        SELECT id, name, description, created_at, updated_at, time_interval, time_start, time_end 
        FROM networks 
        ORDER BY created_at DESC
    """)
    
    networks = []
    for row in cursor.fetchall():
        networks.append({
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3],
            "updated_at": row[4],
            "time_resolution": row[5],  # time_interval from DB mapped to time_resolution
            "start_time": row[6],       # time_start from DB mapped to start_time
            "end_time": row[7],         # time_end from DB mapped to end_time
        })
    
    return networks


def get_first_network(conn: sqlite3.Connection) -> Optional[Dict[str, Any]]:
    """
    Get the first network (useful for single-network databases).
    
    Args:
        conn: Database connection
        
    Returns:
        Network dictionary or None if no networks exist
    """
    cursor = conn.execute("""
        SELECT id, name, description, created_at, updated_at, time_interval, time_start, time_end 
        FROM networks 
        ORDER BY created_at DESC
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "time_resolution": row[5],
        "start_time": row[6],
        "end_time": row[7],
    }


def get_network_by_name(conn: sqlite3.Connection, name: str) -> Optional[Dict[str, Any]]:
    """
    Get a network by name.
    
    Args:
        conn: Database connection
        name: Network name
        
    Returns:
        Network dictionary or None if not found
    """
    cursor = conn.execute("""
        SELECT id, name, description, created_at, updated_at, time_interval, time_start, time_end 
        FROM networks 
        WHERE name = ?
    """, (name,))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    return {
        "id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "time_resolution": row[5],
        "start_time": row[6],
        "end_time": row[7],
    }


def create_carrier(
    conn: sqlite3.Connection, 
    network_id: int, 
    name: str, 
    co2_emissions: float = 0.0,
    color: Optional[str] = None,
    nice_name: Optional[str] = None
) -> int:
    """
    Create a carrier record and return carrier ID.
    
    Args:
        conn: Database connection
        network_id: Network ID
        name: Carrier name
        co2_emissions: CO2 emissions factor
        color: Display color
        nice_name: Human-readable name
        
    Returns:
        ID of the newly created carrier
    """
    cursor = conn.execute("""
        INSERT INTO carriers (network_id, name, co2_emissions, color, nice_name)
        VALUES (?, ?, ?, ?, ?)
    """, (network_id, name, co2_emissions, color, nice_name))
    
    carrier_id = cursor.lastrowid
    if not carrier_id:
        raise DatabaseError("Failed to create carrier")
    
    return carrier_id


def list_carriers(conn: sqlite3.Connection, network_id: int) -> List[Dict[str, Any]]:
    """
    List all carriers for a network.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        List of carrier dictionaries
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, co2_emissions, color, nice_name
        FROM carriers 
        WHERE network_id = ? 
        ORDER BY name
    """, (network_id,))
    
    carriers = []
    for row in cursor.fetchall():
        carriers.append({
            "id": row[0],
            "network_id": row[1],
            "name": row[2],
            "co2_emissions": row[3],
            "color": row[4],
            "nice_name": row[5]
        })
    
    return carriers


def get_network_config(
    conn: sqlite3.Connection,
    network_id: int,
    scenario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get network configuration with scenario-aware fallback.
    
    Priority order:
    1. Scenario-specific config (network_config WHERE scenario_id = X)
    2. Network default config (network_config WHERE scenario_id IS NULL)
    3. Legacy column value (networks.unmet_load_active)
    4. System default value
    
    Args:
        conn: Database connection
        network_id: Network ID
        scenario_id: Optional scenario ID
        
    Returns:
        Dictionary with network configuration
    """
    config = {}
    
    # Load from network_config table with scenario fallback
    cursor = conn.execute("""
        SELECT param_name, param_type, param_value
        FROM network_config 
        WHERE network_id = ? AND (scenario_id = ? OR scenario_id IS NULL)
        ORDER BY scenario_id DESC NULLS LAST  -- Scenario-specific values first
    """, (network_id, scenario_id))
    
    seen_params = set()
    for row in cursor.fetchall():
        param_name, param_type, param_value = row
        
        # Skip if we already have this parameter (scenario-specific takes precedence)
        if param_name in seen_params:
            continue
        seen_params.add(param_name)
        
        # Parse value based on type
        try:
            if param_type == 'boolean':
                config[param_name] = param_value.lower() == 'true'
            elif param_type == 'real':
                config[param_name] = float(param_value)
            elif param_type == 'integer':
                config[param_name] = int(param_value)
            elif param_type == 'json':
                config[param_name] = json.loads(param_value)
            else:  # string
                config[param_name] = param_value
        except (ValueError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to parse config parameter {param_name}: {e}")
            continue
    
    # Fallback to legacy column for unmet_load_active if not in config table
    if 'unmet_load_active' not in config:
        cursor = conn.execute("SELECT unmet_load_active FROM networks WHERE id = ?", (network_id,))
        row = cursor.fetchone()
        if row and row[0] is not None:
            config['unmet_load_active'] = bool(row[0])
    
    # Apply system defaults for missing parameters
    defaults = {
        'unmet_load_active': True,
        'discount_rate': 0.0,  # No discounting by default
        'solver_name': 'default'
    }
    
    for param, default_value in defaults.items():
        if param not in config:
            config[param] = default_value
    
    return config


def set_network_config(
    conn: sqlite3.Connection,
    network_id: int,
    param_name: str,
    param_value: Any,
    param_type: str,
    scenario_id: Optional[int] = None,
    description: Optional[str] = None
) -> None:
    """
    Set network configuration parameter.
    
    Args:
        conn: Database connection
        network_id: Network ID
        param_name: Parameter name
        param_value: Parameter value
        param_type: Parameter type ('boolean', 'real', 'integer', 'string', 'json')
        scenario_id: Optional scenario ID
        description: Optional parameter description
        
    Raises:
        ValidationError: If parameter type is invalid or serialization fails
    """
    
    # Validate parameter type
    valid_types = {'boolean', 'real', 'integer', 'string', 'json'}
    if param_type not in valid_types:
        raise ValidationError(f"Invalid parameter type: {param_type}. Must be one of {valid_types}")
    
    # Serialize value based on type
    try:
        if param_type == 'boolean':
            serialized = str(param_value).lower()
            if serialized not in {'true', 'false'}:
                raise ValidationError(f"Boolean parameter must be True/False, got: {param_value}")
        elif param_type == 'real':
            serialized = str(float(param_value))
        elif param_type == 'integer':
            serialized = str(int(param_value))
        elif param_type == 'json':
            serialized = json.dumps(param_value)
        else:  # string
            serialized = str(param_value)
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Failed to serialize parameter {param_name} as {param_type}: {e}")
    
    # Insert or update parameter
    conn.execute("""
        INSERT OR REPLACE INTO network_config 
        (network_id, scenario_id, param_name, param_type, param_value, param_description, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
    """, (network_id, scenario_id, param_name, param_type, serialized, description))


def get_component_counts(conn: sqlite3.Connection, network_id: int) -> Dict[str, int]:
    """
    Get component counts by type for a network.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        Dictionary mapping component types to counts
    """
    cursor = conn.execute("""
        SELECT component_type, COUNT(*) FROM components 
        WHERE network_id = ? GROUP BY component_type
    """, (network_id,))
    
    counts = {}
    for row in cursor.fetchall():
        counts[row[0].lower()] = row[1]
    
    return counts


def get_master_scenario_id(conn: sqlite3.Connection, network_id: int) -> int:
    """Get the master scenario ID for a network"""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM scenarios WHERE network_id = ? AND is_master = TRUE",
        (network_id,)
    )
    result = cursor.fetchone()
    if not result:
        raise ValidationError(f"No master scenario found for network {network_id}")
    return result[0]


def resolve_scenario_id(conn: sqlite3.Connection, component_id: int, scenario_id: Optional[int]) -> int:
    """Resolve scenario ID - if None, get master scenario ID"""
    if scenario_id is not None:
        return scenario_id
    
    # Get network_id from component, then get master scenario
    cursor = conn.cursor()
    cursor.execute("SELECT network_id FROM components WHERE id = ?", (component_id,))
    result = cursor.fetchone()
    if not result:
        from pyconvexity.core.errors import ComponentNotFound
        raise ComponentNotFound(component_id)
    
    network_id = result[0]
    return get_master_scenario_id(conn, network_id)
