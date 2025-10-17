"""
Results and statistics operations for PyConvexity.

Provides operations for querying solve results and statistics.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from pyconvexity.core.errors import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class SolveResults:
    """Represents solve results for a scenario."""
    network_statistics: Dict[str, Any]
    metadata: Dict[str, Any]
    status: str
    objective_value: Optional[float]
    solve_time: float


@dataclass
class YearlyResults:
    """Represents yearly solve results."""
    year: int
    network_statistics: Dict[str, Any]
    metadata: Dict[str, Any]


def get_solve_results(
    conn: sqlite3.Connection,
    network_id: int,
    scenario_id: Optional[int] = None
) -> Optional[SolveResults]:
    """
    Get overall solve results for a scenario.
    
    Args:
        conn: Database connection
        network_id: Network ID
        scenario_id: Scenario ID (uses master scenario if None)
        
    Returns:
        SolveResults object or None if no results found
    """
    # Resolve scenario ID if not provided
    if scenario_id is None:
        from pyconvexity.models.scenarios import get_master_scenario
        scenario = get_master_scenario(conn, network_id)
        scenario_id = scenario.id
    
    cursor = conn.execute("""
        SELECT results_json, metadata_json, solve_status, objective_value, solve_time_seconds
        FROM network_solve_results
        WHERE network_id = ? AND scenario_id = ?
        ORDER BY solved_at DESC
        LIMIT 1
    """, (network_id, scenario_id))
    
    row = cursor.fetchone()
    if not row:
        return None
    
    try:
        results_json = json.loads(row[0]) if row[0] else {}
        metadata_json = json.loads(row[1]) if row[1] else {}
        
        # Extract network_statistics from results_json
        network_statistics = results_json.get('network_statistics', {})
        
        return SolveResults(
            network_statistics=network_statistics,
            metadata=metadata_json,
            status=row[2] or 'unknown',
            objective_value=row[3],
            solve_time=row[4] or 0.0
        )
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON for scenario {scenario_id}: {e}")
        return None


def get_yearly_results(
    conn: sqlite3.Connection,
    network_id: int,
    scenario_id: Optional[int] = None
) -> Dict[int, YearlyResults]:
    """
    Get year-by-year solve results for a scenario.
    
    Args:
        conn: Database connection
        network_id: Network ID
        scenario_id: Scenario ID (uses master scenario if None)
        
    Returns:
        Dictionary mapping years to YearlyResults objects
    """
    # Resolve scenario ID if not provided
    if scenario_id is None:
        from pyconvexity.models.scenarios import get_master_scenario
        scenario = get_master_scenario(conn, network_id)
        scenario_id = scenario.id
    
    cursor = conn.execute("""
        SELECT year, results_json, metadata_json
        FROM network_solve_results_by_year
        WHERE network_id = ? AND scenario_id = ?
        ORDER BY year
    """, (network_id, scenario_id))
    
    yearly_results = {}
    for row in cursor.fetchall():
        year = row[0]
        try:
            results_json = json.loads(row[1]) if row[1] else {}
            metadata_json = json.loads(row[2]) if row[2] else {}
            
            # Extract network_statistics from results_json
            network_statistics = results_json.get('network_statistics', {})
            
            yearly_results[year] = YearlyResults(
                year=year,
                network_statistics=network_statistics,
                metadata=metadata_json
            )
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for year {year}: {e}")
            continue
    
    return yearly_results

