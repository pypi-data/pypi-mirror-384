"""
Carrier management operations for PyConvexity.

Provides operations for querying carriers and their properties.
"""

import sqlite3
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from pyconvexity.core.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class Carrier:
    """Represents an energy carrier in the network."""
    id: int
    network_id: int
    name: str
    co2_emissions: float
    color: Optional[str]
    nice_name: Optional[str]


def list_carriers(conn: sqlite3.Connection, network_id: int) -> List[Carrier]:
    """
    List all carriers for a network.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        List of Carrier objects ordered by name
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, co2_emissions, color, nice_name
        FROM carriers
        WHERE network_id = ?
        ORDER BY name
    """, (network_id,))
    
    carriers = []
    for row in cursor.fetchall():
        carriers.append(Carrier(
            id=row[0],
            network_id=row[1],
            name=row[2],
            co2_emissions=row[3] or 0.0,
            color=row[4],
            nice_name=row[5]
        ))
    
    return carriers


def get_carrier_by_name(conn: sqlite3.Connection, network_id: int, name: str) -> Carrier:
    """
    Get a carrier by name.
    
    Args:
        conn: Database connection
        network_id: Network ID
        name: Carrier name
        
    Returns:
        Carrier object
        
    Raises:
        ValidationError: If carrier doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, co2_emissions, color, nice_name
        FROM carriers
        WHERE network_id = ? AND name = ?
    """, (network_id, name))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"Carrier '{name}' not found for network {network_id}")
    
    return Carrier(
        id=row[0],
        network_id=row[1],
        name=row[2],
        co2_emissions=row[3] or 0.0,
        color=row[4],
        nice_name=row[5]
    )


def get_carrier_by_id(conn: sqlite3.Connection, carrier_id: int) -> Carrier:
    """
    Get a carrier by ID.
    
    Args:
        conn: Database connection
        carrier_id: Carrier ID
        
    Returns:
        Carrier object
        
    Raises:
        ValidationError: If carrier doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, co2_emissions, color, nice_name
        FROM carriers
        WHERE id = ?
    """, (carrier_id,))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"Carrier with ID {carrier_id} not found")
    
    return Carrier(
        id=row[0],
        network_id=row[1],
        name=row[2],
        co2_emissions=row[3] or 0.0,
        color=row[4],
        nice_name=row[5]
    )


def get_carrier_colors(conn: sqlite3.Connection, network_id: int) -> Dict[str, str]:
    """
    Get carrier colors for visualization.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        Dictionary mapping carrier names to color strings
    """
    cursor = conn.execute("""
        SELECT name, color
        FROM carriers
        WHERE network_id = ?
    """, (network_id,))
    
    colors = {}
    for row in cursor.fetchall():
        if row[1]:  # Only include if color is defined
            colors[row[0]] = row[1]
    
    # Add default color for Unmet Load if not present
    if 'Unmet Load' not in colors:
        colors['Unmet Load'] = '#FF0000'
    
    return colors

