"""
Validation rules and operations for PyConvexity.

Provides validation logic for component attributes, data types, and timeseries alignment.
"""

import sqlite3
import json
import logging
from typing import Dict, Any, Optional, List

from pyconvexity.core.types import (
    ValidationRule, StaticValue, TimePeriod, TimeseriesValidationResult
)
from pyconvexity.core.errors import (
    ValidationError, InvalidDataType
)

logger = logging.getLogger(__name__)


def get_validation_rule(
    conn: sqlite3.Connection, 
    component_type: str, 
    attribute_name: str
) -> ValidationRule:
    """
    Get validation rule for a specific component type and attribute.
    
    Args:
        conn: Database connection
        component_type: Type of component (e.g., "BUS", "GENERATOR")
        attribute_name: Name of the attribute
        
    Returns:
        ValidationRule object with all validation information
        
    Raises:
        ValidationError: If no validation rule is found
    """
    cursor = conn.execute("""
        SELECT component_type, attribute_name, data_type, unit, default_value, allowed_storage_types, 
               is_required, is_input, description
        FROM attribute_validation_rules 
        WHERE component_type = ? AND attribute_name = ?
    """, (component_type, attribute_name))
    
    row = cursor.fetchone()
    if not row:
        raise ValidationError(f"No validation rule found for {component_type}.{attribute_name}")
    
    allowed_storage_types = row[5]
    allows_static = allowed_storage_types in ("static", "static_or_timeseries")
    allows_timeseries = allowed_storage_types in ("timeseries", "static_or_timeseries")
    
    # Parse default value
    default_value = None
    if row[4]:  # default_value_string
        default_value = parse_default_value(row[4])
    
    return ValidationRule(
        component_type=row[0],
        attribute_name=row[1],
        data_type=row[2],
        unit=row[3],
        default_value_string=row[4],
        allowed_storage_types=allowed_storage_types,
        allows_static=allows_static,
        allows_timeseries=allows_timeseries,
        is_required=bool(row[6]),
        is_input=bool(row[7]),
        description=row[8],
        default_value=default_value
    )


def list_validation_rules(
    conn: sqlite3.Connection,
    component_type: str
) -> List[ValidationRule]:
    """
    List validation rules for a component type.
    
    Args:
        conn: Database connection
        component_type: Type of component
        
    Returns:
        List of ValidationRule objects
    """
    cursor = conn.execute("""
        SELECT component_type, attribute_name, data_type, unit, default_value, allowed_storage_types, 
               is_required, is_input, description
        FROM attribute_validation_rules 
        WHERE component_type = ?
        ORDER BY attribute_name
    """, (component_type,))
    
    rules = []
    for row in cursor.fetchall():
        allowed_storage_types = row[5]
        allows_static = allowed_storage_types in ("static", "static_or_timeseries")
        allows_timeseries = allowed_storage_types in ("timeseries", "static_or_timeseries")
        
        # Parse default value
        default_value = None
        if row[4]:  # default_value_string
            default_value = parse_default_value(row[4])
        
        rules.append(ValidationRule(
            component_type=row[0],
            attribute_name=row[1],
            data_type=row[2],
            unit=row[3],
            default_value_string=row[4],
            allowed_storage_types=allowed_storage_types,
            allows_static=allows_static,
            allows_timeseries=allows_timeseries,
            is_required=bool(row[6]),
            is_input=bool(row[7]),
            description=row[8],
            default_value=default_value
        ))
    
    return rules


def get_all_validation_rules(conn: sqlite3.Connection) -> Dict[str, Any]:
    """
    Get all validation rules from the database.
    This replaces the need to load the entire JSON file into memory.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary mapping component types to their validation rules
    """
    try:
        cursor = conn.execute("""
            SELECT component_type, attribute_name, data_type, unit, default_value, allowed_storage_types, 
                   is_required, is_input, description
            FROM attribute_validation_rules 
        """)
        
        rules = {}
        for row in cursor.fetchall():
            component_type = row[0]
            attribute_name = row[1]
            data_type = row[2]
            unit = row[3]
            default_value = row[4]
            allowed_storage_types = row[5]
            is_required = bool(row[6])
            is_input = bool(row[7])
            description = row[8]
            
            if component_type not in rules:
                rules[component_type] = {}
            
            rules[component_type][attribute_name] = {
                'data_type': data_type,
                'unit': unit,
                'default_value': default_value,
                'allowed_storage_types': allowed_storage_types,
                'is_required': is_required,
                'is_input': is_input,
                'description': description
            }
        
        return rules
    except Exception as e:
        logger.error(f"Error getting all validation rules: {e}")
        return {}


def validate_static_value(value: StaticValue, rule: ValidationRule) -> None:
    """
    Validate static value against rule.
    
    Args:
        value: StaticValue to validate
        rule: ValidationRule to validate against
        
    Raises:
        InvalidDataType: If value type doesn't match rule
    """
    value_type = value.data_type()
    
    if value_type != rule.data_type:
        raise InvalidDataType(expected=rule.data_type, actual=value_type)


def validate_timeseries_alignment(
    conn: sqlite3.Connection,
    network_id: int,
    timeseries: List[float]
) -> TimeseriesValidationResult:
    """
    Validate timeseries alignment with network periods.
    
    Args:
        conn: Database connection
        network_id: Network ID
        timeseries: List of timeseries points to validate
        
    Returns:
        TimeseriesValidationResult with validation details
    """
    # Get network time periods
    from pyconvexity.models.network import get_network_time_periods
    network_periods = get_network_time_periods(conn, network_id)
    network_period_indices = {p.period_index for p in network_periods}
    
    # Get provided period indices
    provided_period_indices = {p.period_index for p in timeseries}
    
    # Find missing and extra periods
    missing_periods = list(network_period_indices - provided_period_indices)
    extra_periods = list(provided_period_indices - network_period_indices)
    
    is_valid = len(missing_periods) == 0 and len(extra_periods) == 0
    
    return TimeseriesValidationResult(
        is_valid=is_valid,
        missing_periods=missing_periods,
        extra_periods=extra_periods,
        total_network_periods=len(network_periods),
        provided_periods=len(timeseries)
    )


def parse_default_value(s: str) -> Optional[StaticValue]:
    """
    Parse default value string.
    
    Args:
        s: String representation of default value
        
    Returns:
        StaticValue object or None if parsing fails
    """
    # Try to parse as JSON first
    try:
        value = json.loads(s)
        if isinstance(value, float):
            return StaticValue(value)
        elif isinstance(value, int):
            return StaticValue(value)
        elif isinstance(value, bool):
            return StaticValue(value)
        elif isinstance(value, str):
            return StaticValue(value)
        else:
            return None
    except (json.JSONDecodeError, ValueError):
        # Fallback to string
        return StaticValue(s)


def get_attribute_setter_info(
    conn: sqlite3.Connection,
    component_type: str,
    attribute_name: str,
) -> Dict[str, Any]:
    """
    Get the appropriate function name for setting an attribute.
    
    Args:
        conn: Database connection
        component_type: Type of component
        attribute_name: Name of the attribute
        
    Returns:
        Dictionary with setter function information
        
    Raises:
        ValidationError: If attribute or data type is unknown
    """
    rule = get_validation_rule(conn, component_type, attribute_name)
    
    function_name = {
        "float": "set_float_attribute",
        "int": "set_integer_attribute", 
        "boolean": "set_boolean_attribute",
        "string": "set_string_attribute",
    }.get(rule.data_type)
    
    if not function_name:
        raise ValidationError(f"Unknown data type: {rule.data_type}")
    
    return {
        "function_name": function_name,
        "data_type": rule.data_type,
        "allows_static": rule.allows_static,
        "allows_timeseries": rule.allows_timeseries,
        "is_required": rule.is_required,
        "default_value": rule.default_value_string,
        "unit": rule.unit,
        "description": rule.description
    }
