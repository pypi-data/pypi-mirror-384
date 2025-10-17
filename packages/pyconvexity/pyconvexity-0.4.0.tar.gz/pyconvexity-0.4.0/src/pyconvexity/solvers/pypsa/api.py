"""
High-level API for PyPSA solver integration.

Provides user-friendly functions for the most common workflows.
"""

import logging
from typing import Dict, Any, Optional, Callable

from pyconvexity.core.database import database_context
from pyconvexity.solvers.pypsa.builder import NetworkBuilder
from pyconvexity.solvers.pypsa.solver import NetworkSolver
from pyconvexity.solvers.pypsa.storage import ResultStorage
from pyconvexity.solvers.pypsa.constraints import ConstraintApplicator

logger = logging.getLogger(__name__)


def solve_network(
    db_path: str,
    network_id: int,
    scenario_id: Optional[int] = None,
    solver_name: str = "highs",
    solver_options: Optional[Dict[str, Any]] = None,
    constraints_dsl: Optional[str] = None,
    discount_rate: Optional[float] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    return_detailed_results: bool = True,
    custom_solver_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Complete solve workflow: build PyPSA network from database, solve, store results.
    
    This is the main high-level function that most users should use. It handles
    the complete workflow of loading data from database, building a PyPSA network,
    solving it, and storing results back to the database.
    
    Args:
        db_path: Path to the database file
        network_id: ID of the network to solve
        scenario_id: Optional scenario ID (uses master scenario if None)
        solver_name: Solver to use (default: "highs"). Use "custom" for custom_solver_config.
        solver_options: Optional solver-specific options
        constraints_dsl: Optional DSL constraints to apply
        discount_rate: Optional discount rate for multi-period optimization
        progress_callback: Optional callback for progress updates (progress: int, message: str)
        return_detailed_results: If True, return comprehensive results; if False, return simple status
        custom_solver_config: Optional custom solver configuration when solver_name="custom"
            Format: {"solver": "actual_solver_name", "solver_options": {...}}
            Example: {"solver": "gurobi", "solver_options": {"Method": 2, "Crossover": 0}}
        
    Returns:
        Dictionary with solve results - comprehensive if return_detailed_results=True, simple status otherwise
        
    Raises:
        DatabaseError: If database operations fail
        ValidationError: If network data is invalid
        ImportError: If PyPSA is not available
    """
    if progress_callback:
        progress_callback(0, "Starting network solve...")
    
    with database_context(db_path) as conn:
        # Load network configuration with scenario awareness (matches old code)
        from pyconvexity.models import get_network_config
        network_config = get_network_config(conn, network_id, scenario_id)
        if progress_callback:
            progress_callback(8, "Loaded network configuration")
        
        # Use configuration values with parameter overrides
        # Note: network_config already has default of 0.0 from get_network_config()
        effective_discount_rate = discount_rate if discount_rate is not None else network_config.get('discount_rate')
        logger.info(f"Using discount rate: {effective_discount_rate} (from {'parameter override' if discount_rate is not None else 'network config'})")
        
        # Build network
        if progress_callback:
            progress_callback(10, "Building PyPSA network...")
            
        builder = NetworkBuilder()
        network = builder.build_network(conn, network_id, scenario_id, progress_callback)
        
        if progress_callback:
            progress_callback(50, f"Network built: {len(network.buses)} buses, {len(network.generators)} generators")
        
        # Create constraint applicator and apply constraints BEFORE solve
        constraint_applicator = ConstraintApplicator()
        
        # Apply constraints before solving (network modifications like GlobalConstraints)
        if progress_callback:
            progress_callback(60, "Applying constraints...")
        
        constraint_applicator.apply_constraints(
            conn, network_id, network, scenario_id, constraints_dsl
        )
        
        # Solve network
        if progress_callback:
            progress_callback(70, f"Solving with {solver_name}...")
            
        solver = NetworkSolver()
        solve_result = solver.solve_network(
            network, 
            solver_name=solver_name,
            solver_options=solver_options,
            discount_rate=effective_discount_rate,  # Use effective discount rate from config
            conn=conn,
            network_id=network_id,
            scenario_id=scenario_id,
            constraint_applicator=constraint_applicator,
            custom_solver_config=custom_solver_config
        )
        
        if progress_callback:
            progress_callback(85, "Storing results...")
        
        # Store results - ALWAYS store results regardless of return_detailed_results flag
        storage = ResultStorage()
        storage_result = storage.store_results(
            conn, network_id, network, solve_result, scenario_id
        )
        
        if progress_callback:
            progress_callback(95, "Solve completed successfully")
        
        # Optimize database after successful solve (if solve was successful)
        if solve_result.get("success", False):
            try:
                if progress_callback:
                    progress_callback(98, "Optimizing database...")
                
                from pyconvexity.core.database import should_optimize_database, optimize_database
                
                # Only optimize if there's significant free space (>5% threshold for post-solve)
                if should_optimize_database(conn, free_space_threshold_percent=5.0):
                    logger.info("Running database optimization after successful solve")
                    optimization_result = optimize_database(conn)
                    logger.info(f"Database optimization completed: {optimization_result['space_reclaimed']:,} bytes reclaimed")
                else:
                    logger.debug("Skipping database optimization - insufficient free space")
                    
            except Exception as e:
                # Don't fail the solve if optimization fails
                logger.warning(f"Database optimization failed (non-critical): {e}")
        
        if progress_callback:
            progress_callback(100, "Complete")
        
        # Return simple status if requested (for sidecar/async usage)
        # Results are now stored in database regardless of this flag
        if not return_detailed_results:
            return {
                "success": solve_result.get("success", False),
                "message": "Solve completed successfully" if solve_result.get("success") else "Solve failed",
                "error": solve_result.get("error") if not solve_result.get("success") else None,
                "network_id": network_id,
                "scenario_id": scenario_id
            }
        
        # Combine results in comprehensive format for detailed analysis
        comprehensive_result = {
            **solve_result,
            "storage_stats": storage_result,
            "network_id": network_id,
            "scenario_id": scenario_id
        }
        
        # Transform to include sidecar-compatible format
        return _transform_to_comprehensive_format(comprehensive_result)


def build_pypsa_network(
    db_path: str,
    network_id: int,
    scenario_id: Optional[int] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> 'pypsa.Network':
    """
    Build PyPSA network object from database.
    
    This function loads all network data from the database and constructs
    a PyPSA Network object ready for solving or analysis. Useful when you
    want to inspect or modify the network before solving.
    
    Args:
        db_path: Path to the database file
        network_id: ID of the network to build
        scenario_id: Optional scenario ID (uses master scenario if None)
        progress_callback: Optional callback for progress updates
        
    Returns:
        PyPSA Network object ready for solving
        
    Raises:
        DatabaseError: If database operations fail
        ValidationError: If network data is invalid
        ImportError: If PyPSA is not available
    """
    with database_context(db_path) as conn:
        builder = NetworkBuilder()
        return builder.build_network(conn, network_id, scenario_id, progress_callback)


def solve_pypsa_network(
    network: 'pypsa.Network',
    db_path: str,
    network_id: int,
    scenario_id: Optional[int] = None,
    solver_name: str = "highs",
    solver_options: Optional[Dict[str, Any]] = None,
    discount_rate: Optional[float] = None,
    store_results: bool = True,
    progress_callback: Optional[Callable[[int, str], None]] = None,
    custom_solver_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Solve PyPSA network and optionally store results back to database.
    
    This function takes an existing PyPSA network (e.g., from build_pypsa_network),
    solves it, and optionally stores the results back to the database.
    
    Args:
        network: PyPSA Network object to solve
        db_path: Path to the database file (needed for result storage)
        network_id: ID of the network (for result storage)
        scenario_id: Optional scenario ID
        solver_name: Solver to use (default: "highs"). Use "custom" for custom_solver_config.
        solver_options: Optional solver-specific options
        discount_rate: Optional discount rate for multi-period optimization (default: 0.0)
        store_results: Whether to store results back to database (default: True)
        progress_callback: Optional callback for progress updates
        custom_solver_config: Optional custom solver configuration when solver_name="custom"
            Format: {"solver": "actual_solver_name", "solver_options": {...}}
        
    Returns:
        Dictionary with solve results and statistics
        
    Raises:
        DatabaseError: If database operations fail (when store_results=True)
        ImportError: If PyPSA is not available
    """
    if progress_callback:
        progress_callback(0, f"Solving network with {solver_name}...")
    
    # Solve network
    solver = NetworkSolver()
    solve_result = solver.solve_network(
        network,
        solver_name=solver_name,
        solver_options=solver_options,
        discount_rate=discount_rate,
        custom_solver_config=custom_solver_config
    )
    
    if progress_callback:
        progress_callback(70, "Solve completed")
    
    # Store results if requested
    if store_results:
        if progress_callback:
            progress_callback(80, "Storing results...")
            
        with database_context(db_path) as conn:
            storage = ResultStorage()
            storage_result = storage.store_results(
                conn, network_id, network, solve_result, scenario_id
            )
            solve_result["storage_stats"] = storage_result
    
    if progress_callback:
        progress_callback(100, "Complete")
    
    return solve_result


def load_network_components(
    db_path: str, 
    network_id: int, 
    scenario_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Load all network components and attributes as structured data.
    
    This low-level function loads network data without building a PyPSA network.
    Useful for analysis, validation, or building custom network representations.
    
    Args:
        db_path: Path to the database file
        network_id: ID of the network to load
        scenario_id: Optional scenario ID
        
    Returns:
        Dictionary containing all network components and metadata
        
    Raises:
        DatabaseError: If database operations fail
    """
    with database_context(db_path) as conn:
        builder = NetworkBuilder()
        return builder.load_network_data(conn, network_id, scenario_id)


def apply_constraints(
    network: 'pypsa.Network',
    db_path: str,
    network_id: int,
    scenario_id: Optional[int] = None,
    constraints_dsl: Optional[str] = None
) -> None:
    """
    Apply custom constraints to PyPSA network.
    
    This function applies database-stored constraints and optional DSL constraints
    to an existing PyPSA network. Modifies the network in-place.
    
    Args:
        network: PyPSA Network object to modify
        db_path: Path to the database file
        network_id: ID of the network
        scenario_id: Optional scenario ID
        constraints_dsl: Optional DSL constraints string
        
    Raises:
        DatabaseError: If database operations fail
        ValidationError: If constraints are invalid
    """
    with database_context(db_path) as conn:
        constraint_applicator = ConstraintApplicator()
        constraint_applicator.apply_constraints(
            conn, network_id, network, scenario_id, constraints_dsl
        )


def store_solve_results(
    network: 'pypsa.Network',
    db_path: str,
    network_id: int,
    scenario_id: Optional[int],
    solve_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store PyPSA solve results back to database.
    
    This low-level function stores solve results from a PyPSA network back
    to the database. Useful when you want full control over the solving process
    but still want to store results in the standard format.
    
    Args:
        network: Solved PyPSA Network object
        db_path: Path to the database file
        network_id: ID of the network
        scenario_id: Scenario ID for result storage
        solve_metadata: Dictionary with solve metadata (solver_name, solve_time, etc.)
        
    Returns:
        Dictionary with storage statistics
        
    Raises:
        DatabaseError: If database operations fail
    """
    with database_context(db_path) as conn:
        storage = ResultStorage()
        return storage.store_results(
            conn, network_id, network, solve_metadata, scenario_id
        )


def _transform_to_comprehensive_format(pyconvexity_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform pyconvexity result to comprehensive format that includes both
    the original structure and sidecar-compatible fields.
    
    This ensures compatibility with existing sidecar code while providing
    a clean API for direct pyconvexity users.
    
    Args:
        pyconvexity_result: Result from pyconvexity solve operations
        
    Returns:
        Comprehensive result with both original and sidecar-compatible fields
    """
    try:
        # Extract basic solve information
        success = pyconvexity_result.get("success", False)
        status = pyconvexity_result.get("status", "unknown")
        solve_time = pyconvexity_result.get("solve_time", 0.0)
        objective_value = pyconvexity_result.get("objective_value")
        
        # Extract storage stats
        storage_stats = pyconvexity_result.get("storage_stats", {})
        component_stats = storage_stats.get("component_stats", {})
        network_stats = storage_stats.get("network_stats", {})
        
        # Create comprehensive result that includes both formats
        comprehensive_result = {
            # Original pyconvexity format (for direct users)
            **pyconvexity_result,
            
            # Sidecar-compatible format (for backward compatibility)
            "network_statistics": {
                "total_generation_mwh": network_stats.get("total_generation_mwh", 0.0),
                "total_load_mwh": network_stats.get("total_load_mwh", 0.0),
                "unmet_load_mwh": network_stats.get("unmet_load_mwh", 0.0),
                "total_cost": network_stats.get("total_cost", objective_value or 0.0),
                "num_buses": network_stats.get("num_buses", 0),
                "num_generators": network_stats.get("num_generators", 0),
                "num_loads": network_stats.get("num_loads", 0),
                "num_lines": network_stats.get("num_lines", 0),
                "num_links": network_stats.get("num_links", 0)
            },
            
            "component_storage_stats": {
                "stored_bus_results": component_stats.get("stored_bus_results", 0),
                "stored_generator_results": component_stats.get("stored_generator_results", 0),
                "stored_unmet_load_results": component_stats.get("stored_unmet_load_results", 0),
                "stored_load_results": component_stats.get("stored_load_results", 0),
                "stored_line_results": component_stats.get("stored_line_results", 0),
                "stored_link_results": component_stats.get("stored_link_results", 0),
                "stored_storage_unit_results": component_stats.get("stored_storage_unit_results", 0),
                "stored_store_results": component_stats.get("stored_store_results", 0),
                "skipped_attributes": component_stats.get("skipped_attributes", 0),
                "errors": component_stats.get("errors", 0)
            },
            
            # Additional compatibility fields
            "multi_period": pyconvexity_result.get("multi_period", False),
            "years": pyconvexity_result.get("years", [])
        }
        
        return comprehensive_result
        
    except Exception as e:
        logger.error(f"Failed to transform result to comprehensive format: {e}", exc_info=True)
        # Return original result with error info if transformation fails
        return {
            **pyconvexity_result,
            "transformation_error": str(e),
            "network_statistics": {},
            "component_storage_stats": {}
        }
