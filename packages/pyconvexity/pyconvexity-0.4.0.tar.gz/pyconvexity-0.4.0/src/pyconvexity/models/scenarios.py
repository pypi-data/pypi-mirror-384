"""
Scenario management operations for PyConvexity.

Provides operations for listing, querying, and managing scenarios.
"""

import sqlite3
import logging
from typing import List, Optional
from dataclasses import dataclass

from pyconvexity.core.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class Scenario:
    """Represents a scenario in the network."""
    id: int
    network_id: int
    name: str
    description: Optional[str]
    is_master: bool
    created_at: str


def list_scenarios(conn: sqlite3.Connection, network_id: int) -> List[Scenario]:
    """
    List all scenarios for a network.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        List of Scenario objects ordered by master first, then by creation date
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, description, is_master, created_at
        FROM scenarios
        WHERE network_id = ?
        ORDER BY is_master DESC, created_at
    """, (network_id,))
    
    scenarios = []
    for row in cursor.fetchall():
        scenarios.append(Scenario(
            id=row[0],
            network_id=row[1],
            name=row[2],
            description=row[3],
            is_master=bool(row[4]),
            created_at=row[5]
        ))
    
    return scenarios


def get_scenario_by_name(conn: sqlite3.Connection, network_id: int, name: str) -> Scenario:
    """
    Get a scenario by name.
    
    Args:
        conn: Database connection
        network_id: Network ID
        name: Scenario name
        
    Returns:
        Scenario object
        
    Raises:
        ValidationError: If scenario doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, description, is_master, created_at
        FROM scenarios
        WHERE network_id = ? AND name = ?
    """, (network_id, name))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"Scenario '{name}' not found for network {network_id}")
    
    return Scenario(
        id=row[0],
        network_id=row[1],
        name=row[2],
        description=row[3],
        is_master=bool(row[4]),
        created_at=row[5]
    )


def get_scenario_by_id(conn: sqlite3.Connection, scenario_id: int) -> Scenario:
    """
    Get a scenario by ID.
    
    Args:
        conn: Database connection
        scenario_id: Scenario ID
        
    Returns:
        Scenario object
        
    Raises:
        ValidationError: If scenario doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, description, is_master, created_at
        FROM scenarios
        WHERE id = ?
    """, (scenario_id,))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"Scenario with ID {scenario_id} not found")
    
    return Scenario(
        id=row[0],
        network_id=row[1],
        name=row[2],
        description=row[3],
        is_master=bool(row[4]),
        created_at=row[5]
    )


def get_master_scenario(conn: sqlite3.Connection, network_id: int) -> Scenario:
    """
    Get the master scenario for a network.
    
    Args:
        conn: Database connection
        network_id: Network ID
        
    Returns:
        Scenario object for the master scenario
        
    Raises:
        ValidationError: If master scenario doesn't exist
    """
    cursor = conn.execute("""
        SELECT id, network_id, name, description, is_master, created_at
        FROM scenarios
        WHERE network_id = ? AND is_master = TRUE
    """, (network_id,))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"No master scenario found for network {network_id}")
    
    return Scenario(
        id=row[0],
        network_id=row[1],
        name=row[2],
        description=row[3],
        is_master=bool(row[4]),
        created_at=row[5]
    )
