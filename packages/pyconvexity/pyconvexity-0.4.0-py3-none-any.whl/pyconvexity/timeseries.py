"""
High-level timeseries API for PyConvexity.

This module provides the main interface for working with timeseries data,
matching the efficient patterns used in the Rust implementation.

Key Features:
- Ultra-fast binary serialization (matches Rust exactly)
- Array-based data structures for maximum performance
- Unified API for getting/setting timeseries data
- Backward compatibility with legacy point-based format
- Efficient sampling and filtering operations
"""

import sqlite3
from typing import List, Optional, Union
import numpy as np

from pyconvexity.core.database import database_context
from pyconvexity.core.types import Timeseries, TimeseriesMetadata
from pyconvexity.models.attributes import (
    get_timeseries as _get_timeseries,
    get_timeseries_metadata as _get_timeseries_metadata,
    set_timeseries_attribute,
    serialize_values_to_binary,
    deserialize_values_from_binary,
    get_timeseries_length_from_binary
)


# ============================================================================
# HIGH-LEVEL TIMESERIES API
# ============================================================================

def get_timeseries(
    db_path: str,
    component_id: int,
    attribute_name: str,
    scenario_id: Optional[int] = None,
    start_index: Optional[int] = None,
    end_index: Optional[int] = None,
    max_points: Optional[int] = None
) -> Timeseries:
    """
    Get timeseries data with efficient array-based format.
    
    This is the main function for retrieving timeseries data. It returns
    a Timeseries object with values as a flat array for maximum performance.
    
    Args:
        db_path: Path to the database file
        component_id: Component ID
        attribute_name: Name of the attribute (e.g., 'p', 'p_set', 'marginal_cost')
        scenario_id: Scenario ID (uses master scenario if None)
        start_index: Start index for range queries (optional)
        end_index: End index for range queries (optional)
        max_points: Maximum number of points for sampling (optional)
        
    Returns:
        Timeseries object with efficient array-based data
        
    Example:
        >>> ts = get_timeseries("model.db", component_id=123, attribute_name="p")
        >>> print(f"Length: {ts.length}, Values: {ts.values[:5]}")
        Length: 8760, Values: [100.5, 95.2, 87.3, 92.1, 88.7]
        
        # Get a subset of the data
        >>> ts_subset = get_timeseries("model.db", 123, "p", start_index=100, end_index=200)
        >>> print(f"Subset length: {ts_subset.length}")
        Subset length: 100
        
        # Sample large datasets
        >>> ts_sampled = get_timeseries("model.db", 123, "p", max_points=1000)
        >>> print(f"Sampled from {ts.length} to {ts_sampled.length} points")
    """
    with database_context(db_path, read_only=True) as conn:
        return _get_timeseries(
            conn, component_id, attribute_name, scenario_id,
            start_index, end_index, max_points
        )


def get_timeseries_metadata(
    db_path: str,
    component_id: int,
    attribute_name: str,
    scenario_id: Optional[int] = None
) -> TimeseriesMetadata:
    """
    Get timeseries metadata without loading the full data.
    
    This is useful for checking the size and properties of a timeseries
    before deciding whether to load the full data.
    
    Args:
        db_path: Path to the database file
        component_id: Component ID
        attribute_name: Name of the attribute
        scenario_id: Scenario ID (uses master scenario if None)
        
    Returns:
        TimeseriesMetadata with length and type information
        
    Example:
        >>> meta = get_timeseries_metadata("model.db", 123, "p")
        >>> print(f"Length: {meta.length}, Type: {meta.data_type}, Unit: {meta.unit}")
        Length: 8760, Type: float, Unit: MW
    """
    with database_context(db_path, read_only=True) as conn:
        return _get_timeseries_metadata(conn, component_id, attribute_name, scenario_id)


def set_timeseries(
    db_path: str,
    component_id: int,
    attribute_name: str,
    values: Union[List[float], np.ndarray, Timeseries],
    scenario_id: Optional[int] = None
) -> None:
    """
    Set timeseries data using efficient array-based format.
    
    This is the main function for storing timeseries data. It accepts
    various input formats and stores them efficiently in the database.
    
    Args:
        db_path: Path to the database file
        component_id: Component ID
        attribute_name: Name of the attribute
        values: Timeseries values as list, numpy array, or Timeseries object
        scenario_id: Scenario ID (uses master scenario if None)
        
    Example:
        # Set from a list
        >>> values = [100.5, 95.2, 87.3, 92.1, 88.7]
        >>> set_timeseries("model.db", 123, "p_set", values)
        
        # Set from numpy array
        >>> import numpy as np
        >>> values = np.random.normal(100, 10, 8760)  # Hourly data for a year
        >>> set_timeseries("model.db", 123, "p_max_pu", values)
        
        # Set from existing Timeseries object
        >>> ts = get_timeseries("model.db", 456, "p")
        >>> set_timeseries("model.db", 123, "p_set", ts)
    """
    # Convert input to list of floats
    if isinstance(values, Timeseries):
        values_list = values.values
    elif isinstance(values, np.ndarray):
        values_list = values.tolist()
    elif isinstance(values, list):
        values_list = [float(v) for v in values]
    else:
        raise ValueError("values must be List[float], numpy.ndarray, or Timeseries")
    
    with database_context(db_path) as conn:
        set_timeseries_attribute(conn, component_id, attribute_name, values_list, scenario_id)


def get_multiple_timeseries(
    db_path: str,
    requests: List[dict],
    max_points: Optional[int] = None
) -> List[Timeseries]:
    """
    Get multiple timeseries efficiently in a single database connection.
    
    This is more efficient than calling get_timeseries multiple times
    when you need to load many timeseries from the same database.
    
    Args:
        db_path: Path to the database file
        requests: List of dicts with keys: component_id, attribute_name, scenario_id (optional)
        max_points: Maximum number of points for sampling (applied to all)
        
    Returns:
        List of Timeseries objects in the same order as requests
        
    Example:
        >>> requests = [
        ...     {"component_id": 123, "attribute_name": "p"},
        ...     {"component_id": 124, "attribute_name": "p"},
        ...     {"component_id": 125, "attribute_name": "p", "scenario_id": 2}
        ... ]
        >>> timeseries_list = get_multiple_timeseries("model.db", requests)
        >>> print(f"Loaded {len(timeseries_list)} timeseries")
    """
    results = []
    
    with database_context(db_path, read_only=True) as conn:
        for request in requests:
            component_id = request["component_id"]
            attribute_name = request["attribute_name"]
            scenario_id = request.get("scenario_id")
            
            ts = _get_timeseries(
                conn, component_id, attribute_name, scenario_id,
                None, None, max_points
            )
            results.append(ts)
    
    return results


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def timeseries_to_numpy(timeseries: Timeseries) -> np.ndarray:
    """
    Convert Timeseries to numpy array for scientific computing.
    
    Args:
        timeseries: Timeseries object
        
    Returns:
        numpy array with float32 dtype for memory efficiency
        
    Example:
        >>> ts = get_timeseries("model.db", 123, "p")
        >>> arr = timeseries_to_numpy(ts)
        >>> print(f"Mean: {arr.mean():.2f}, Std: {arr.std():.2f}")
    """
    return np.array(timeseries.values, dtype=np.float32)


def numpy_to_timeseries(
    array: np.ndarray,
    data_type: str = "float",
    unit: Optional[str] = None,
    is_input: bool = True
) -> Timeseries:
    """
    Convert numpy array to Timeseries object.
    
    Args:
        array: numpy array of values
        data_type: Data type string (default: "float")
        unit: Unit string (optional)
        is_input: Whether this is input data (default: True)
        
    Returns:
        Timeseries object
        
    Example:
        >>> import numpy as np
        >>> arr = np.random.normal(100, 10, 8760)
        >>> ts = numpy_to_timeseries(arr, unit="MW")
        >>> print(f"Created timeseries with {ts.length} points")
    """
    values = array.tolist() if hasattr(array, 'tolist') else list(array)
    return Timeseries(
        values=[float(v) for v in values],
        length=len(values),
        start_index=0,
        data_type=data_type,
        unit=unit,
        is_input=is_input
    )


def validate_timeseries_alignment(
    db_path: str,
    network_id: int,
    values: Union[List[float], np.ndarray, Timeseries]
) -> dict:
    """
    Validate that timeseries data aligns with network time periods.
    
    Args:
        db_path: Path to the database file
        network_id: Network ID
        values: Timeseries values to validate
        
    Returns:
        Dictionary with validation results
        
    Example:
        >>> values = [100.0] * 8760  # Hourly data for a year
        >>> result = validate_timeseries_alignment("model.db", 1, values)
        >>> if result["is_valid"]:
        ...     print("Timeseries is properly aligned")
        ... else:
        ...     print(f"Alignment issues: {result['issues']}")
    """
    # Convert to list of floats
    if isinstance(values, Timeseries):
        values_list = values.values
    elif isinstance(values, np.ndarray):
        values_list = values.tolist()
    elif isinstance(values, list):
        values_list = [float(v) for v in values]
    else:
        raise ValueError("values must be List[float], numpy.ndarray, or Timeseries")
    
    with database_context(db_path, read_only=True) as conn:
        # Get network time periods
        from pyconvexity.models.network import get_network_time_periods
        try:
            time_periods = get_network_time_periods(conn, network_id)
            expected_length = len(time_periods)
            actual_length = len(values_list)
            
            is_valid = actual_length == expected_length
            issues = []
            
            if actual_length < expected_length:
                issues.append(f"Missing {expected_length - actual_length} time periods")
            elif actual_length > expected_length:
                issues.append(f"Extra {actual_length - expected_length} time periods")
            
            return {
                "is_valid": is_valid,
                "expected_length": expected_length,
                "actual_length": actual_length,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "is_valid": False,
                "expected_length": 0,
                "actual_length": len(values_list),
                "issues": [f"Failed to get network time periods: {e}"]
            }

