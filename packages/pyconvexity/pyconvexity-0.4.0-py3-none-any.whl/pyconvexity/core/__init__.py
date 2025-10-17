"""
Core module for PyConvexity.

Contains fundamental types, database operations, and error handling.
"""

from pyconvexity.core.errors import (
    PyConvexityError,
    DatabaseError,
    ValidationError,
    ComponentNotFound,
    AttributeNotFound,
    InvalidDataType,
    TimeseriesError,
)

from pyconvexity.core.types import (
    StaticValue,
    AttributeValue,
    ValidationRule,
    Component,
    Network,
    TimePeriod,
    TimeseriesValidationResult,
    CreateComponentRequest,
    CreateNetworkRequest,
)

from pyconvexity.core.database import (
    DatabaseContext,
    open_connection,
    validate_database,
    create_database_with_schema,
)

__all__ = [
    # Errors
    "PyConvexityError",
    "DatabaseError", 
    "ValidationError",
    "ComponentNotFound",
    "AttributeNotFound",
    "InvalidDataType",
    "TimeseriesError",
    
    # Types
    "StaticValue",
    "AttributeValue", 
    "ValidationRule",
    "Component",
    "Network",
    "TimePeriod",
    "TimeseriesValidationResult",
    "CreateComponentRequest",
    "CreateNetworkRequest",
    
    # Database
    "DatabaseContext",
    "open_connection",
    "validate_database", 
    "create_database_with_schema",
]
