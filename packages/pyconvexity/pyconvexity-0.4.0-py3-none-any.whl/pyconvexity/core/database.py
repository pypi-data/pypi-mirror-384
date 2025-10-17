"""
Database connection and schema management for PyConvexity.

Provides clean abstractions for database operations with proper connection
management, schema validation, and resource cleanup.
"""

import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

from pyconvexity.core.errors import ConnectionError, DatabaseError, ValidationError


class DatabaseContext:
    """
    Context manager for database connections with automatic cleanup.
    
    Provides a clean way to manage database connections with proper
    resource cleanup and error handling.
    """
    
    def __init__(self, db_path: str, read_only: bool = False):
        self.db_path = db_path
        self.read_only = read_only
        self.connection: Optional[sqlite3.Connection] = None
    
    def __enter__(self) -> sqlite3.Connection:
        self.connection = open_connection(self.db_path, read_only=self.read_only)
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is None:
                # No exception, commit any pending changes
                self.connection.commit()
            else:
                # Exception occurred, rollback
                self.connection.rollback()
            self.connection.close()
            self.connection = None


@contextmanager
def database_context(db_path: str, read_only: bool = False) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager function for database connections.
    
    Args:
        db_path: Path to the SQLite database file
        read_only: If True, open in read-only mode
        
    Yields:
        sqlite3.Connection: Database connection with proper configuration
        
    Example:
        with database_context("model.db") as conn:
            cursor = conn.execute("SELECT * FROM networks")
            networks = cursor.fetchall()
    """
    with DatabaseContext(db_path, read_only) as conn:
        yield conn


def open_connection(db_path: str, read_only: bool = False) -> sqlite3.Connection:
    """
    Open database connection with proper settings.
    
    Args:
        db_path: Path to the SQLite database file
        read_only: If True, open in read-only mode
        
    Returns:
        sqlite3.Connection: Configured database connection
        
    Raises:
        ConnectionError: If database connection fails
    """
    try:
        # Build connection URI for read-only mode if needed
        if read_only:
            uri = f"file:{db_path}?mode=ro"
            conn = sqlite3.connect(uri, uri=True)
        else:
            conn = sqlite3.connect(db_path)
        
        # Configure connection
        conn.row_factory = sqlite3.Row  # Enable column access by name
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        
        # Configure for concurrent access (WAL mode for better concurrency)
        if not read_only:
            conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging for concurrency
            conn.execute("PRAGMA synchronous = NORMAL")  # Faster than FULL, still safe
            conn.execute("PRAGMA wal_autocheckpoint = 1000")  # Less frequent checkpoints
            conn.execute("PRAGMA temp_store = MEMORY")  # Faster temporary operations
        
        # Set reasonable timeouts
        conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
        
        return conn
        
    except sqlite3.Error as e:
        raise ConnectionError(f"Failed to open database at {db_path}: {e}") from e


def validate_database(conn: sqlite3.Connection) -> None:
    """
    Validate database schema has required tables.
    
    Args:
        conn: Database connection to validate
        
    Raises:
        ValidationError: If required tables are missing
    """
    required_tables = [
        "networks",
        "components", 
        "component_attributes",
        "attribute_validation_rules",
        "carriers",
        "scenarios"
    ]
    
    missing_tables = []
    
    for table in required_tables:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", 
            (table,)
        )
        if not cursor.fetchone():
            missing_tables.append(table)
    
    if missing_tables:
        raise ValidationError(
            f"Required tables not found in database: {', '.join(missing_tables)}"
        )


def create_database_with_schema(db_path: str) -> None:
    """
    Create a new database and apply the complete schema.
    
    Args:
        db_path: Path where the new database should be created
        
    Raises:
        DatabaseError: If schema files cannot be found or applied
    """
    db_path_obj = Path(db_path)
    
    # Ensure parent directory exists
    if db_path_obj.parent and not db_path_obj.parent.exists():
        db_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
    # Remove existing file if it exists, to ensure a clean start
    if db_path_obj.exists():
        db_path_obj.unlink()
    
    # Find schema files
    schema_dir = _find_schema_directory()
    if not schema_dir:
        raise DatabaseError("Could not find schema directory")
    
    schema_files = [
        "01_core_schema.sql",
        "02_data_metadata.sql", 
        "03_validation_data.sql",
        "04_scenario_schema.sql"
    ]
    
    # Verify all schema files exist
    missing_files = []
    for filename in schema_files:
        schema_file = schema_dir / filename
        if not schema_file.exists():
            missing_files.append(filename)
    
    if missing_files:
        raise DatabaseError(f"Schema files not found: {', '.join(missing_files)}")
    
    # Create connection and apply schemas
    try:
        conn = sqlite3.connect(db_path)
        
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Configure for concurrent access
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA wal_autocheckpoint = 1000")
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA busy_timeout = 30000")
        
        # Execute schemas in order
        for filename in schema_files:
            schema_file = schema_dir / filename
            with open(schema_file, 'r') as f:
                conn.executescript(f.read())
        
        conn.close()
        
    except sqlite3.Error as e:
        # Clean up partial database on error
        if db_path_obj.exists():
            db_path_obj.unlink()
        raise DatabaseError(f"Failed to create database schema: {e}") from e


def _find_schema_directory() -> Optional[Path]:
    """
    Find the schema directory in various possible locations.
    
    Returns:
        Path to schema directory or None if not found
    """   # Try package data location first (PyPI/pip install)
    try:
        import importlib.resources
        schema_path = importlib.resources.files('pyconvexity') / 'data' / 'schema'
        if schema_path.is_dir():
            return Path(str(schema_path))
    except (ImportError, AttributeError):
        pass
    
    # Try relative to this file (development mode)
    current_file = Path(__file__)
    
    # Look for schema in the package data directory
    # pyconvexity/src/pyconvexity/core/database.py -> pyconvexity/src/pyconvexity/data/schema
    package_schema_dir = current_file.parent.parent / "data" / "schema"
    if package_schema_dir.exists():
        return package_schema_dir
    
    # Look for schema in the main project (development mode)
    # Assuming pyconvexity/src/pyconvexity/core/database.py
    # and schema is at project_root/schema
    project_root = current_file.parent.parent.parent.parent.parent
    dev_schema_dir = project_root / "schema"
    if dev_schema_dir.exists():
        return dev_schema_dir
    
    # Try bundled location (PyInstaller)
    for p in sys.path:
        candidate = Path(p) / "schema"
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    return None


def get_database_info(conn: sqlite3.Connection) -> dict:
    """
    Get information about the database structure and contents.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with database information
    """
    info = {
        "tables": [],
        "networks": 0,
        "components": 0,
        "attributes": 0,
        "scenarios": 0,
        "carriers": 0
    }
    
    # Get table list
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    info["tables"] = [row[0] for row in cursor.fetchall()]
    
    # Get counts for main entities
    count_queries = {
        "networks": "SELECT COUNT(*) FROM networks",
        "components": "SELECT COUNT(*) FROM components", 
        "attributes": "SELECT COUNT(*) FROM component_attributes",
        "scenarios": "SELECT COUNT(*) FROM scenarios",
        "carriers": "SELECT COUNT(*) FROM carriers"
    }
    
    for key, query in count_queries.items():
        try:
            cursor = conn.execute(query)
            info[key] = cursor.fetchone()[0]
        except sqlite3.Error:
            # Table might not exist
            info[key] = 0
    
    return info


def check_database_compatibility(conn: sqlite3.Connection) -> dict:
    """
    Check if database is compatible with current PyConvexity version.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with compatibility information
    """
    result = {
        "compatible": True,
        "version": None,
        "issues": [],
        "warnings": []
    }
    
    try:
        validate_database(conn)
    except ValidationError as e:
        result["compatible"] = False
        result["issues"].append(str(e))
    
    # Check for version information (if we add a version table later)
    try:
        cursor = conn.execute("SELECT version FROM database_version LIMIT 1")
        row = cursor.fetchone()
        if row:
            result["version"] = row[0]
    except sqlite3.Error:
        result["warnings"].append("No version information found in database")
    
    return result


# ============================================================================
# DATABASE MAINTENANCE FUNCTIONS
# ============================================================================

def vacuum_database(conn: sqlite3.Connection) -> None:
    """
    Run VACUUM to reclaim database space and defragment.
    
    VACUUM rebuilds the database file, repacking it into a minimal amount of disk space.
    This is useful after deleting large amounts of data or after many INSERT/UPDATE/DELETE operations.
    
    Args:
        conn: Database connection
        
    Note:
        VACUUM can take a significant amount of time on large databases and requires
        temporary disk space up to twice the size of the original database.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Running VACUUM to reclaim database space and defragment")
    conn.execute("VACUUM")
    logger.info("VACUUM completed successfully")


def analyze_database(conn: sqlite3.Connection) -> None:
    """
    Run ANALYZE to update query planner statistics.
    
    ANALYZE gathers statistics about the contents of tables and indices.
    These statistics are used by the query planner to help make better choices about how to perform queries.
    
    Args:
        conn: Database connection
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("Running ANALYZE to update query planner statistics")
    conn.execute("ANALYZE")
    logger.info("ANALYZE completed successfully")


def optimize_database(conn: sqlite3.Connection) -> dict:
    """
    Run complete database optimization (VACUUM + ANALYZE).
    
    This performs both VACUUM and ANALYZE operations in the correct order:
    1. VACUUM first to reclaim space and defragment
    2. ANALYZE to update statistics with the new layout
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with optimization results including before/after size information
    """
    import logging
    import time
    logger = logging.getLogger(__name__)
    
    logger.info("Running database optimization (VACUUM + ANALYZE)")
    start_time = time.time()
    
    # Get size before optimization
    size_before = get_database_size_info(conn)
    
    # VACUUM first to reclaim space and defragment
    vacuum_database(conn)
    
    # Then ANALYZE to update statistics with the new layout
    analyze_database(conn)
    
    # Get size after optimization
    size_after = get_database_size_info(conn)
    
    optimization_time = time.time() - start_time
    
    result = {
        "success": True,
        "optimization_time": optimization_time,
        "size_before": size_before,
        "size_after": size_after,
        "space_reclaimed": size_before["total_size"] - size_after["total_size"],
        "free_pages_reclaimed": size_before["free_pages"] - size_after["free_pages"]
    }
    
    logger.info(f"Database optimization completed in {optimization_time:.2f} seconds")
    logger.info(f"Space reclaimed: {result['space_reclaimed']:,} bytes ({result['space_reclaimed']/1024/1024:.1f} MB)")
    
    return result


def get_database_size_info(conn: sqlite3.Connection) -> dict:
    """
    Get detailed information about database size and space usage.
    
    Args:
        conn: Database connection
        
    Returns:
        Dictionary with size information including total, used, and free space
    """
    # Get page count, page size, and freelist count
    page_count = conn.execute("PRAGMA page_count").fetchone()[0]
    page_size = conn.execute("PRAGMA page_size").fetchone()[0]
    freelist_count = conn.execute("PRAGMA freelist_count").fetchone()[0]
    
    total_size = page_count * page_size
    free_size = freelist_count * page_size
    used_size = total_size - free_size
    
    return {
        "total_size": total_size,
        "used_size": used_size,
        "free_size": free_size,
        "page_count": page_count,
        "page_size": page_size,
        "free_pages": freelist_count,
        "utilization_percent": (used_size / total_size * 100) if total_size > 0 else 0
    }


def should_optimize_database(conn: sqlite3.Connection, free_space_threshold_percent: float = 10.0) -> bool:
    """
    Check if database would benefit from optimization based on free space.
    
    Args:
        conn: Database connection
        free_space_threshold_percent: Threshold percentage of free space to trigger optimization
        
    Returns:
        True if optimization is recommended, False otherwise
    """
    size_info = get_database_size_info(conn)
    
    if size_info["total_size"] == 0:
        return False
    
    free_space_percent = (size_info["free_size"] / size_info["total_size"]) * 100
    return free_space_percent >= free_space_threshold_percent
