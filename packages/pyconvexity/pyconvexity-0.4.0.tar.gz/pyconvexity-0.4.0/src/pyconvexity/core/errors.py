"""
Error classes for PyConvexity.

These mirror the error handling from the original Rust implementation
while providing Python-specific enhancements.
"""

from typing import Optional


class PyConvexityError(Exception):
    """Base exception for all PyConvexity errors"""
    pass


class DatabaseError(PyConvexityError):
    """Database-related errors"""
    pass


class ConnectionError(DatabaseError):
    """Database connection failed"""
    pass


class ValidationError(PyConvexityError):
    """Data validation error"""
    pass


class ComponentNotFound(PyConvexityError):
    """Component not found in database"""
    
    def __init__(self, component_id: int, message: Optional[str] = None):
        self.component_id = component_id
        if message is None:
            message = f"Component not found: {component_id}"
        super().__init__(message)


class AttributeNotFound(PyConvexityError):
    """Attribute not found for component"""
    
    def __init__(self, component_id: int, attribute_name: str, message: Optional[str] = None):
        self.component_id = component_id
        self.attribute_name = attribute_name
        if message is None:
            message = f"Attribute not found: component {component_id}, attribute '{attribute_name}'"
        super().__init__(message)


class InvalidDataType(ValidationError):
    """Invalid data type for attribute"""
    
    def __init__(self, expected: str, actual: str, message: Optional[str] = None):
        self.expected = expected
        self.actual = actual
        if message is None:
            message = f"Invalid data type: expected {expected}, got {actual}"
        super().__init__(message)


class TimeseriesError(PyConvexityError):
    """Timeseries serialization/deserialization error"""
    pass


class NetworkNotFound(PyConvexityError):
    """Network not found in database"""
    
    def __init__(self, network_id: int, message: Optional[str] = None):
        self.network_id = network_id
        if message is None:
            message = f"Network not found: {network_id}"
        super().__init__(message)


class ScenarioNotFound(PyConvexityError):
    """Scenario not found in database"""
    
    def __init__(self, scenario_id: int, message: Optional[str] = None):
        self.scenario_id = scenario_id
        if message is None:
            message = f"Scenario not found: {scenario_id}"
        super().__init__(message)


class CarrierNotFound(PyConvexityError):
    """Carrier not found in database"""
    
    def __init__(self, carrier_id: int, message: Optional[str] = None):
        self.carrier_id = carrier_id
        if message is None:
            message = f"Carrier not found: {carrier_id}"
        super().__init__(message)


# Legacy aliases for backward compatibility with existing code
# These will be deprecated in future versions
DbError = PyConvexityError
