"""
Solving functionality for PyPSA networks.

Simplified to always use multi-period optimization for consistency.
"""

import logging
import time
import uuid
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NetworkSolver:
    """
    Simplified PyPSA network solver that always uses multi-period optimization.
    
    This ensures consistent behavior for both single-year and multi-year models.
    """
    
    def __init__(self):
        # Import PyPSA with error handling
        try:
            import pypsa
            self.pypsa = pypsa
        except ImportError as e:
            raise ImportError(
                "PyPSA is not installed or could not be imported. "
                "Please ensure it is installed correctly in the environment."
            ) from e
    
    def _get_user_settings_path(self):
        """Get the path to the user settings file (same location as Tauri uses)"""
        try:
            import platform
            import os
            from pathlib import Path
            
            system = platform.system()
            if system == "Darwin":  # macOS
                home = Path.home()
                app_data_dir = home / "Library" / "Application Support" / "com.convexity.desktop"
            elif system == "Windows":
                app_data_dir = Path(os.environ.get("APPDATA", "")) / "com.convexity.desktop"
            else:  # Linux
                home = Path.home()
                app_data_dir = home / ".local" / "share" / "com.convexity.desktop"
            
            settings_file = app_data_dir / "user_settings.json"
            return settings_file if settings_file.exists() else None
            
        except Exception as e:
            logger.warning(f"Failed to determine user settings path: {e}")
            return None
    
    def _resolve_default_solver(self) -> str:
        """Resolve 'default' solver to user's preferred solver"""
        try:
            import json
            
            settings_path = self._get_user_settings_path()
            if not settings_path:
                logger.debug("User settings file not found, using 'highs' as default solver")
                return 'highs'
            
            with open(settings_path, 'r') as f:
                user_settings = json.load(f)
            
            # Get default solver from user settings
            default_solver = user_settings.get('default_solver', 'highs')
            logger.info(f"📖 Read default solver from user settings: {default_solver}")
            
            # Validate that it's a known solver
            known_solvers = ['highs', 'gurobi', 'gurobi (barrier)', 'gurobi (barrier homogeneous)', 
                           'gurobi (barrier+crossover balanced)', 'gurobi (dual simplex)', 
                           'mosek', 'mosek (default)', 'mosek (barrier)', 'mosek (barrier+crossover)', 'mosek (dual simplex)',
                           'copt', 'copt (barrier)', 'copt (barrier homogeneous)', 'copt (barrier+crossover)', 
                           'copt (dual simplex)', 'copt (concurrent)',
                           'cplex', 'glpk', 'cbc', 'scip']
            
            if default_solver in known_solvers:
                return default_solver
            else:
                logger.warning(f"Unknown default solver '{default_solver}' in user settings, falling back to 'highs'")
                return 'highs'
                
        except Exception as e:
            logger.warning(f"Failed to read default solver from user settings: {e}")
            return 'highs'
    
    def solve_network(
        self,
        network: 'pypsa.Network',
        solver_name: str = "highs",
        solver_options: Optional[Dict[str, Any]] = None,
        discount_rate: Optional[float] = None,
        job_id: Optional[str] = None,
        conn=None,
        network_id: Optional[int] = None,
        scenario_id: Optional[int] = None,
        constraint_applicator=None,
        custom_solver_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solve PyPSA network and return results.
        
        Args:
            network: PyPSA Network object to solve
            solver_name: Solver to use (default: "highs"). Use "custom" for custom_solver_config.
            solver_options: Optional solver-specific options
            discount_rate: Optional discount rate for multi-period optimization
            job_id: Optional job ID for tracking
            custom_solver_config: Optional custom solver configuration when solver_name="custom"
                Format: {"solver": "actual_solver_name", "solver_options": {...}}
                Example: {"solver": "gurobi", "solver_options": {"Method": 2, "Crossover": 0}}
            
        Returns:
            Dictionary with solve results and metadata
            
        Raises:
            ImportError: If PyPSA is not available
            Exception: If solving fails
        """
        start_time = time.time()
        run_id = str(uuid.uuid4())
        
        logger.info(f"Starting network solve with {solver_name}")
        
        try:
            # Get solver configuration
            actual_solver_name, solver_config = self._get_solver_config(solver_name, solver_options, custom_solver_config)
            
            # Resolve discount rate - fallback to 0.0 if None
            # Note: API layer (api.py) handles fetching from network_config before calling this
            effective_discount_rate = discount_rate if discount_rate is not None else 0.0
            logger.info(f"Discount rate for solve: {effective_discount_rate}")
            
            years = list(network.investment_periods)
            
            logger.info(f"Multi-period optimization with {len(years)} periods: {years}")
            
            # Calculate investment period weightings with discount rate
            self._calculate_investment_weightings(network, effective_discount_rate)
            
            # Set snapshot weightings after multi-period setup
            if conn and network_id:
                self._set_snapshot_weightings_after_multiperiod(conn, network_id, network)
            
            # Prepare optimization constraints - ONLY model constraints
            # Network constraints were already applied before solve in api.py
            extra_functionality = None
            model_constraints = []
            
            if conn and network_id and constraint_applicator:
                optimization_constraints = constraint_applicator.get_optimization_constraints(conn, network_id, scenario_id)
                if optimization_constraints:
                    logger.info(f"Found {len(optimization_constraints)} optimization constraints")
                    
                    # Filter for model constraints only (network constraints already applied)
                    for constraint in optimization_constraints:
                        constraint_code = constraint.get('constraint_code', '')
                        constraint_type = self._detect_constraint_type(constraint_code)
                        constraint_name = constraint.get('name', 'unknown')
                        
                        if constraint_type == "model_constraint":
                            model_constraints.append(constraint)
                            logger.info(f"Will apply model constraint during solve: {constraint_name}")
                        else:
                            logger.info(f"Skipping network constraint (already applied): {constraint_name}")
                    
                    logger.info(f"Will apply {len(model_constraints)} model constraints during optimization")
                    
                    # Create extra_functionality for model constraints only
                    if model_constraints:
                        extra_functionality = self._create_extra_functionality(model_constraints, constraint_applicator)
                        logger.info(f"Prepared {len(model_constraints)} model constraints for optimization-time application")
            
            # NOTE: Model constraints are applied DURING solve via extra_functionality
            # Network constraints were already applied to the network structure before solve
            
            # Solver diagnostics
            logger.info(f"=== PYPSA SOLVER DIAGNOSTICS ===")
            logger.info(f"Solver: {actual_solver_name}")
            logger.info(f"Investment periods: {years}")
            logger.info(f"Snapshots: {len(network.snapshots)} (MultiIndex)")
            if solver_config:
                logger.info(f"Solver options: {solver_config}")
            logger.info(f"=== END PYPSA SOLVER DIAGNOSTICS ===")
            
            # Always solve with multi-period optimization
            logger.info(f"Solving network with multi-period optimization using {actual_solver_name}")
            
            # DEBUG: Check network structure before solving
            logger.info(f"DEBUG: Network snapshots type: {type(network.snapshots)}")
            logger.info(f"DEBUG: Network snapshots names: {getattr(network.snapshots, 'names', 'No names')}")
            logger.info(f"DEBUG: Network snapshots shape: {len(network.snapshots)}")
            logger.info(f"DEBUG: First 3 snapshots: {network.snapshots[:3].tolist()}")
            
            # Check some timeseries data structure
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p_max_pu'):
                if not network.generators_t.p_max_pu.empty:
                    logger.info(f"DEBUG: generators_t.p_max_pu type: {type(network.generators_t.p_max_pu)}")
                    logger.info(f"DEBUG: generators_t.p_max_pu index type: {type(network.generators_t.p_max_pu.index)}")
                    logger.info(f"DEBUG: generators_t.p_max_pu index names: {getattr(network.generators_t.p_max_pu.index, 'names', 'No names')}")
                    logger.info(f"DEBUG: generators_t.p_max_pu shape: {network.generators_t.p_max_pu.shape}")
                    logger.info(f"DEBUG: First 3 p_max_pu index values: {network.generators_t.p_max_pu.index[:3].tolist()}")
            
            if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p_set'):
                if not network.loads_t.p_set.empty:
                    logger.info(f"DEBUG: loads_t.p_set type: {type(network.loads_t.p_set)}")
                    logger.info(f"DEBUG: loads_t.p_set index type: {type(network.loads_t.p_set.index)}")
                    logger.info(f"DEBUG: loads_t.p_set index names: {getattr(network.loads_t.p_set.index, 'names', 'No names')}")
                    logger.info(f"DEBUG: loads_t.p_set shape: {network.loads_t.p_set.shape}")
                    logger.info(f"DEBUG: First 3 p_set index values: {network.loads_t.p_set.index[:3].tolist()}")
            
            if solver_config:
                result = network.optimize(solver_name=actual_solver_name, multi_investment_periods=True, 
                                        extra_functionality=extra_functionality, **solver_config)
            else:
                result = network.optimize(solver_name=actual_solver_name, multi_investment_periods=True,
                                        extra_functionality=extra_functionality)
            
            solve_time = time.time() - start_time
            
            # Post-solve debug logging (matches old code)
            objective_value = getattr(network, 'objective', None)
            if objective_value is not None:
                logger.info(f"[DEBUG] POST-SOLVE snapshot_weightings structure:")
                if hasattr(network, 'snapshot_weightings'):
                    logger.info(f"[DEBUG] Type: {type(network.snapshot_weightings)}")
                    logger.info(f"[DEBUG] Columns: {list(network.snapshot_weightings.columns)}")
                    logger.info(f"[DEBUG] Shape: {network.snapshot_weightings.shape}")
                    logger.info(f"[DEBUG] Unique values in objective column: {network.snapshot_weightings['objective'].unique()}")
                    logger.info(f"[DEBUG] Sum of objective column: {network.snapshot_weightings['objective'].sum()}")
                    
                    if hasattr(network, 'investment_period_weightings'):
                        logger.info(f"[DEBUG] investment_period_weightings exists:")
                        logger.info(f"[DEBUG] Type: {type(network.investment_period_weightings)}")
                        logger.info(f"[DEBUG] Content:\n{network.investment_period_weightings}")
            
            # Extract solve results with comprehensive statistics
            solve_result = self._extract_solve_results(network, result, solve_time, actual_solver_name, run_id)
            
            # Calculate comprehensive network statistics (all years combined)
            if solve_result.get('success'):
                logger.info("Calculating comprehensive network statistics...")
                network_statistics = self._calculate_comprehensive_network_statistics(network, solve_time, actual_solver_name)
                solve_result['network_statistics'] = network_statistics
                
                # Calculate year-based statistics for capacity expansion analysis
                logger.info("Calculating year-based statistics...")
                year_statistics = self._calculate_statistics_by_year(network, solve_time, actual_solver_name)
                solve_result['year_statistics'] = year_statistics
                solve_result['year_statistics_available'] = len(year_statistics) > 0
            
            logger.info(f"Solve completed in {solve_time:.2f} seconds with status: {solve_result['status']}")
            logger.info(f"PyPSA result object: {result}")
            logger.info(f"PyPSA result status: {getattr(result, 'status', 'no status attr')}")
            logger.info(f"Network objective: {getattr(network, 'objective', 'no objective')}")
            logger.info(f"Solve result success: {solve_result.get('success')}")
            
            return solve_result
            
        except Exception as e:
            solve_time = time.time() - start_time
            logger.error(f"Solve failed after {solve_time:.2f} seconds: {e}")
            logger.exception("Full solve error traceback:")
            
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "solve_time": solve_time,
                "solver_name": actual_solver_name if 'actual_solver_name' in locals() else solver_name,
                "run_id": run_id,
                "objective_value": None
            }
    
    def _get_solver_config(self, solver_name: str, solver_options: Optional[Dict[str, Any]] = None, 
                           custom_solver_config: Optional[Dict[str, Any]] = None) -> tuple[str, Optional[Dict[str, Any]]]:
        """
        Get the actual solver name and options for special solver configurations.
        
        Args:
            solver_name: The solver name (e.g., 'gurobi (barrier)', 'highs', 'custom')
            solver_options: Optional additional solver options
            custom_solver_config: Optional custom solver configuration for solver_name='custom'
                Format: {"solver": "actual_solver_name", "solver_options": {...}}
            
        Returns:
            Tuple of (actual_solver_name, solver_options_dict)
        """
        # Handle "custom" solver with custom configuration
        if solver_name == 'custom':
            if not custom_solver_config:
                raise ValueError("custom_solver_config must be provided when solver_name='custom'")
            
            if 'solver' not in custom_solver_config:
                raise ValueError("custom_solver_config must contain 'solver' key with the actual solver name")
            
            actual_solver = custom_solver_config['solver']
            custom_options = custom_solver_config.get('solver_options', {})
            
            # Merge with any additional solver_options passed separately
            if solver_options:
                merged_options = {'solver_options': {**custom_options, **solver_options}}
            else:
                merged_options = {'solver_options': custom_options} if custom_options else None
            
            logger.info(f"Using custom solver configuration: {actual_solver} with options: {custom_options}")
            return actual_solver, merged_options
        
        # Handle "default" solver
        if solver_name == 'default':
            # Try to read user's default solver preference
            actual_solver = self._resolve_default_solver()
            logger.info(f"Resolved 'default' solver to: {actual_solver}")
            return actual_solver, solver_options
        
        # Handle special Gurobi configurations
        if solver_name == 'gurobi (barrier)':
            gurobi_barrier_options = {
                'solver_options': {
                    'Method': 2,             # Barrier
                    'Crossover': 0,          # Skip crossover
                    'MIPGap': 0.05,          # 5% gap
                    'Threads': 0,            # Use all cores (0 = auto)
                    'Presolve': 2,           # Aggressive presolve
                    'ConcurrentMIP': 1,      # Parallel root strategies
                    'BarConvTol': 1e-4,      # Relaxed barrier convergence
                    'FeasibilityTol': 1e-5,
                    'OptimalityTol': 1e-5,
                    'NumericFocus': 1,       # Improve stability
                    'PreSparsify': 1,
                }
            }
            # Merge with any additional options
            if solver_options:
                gurobi_barrier_options.update(solver_options)
            return 'gurobi', gurobi_barrier_options

        elif solver_name == 'gurobi (barrier homogeneous)':
            gurobi_barrier_homogeneous_options = {
                'solver_options': {
                    'Method': 2,             # Barrier
                    'Crossover': 0,          # Skip crossover
                    'MIPGap': 0.05,
                    'Threads': 0,            # Use all cores (0 = auto)
                    'Presolve': 2,
                    'ConcurrentMIP': 1,
                    'BarConvTol': 1e-4,
                    'FeasibilityTol': 1e-5,
                    'OptimalityTol': 1e-5,
                    'NumericFocus': 1,
                    'PreSparsify': 1,
                    'BarHomogeneous': 1,     # Enable homogeneous barrier algorithm
                }
            }
            if solver_options:
                gurobi_barrier_homogeneous_options.update(solver_options)
            return 'gurobi', gurobi_barrier_homogeneous_options

        elif solver_name == 'gurobi (barrier+crossover balanced)':
            gurobi_options_balanced = {
                'solver_options': {
                    'Method': 2,
                    'Crossover': 1,         # Dual crossover
                    'MIPGap': 0.01,
                    'Threads': 0,            # Use all cores (0 = auto)
                    'Presolve': 2,
                    'Heuristics': 0.1,
                    'Cuts': 2,
                    'ConcurrentMIP': 1,
                    'BarConvTol': 1e-6,
                    'FeasibilityTol': 1e-6,
                    'OptimalityTol': 1e-6,
                    'NumericFocus': 1,
                    'PreSparsify': 1,
                }
            }
            if solver_options:
                gurobi_options_balanced.update(solver_options)
            logger.info(f"Using Gurobi Barrier+Dual Crossover Balanced configuration")
            return 'gurobi', gurobi_options_balanced

        elif solver_name == 'gurobi (dual simplex)':
            gurobi_dual_options = {
                'solver_options': {
                    'Method': 1,           # Dual simplex method
                    'Threads': 0,          # Use all available cores
                    'Presolve': 2,         # Aggressive presolve
                }
            }
            if solver_options:
                gurobi_dual_options.update(solver_options)
            return 'gurobi', gurobi_dual_options
        
        # Handle special Mosek configurations
        elif solver_name == 'mosek (default)':
            # No custom options - let Mosek use its default configuration
            mosek_default_options = {
                'solver_options': {
                    'MSK_DPAR_MIO_REL_GAP_CONST': 0.05,       # MIP relative gap tolerance (5% to match Gurobi)
                    'MSK_IPAR_MIO_MAX_TIME': 36000,            # Max time 1 hour
                }
            }
            if solver_options:
                mosek_default_options['solver_options'].update(solver_options)
            logger.info(f"Using Mosek with default configuration (auto-select optimizer) and moderate MIP strategies")
            return 'mosek', mosek_default_options
        
        elif solver_name == 'mosek (barrier)':
            mosek_barrier_options = {
                'solver_options': {
                    'MSK_IPAR_INTPNT_BASIS': 0,                # Skip crossover (barrier-only) - 0 = MSK_BI_NEVER
                    'MSK_DPAR_INTPNT_TOL_REL_GAP': 1e-4,      # Match Gurobi barrier tolerance
                    'MSK_DPAR_INTPNT_TOL_PFEAS': 1e-5,        # Match Gurobi primal feasibility
                    'MSK_DPAR_INTPNT_TOL_DFEAS': 1e-5,        # Match Gurobi dual feasibility
                    # Removed MSK_DPAR_INTPNT_TOL_INFEAS - was 1000x tighter than other tolerances!
                    'MSK_IPAR_NUM_THREADS': 0,                # Use all available cores (0 = auto)
                    'MSK_IPAR_PRESOLVE_USE': 2,               # Aggressive presolve (match Gurobi Presolve=2)
                    'MSK_DPAR_MIO_REL_GAP_CONST': 0.05,       # Match Gurobi 5% MIP gap
                    'MSK_IPAR_MIO_ROOT_OPTIMIZER': 4,         # Use interior-point for MIP root
                    'MSK_DPAR_MIO_MAX_TIME': 36000,            # Max time 10 hour
                }
            }
            if solver_options:
                mosek_barrier_options['solver_options'].update(solver_options)
            logger.info(f"Using Mosek Barrier with aggressive presolve and relaxed tolerances")
            return 'mosek', mosek_barrier_options
        
        elif solver_name == 'mosek (barrier+crossover)':
            mosek_barrier_crossover_options = {
                'solver_options': {
                    'MSK_IPAR_INTPNT_BASIS': 1,                # Always crossover (1 = MSK_BI_ALWAYS)
                    'MSK_DPAR_INTPNT_TOL_REL_GAP': 1e-4,      # Match Gurobi barrier tolerance (was 1e-6)
                    'MSK_DPAR_INTPNT_TOL_PFEAS': 1e-5,        # Match Gurobi (was 1e-6)
                    'MSK_DPAR_INTPNT_TOL_DFEAS': 1e-5,        # Match Gurobi (was 1e-6)
                    'MSK_IPAR_NUM_THREADS': 0,                # Use all available cores (0 = auto)
                    'MSK_DPAR_MIO_REL_GAP_CONST': 0.05,       # Match Gurobi 5% MIP gap (was 1e-6)
                    'MSK_IPAR_MIO_ROOT_OPTIMIZER': 4,         # Use interior-point for MIP root
                    'MSK_DPAR_MIO_MAX_TIME': 36000,            # Max time 10 hour (safety limit)
                }
            }
            if solver_options:
                mosek_barrier_crossover_options['solver_options'].update(solver_options)
            logger.info(f"Using Mosek Barrier+Crossover configuration with Gurobi-matched tolerances and moderate MIP strategies")
            return 'mosek', mosek_barrier_crossover_options
        
        elif solver_name == 'mosek (dual simplex)':
            mosek_dual_options = {
                'solver_options': {
                    'MSK_IPAR_NUM_THREADS': 0,                # Use all available cores (0 = automatic)
                    'MSK_IPAR_PRESOLVE_USE': 1,               # Force presolve
                    'MSK_DPAR_MIO_REL_GAP_CONST': 0.05,       # Match Gurobi 5% MIP gap (was 1e-6)
                    'MSK_IPAR_MIO_ROOT_OPTIMIZER': 1,         # Use dual simplex for MIP root
                    'MSK_DPAR_MIO_MAX_TIME': 36000,            # Max time 10 hour (safety limit)

                }
            }
            if solver_options:
                mosek_dual_options['solver_options'].update(solver_options)
            logger.info(f"Using Mosek Dual Simplex configuration with Gurobi-matched tolerances and moderate MIP strategies")
            return 'mosek', mosek_dual_options
        
        # Check if this is a known valid solver name
        elif solver_name == 'mosek':
            # Add default MILP-friendly settings for plain Mosek
            mosek_defaults = {
                'solver_options': {
                    'MSK_DPAR_MIO_REL_GAP_CONST': 0.05,       # Match Gurobi 5% MIP gap (was 1e-4)
                    'MSK_IPAR_MIO_MAX_TIME': 36000,            # Max time 1 hour
                    'MSK_IPAR_NUM_THREADS': 0,                # Use all cores (0 = auto)
                }
            }
            if solver_options:
                mosek_defaults['solver_options'].update(solver_options)
            logger.info(f"Using Mosek with barrier method for MIP (interior-point for root/nodes)")
            return solver_name, mosek_defaults
        
        elif solver_name == 'gurobi':
            # Add default MILP-friendly settings for plain Gurobi (for consistency)
            gurobi_defaults = {
                'solver_options': {
                    'MIPGap': 1e-4,          # 0.01% gap
                    'TimeLimit': 3600,       # 1 hour
                    'Threads': 0,            # Use all cores
                    'OutputFlag': 1,         # Enable output
                }
            }
            if solver_options:
                gurobi_defaults['solver_options'].update(solver_options)
            logger.info(f"Using Gurobi with default MILP-friendly settings")
            return solver_name, gurobi_defaults
        
        # Handle special COPT configurations
        elif solver_name == 'copt (barrier)':
            copt_barrier_options = {
                'solver_options': {
                    'LpMethod': 2,              # Barrier method
                    'Crossover': 0,             # Skip crossover for speed
                    'RelGap': 0.05,             # 5% MIP gap (match Gurobi)
                    'TimeLimit': 7200,          # 1 hour time limit
                    'Threads': -1,               # 4 threads (memory-conscious)
                    'Presolve': 3,              # Aggressive presolve
                    'Scaling': 1,               # Enable scaling
                    'FeasTol': 1e-5,            # Match Gurobi feasibility
                    'DualTol': 1e-5,            # Match Gurobi dual tolerance
                    # MIP performance settings
                    'CutLevel': 2,              # Normal cut generation
                    'HeurLevel': 3,             # Aggressive heuristics
                    'StrongBranching': 1,       # Fast strong branching
                }
            }
            if solver_options:
                copt_barrier_options['solver_options'].update(solver_options)
            logger.info(f"Using COPT Barrier configuration (fast interior-point method)")
            return 'copt', copt_barrier_options
        
        elif solver_name == 'copt (barrier homogeneous)':
            copt_barrier_homogeneous_options = {
                'solver_options': {
                    'LpMethod': 2,              # Barrier method
                    'Crossover': 0,             # Skip crossover
                    'BarHomogeneous': 1,        # Use homogeneous self-dual form
                    'RelGap': 0.05,             # 5% MIP gap
                    'TimeLimit': 3600,          # 1 hour
                    'Threads': -1,               # 4 threads (memory-conscious)
                    'Presolve': 3,              # Aggressive presolve
                    'Scaling': 1,               # Enable scaling
                    'FeasTol': 1e-5,
                    'DualTol': 1e-5,
                    # MIP performance settings
                    'CutLevel': 2,              # Normal cuts
                    'HeurLevel': 3,             # Aggressive heuristics
                    'StrongBranching': 1,       # Fast strong branching
                }
            }
            if solver_options:
                copt_barrier_homogeneous_options['solver_options'].update(solver_options)
            logger.info(f"Using COPT Barrier Homogeneous configuration")
            return 'copt', copt_barrier_homogeneous_options
        
        elif solver_name == 'copt (barrier+crossover)':
            copt_barrier_crossover_options = {
                'solver_options': {
                    'LpMethod': 2,              # Barrier method
                    'Crossover': 1,             # Enable crossover for better solutions
                    'RelGap': 0.05,             # 5% MIP gap (relaxed for faster solves)
                    'TimeLimit': 36000,          # 10 hour
                    'Threads': -1,              # Use all cores
                    'Presolve': 2,              # Aggressive presolve
                    'Scaling': 1,               # Enable scaling
                    'FeasTol': 1e-4,            # Tighter feasibility
                    'DualTol': 1e-4,            # Tighter dual tolerance
                }
            }
            if solver_options:
                copt_barrier_crossover_options['solver_options'].update(solver_options)
            logger.info(f"Using COPT Barrier+Crossover configuration (balanced performance)")
            return 'copt', copt_barrier_crossover_options
        
        elif solver_name == 'copt (dual simplex)':
            copt_dual_simplex_options = {
                'solver_options': {
                    'LpMethod': 1,              # Dual simplex method
                    'RelGap': 0.05,             # 5% MIP gap
                    'TimeLimit': 3600,          # 1 hour
                    'Threads': -1,              # Use all cores
                    'Presolve': 3,              # Aggressive presolve
                    'Scaling': 1,               # Enable scaling
                    'FeasTol': 1e-6,
                    'DualTol': 1e-6,
                    # MIP performance settings
                    'CutLevel': 2,              # Normal cuts
                    'HeurLevel': 2,             # Normal heuristics
                    'StrongBranching': 1,       # Fast strong branching
                }
            }
            if solver_options:
                copt_dual_simplex_options['solver_options'].update(solver_options)
            logger.info(f"Using COPT Dual Simplex configuration (robust method)")
            return 'copt', copt_dual_simplex_options
        
        elif solver_name == 'copt (concurrent)':
            copt_concurrent_options = {
                'solver_options': {
                    'LpMethod': 4,              # Concurrent (simplex + barrier)
                    'RelGap': 0.05,             # 5% MIP gap
                    'TimeLimit': 3600,          # 1 hour
                    'Threads': -1,              # Use all cores
                    'Presolve': 3,              # Aggressive presolve
                    'Scaling': 1,               # Enable scaling
                    'FeasTol': 1e-5,
                    'DualTol': 1e-5,
                    # MIP performance settings
                    'CutLevel': 2,              # Normal cuts
                    'HeurLevel': 3,             # Aggressive heuristics
                    'StrongBranching': 1,       # Fast strong branching
                }
            }
            if solver_options:
                copt_concurrent_options['solver_options'].update(solver_options)
            logger.info(f"Using COPT Concurrent configuration (parallel simplex + barrier)")
            return 'copt', copt_concurrent_options
        
        elif solver_name in ['highs', 'cplex', 'glpk', 'cbc', 'scip', 'copt']:
            return solver_name, solver_options
        
        else:
            # Unknown solver name - log warning and fall back to highs
            logger.warning(f"Unknown solver name '{solver_name}' - falling back to 'highs'")
            return 'highs', solver_options
    
    
    def _detect_constraint_type(self, constraint_code: str) -> str:
        """
        Detect if constraint is network-modification or model-constraint type.
        
        Args:
            constraint_code: The constraint code to analyze
            
        Returns:
            "model_constraint" or "network_modification"
        """
        # Type 2 indicators (model constraints) - need access to optimization model
        model_indicators = [
            'n.optimize.create_model()',
            'm.variables',
            'm.add_constraints',
            'gen_p =',
            'constraint_expr =',
            'LinearExpression',
            'linopy',
            'Generator-p',
            'lhs <=',
            'constraint_expr ='
        ]
        
        # Type 1 indicators (network modifications) - modify network directly
        network_indicators = [
            'n.generators.loc',
            'n.add(',
            'n.buses.',
            'n.lines.',
            'network.generators.loc',
            'network.add(',
            'network.buses.',
            'network.lines.'
        ]
        
        # Check for model constraint indicators first (more specific)
        if any(indicator in constraint_code for indicator in model_indicators):
            return "model_constraint"
        elif any(indicator in constraint_code for indicator in network_indicators):
            return "network_modification"
        else:
            # Default to network_modification for safety (existing behavior)
            return "network_modification"

    def _create_extra_functionality(self, optimization_constraints: list, constraint_applicator) -> callable:
        """
        Create extra_functionality function for optimization-time constraints.
        
        This matches the old PyPSA solver's approach to applying constraints during optimization.
        
        Args:
            optimization_constraints: List of optimization constraint dictionaries
            constraint_applicator: ConstraintApplicator instance
            
        Returns:
            Function that can be passed to network.optimize(extra_functionality=...)
        """
        def extra_functionality(network, snapshots):
            """Apply optimization constraints during solve - matches old code structure"""
            try:
                logger.info(f"Applying {len(optimization_constraints)} optimization constraints during solve")
                
                # Apply each constraint in priority order
                sorted_constraints = sorted(optimization_constraints, key=lambda x: x.get('priority', 0))
                
                for constraint in sorted_constraints:
                    try:
                        constraint_applicator.apply_optimization_constraint(network, snapshots, constraint)
                    except Exception as e:
                        logger.error(f"Failed to apply optimization constraint {constraint.get('name', 'unknown')}: {e}")
                        continue
                
                logger.info("Optimization constraints applied successfully")
                
            except Exception as e:
                logger.error(f"Failed to apply optimization constraints: {e}")
                # Don't re-raise - let optimization continue
        
        return extra_functionality
    
    def _set_snapshot_weightings_after_multiperiod(self, conn, network_id: int, network: 'pypsa.Network'):
        """Set snapshot weightings AFTER multi-period setup - matches old code approach."""
        try:
            from pyconvexity.models import get_network_time_periods, get_network_info
            
            time_periods = get_network_time_periods(conn, network_id)
            if time_periods and len(network.snapshots) > 0:
                logger.info(f"Setting snapshot weightings AFTER multi-period setup for {len(time_periods)} time periods")
                
                # Get network info to determine time interval (stored in networks table, not network_config)
                network_info = get_network_info(conn, network_id)
                time_interval = network_info.get('time_interval', '1H')
                weight = self._parse_time_interval(time_interval)
                
                if weight is None:
                    weight = 1.0
                    logger.warning(f"Could not parse time interval '{time_interval}', using default weight of 1.0")
                
                logger.info(f"Parsed time interval '{time_interval}' -> weight = {weight}")
                
                # Create weightings array - all snapshots get the same weight for this time resolution
                weightings = [weight] * len(time_periods)
                
                if len(weightings) == len(network.snapshots):
                    # Set all three columns like the old code - critical for proper objective calculation
                    network.snapshot_weightings.loc[:, 'objective'] = weightings
                    network.snapshot_weightings.loc[:, 'generators'] = weightings  
                    network.snapshot_weightings.loc[:, 'stores'] = weightings
                    logger.info(f"Set snapshot weightings AFTER multi-period setup: objective, generators, stores columns")
                    
                    # Debug logging like old code
                    logger.info(f"Snapshot weightings shape: {network.snapshot_weightings.shape}")
                    logger.info(f"Unique values in objective column: {network.snapshot_weightings['objective'].unique()}")
                    logger.info(f"Sum of objective column: {network.snapshot_weightings['objective'].sum()}")
                    logger.info(f"Weight per snapshot: {weight} hours")
                else:
                    logger.warning(f"Mismatch between weightings ({len(weightings)}) and snapshots ({len(network.snapshots)})")
        except Exception as e:
            logger.warning(f"Failed to set snapshot weightings after multi-period setup: {e}")
            logger.exception("Full traceback:")
    
    def _parse_time_interval(self, time_interval: str) -> Optional[float]:
        """Parse time interval string to hours - handles multiple formats."""
        if not time_interval:
            return None
        
        try:
            # Clean up the string
            interval = time_interval.strip()
            
            # Handle ISO 8601 duration format (PT3H, PT30M, etc.)
            if interval.startswith('PT') and interval.endswith('H'):
                # Extract hours (e.g., 'PT3H' -> 3.0)
                hours_str = interval[2:-1]  # Remove 'PT' and 'H'
                return float(hours_str)
            elif interval.startswith('PT') and interval.endswith('M'):
                # Extract minutes (e.g., 'PT30M' -> 0.5)
                minutes_str = interval[2:-1]  # Remove 'PT' and 'M'
                return float(minutes_str) / 60.0
            elif interval.startswith('PT') and interval.endswith('S'):
                # Extract seconds (e.g., 'PT3600S' -> 1.0)
                seconds_str = interval[2:-1]  # Remove 'PT' and 'S'
                return float(seconds_str) / 3600.0
            
            # Handle simple frequency strings (3H, 2D, etc.)
            elif interval.endswith('H') or interval.endswith('h'):
                hours_str = interval[:-1]
                return float(hours_str) if hours_str else 1.0
            elif interval.endswith('D') or interval.endswith('d'):
                days_str = interval[:-1]
                return float(days_str) * 24 if days_str else 24.0
            elif interval.endswith('M') or interval.endswith('m'):
                minutes_str = interval[:-1]
                return float(minutes_str) / 60.0 if minutes_str else 1.0/60.0
            elif interval.endswith('S') or interval.endswith('s'):
                seconds_str = interval[:-1]
                return float(seconds_str) / 3600.0 if seconds_str else 1.0/3600.0
            
            # Try to parse as plain number (assume hours)
            else:
                return float(interval)
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse time interval '{time_interval}': {e}")
            return None
    
    def _calculate_investment_weightings(self, network: 'pypsa.Network', discount_rate: float) -> None:
        """
        Calculate investment period weightings using discount rate - matching old PyPSA solver exactly.
        
        Args:
            network: PyPSA Network object
            discount_rate: Discount rate for NPV calculations
        """
        try:
            import pandas as pd
            
            if not hasattr(network, 'investment_periods') or len(network.investment_periods) == 0:
                return
            
            years = network.investment_periods
            # Convert pandas Index to list for easier handling
            years_list = years.tolist() if hasattr(years, 'tolist') else list(years)
            
            logger.info(f"Calculating investment weightings for periods: {years_list} with discount rate: {discount_rate}")
            
            # For single year, use simple weighting of 1.0
            if len(years_list) == 1:
                # Single year case
                network.investment_period_weightings = pd.DataFrame({
                    'objective': pd.Series({years_list[0]: 1.0}),
                    'years': pd.Series({years_list[0]: 1})
                })
                logger.info(f"Set single-year investment period weightings for year {years_list[0]}")
            else:
                # Multi-year case - EXACTLY match old code logic
                # Get unique years from the network snapshots to determine period lengths
                if hasattr(network.snapshots, 'year'):
                    snapshot_years = sorted(network.snapshots.year.unique())
                elif hasattr(network.snapshots, 'get_level_values'):
                    # MultiIndex case - get years from 'period' level
                    snapshot_years = sorted(network.snapshots.get_level_values('period').unique())
                else:
                    # Fallback: use investment periods as years
                    snapshot_years = years_list
                
                logger.info(f"Snapshot years found: {snapshot_years}")
                
                # Calculate years per period - EXACTLY matching old code
                years_diff = []
                for i, year in enumerate(years_list):
                    if i < len(years_list) - 1:
                        # Years between this period and the next
                        next_year = years_list[i + 1]
                        period_years = next_year - year
                    else:
                        # For the last period, calculate based on snapshot coverage
                        if snapshot_years:
                            # Find the last snapshot year that's >= current period year
                            last_snapshot_year = max([y for y in snapshot_years if y >= year])
                            period_years = last_snapshot_year - year + 1
                        else:
                            # Fallback: assume same length as previous period or 1
                            if len(years_diff) > 0:
                                period_years = years_diff[-1]  # Same as previous period
                            else:
                                period_years = 1
                    
                    years_diff.append(period_years)
                    logger.info(f"Period {year}: {period_years} years")
                
                # Create weightings DataFrame with years column
                weightings_df = pd.DataFrame({
                    'years': pd.Series(years_diff, index=years_list)
                })
                
                # Calculate objective weightings with discount rate - EXACTLY matching old code
                r = discount_rate
                T = 0  # Cumulative time tracker
                
                logger.info(f"Calculating discount factors with rate {r}:")
                for period, nyears in weightings_df.years.items():
                    # Calculate discount factors for each year in this period
                    discounts = [(1 / (1 + r) ** t) for t in range(T, T + nyears)]
                    period_weighting = sum(discounts)
                    weightings_df.at[period, "objective"] = period_weighting
                    
                    logger.info(f"  Period {period}: years {T} to {T + nyears - 1}, discounts={[f'{d:.4f}' for d in discounts]}, sum={period_weighting:.4f}")
                    T += nyears  # Update cumulative time
                
                network.investment_period_weightings = weightings_df
                logger.info(f"Final investment period weightings:")
                logger.info(f"  Years: {weightings_df['years'].to_dict()}")
                logger.info(f"  Objective: {weightings_df['objective'].to_dict()}")
            
        except Exception as e:
            logger.error(f"Failed to calculate investment weightings: {e}")
            logger.exception("Full traceback:")
    
    
    def _extract_solve_results(self, network: 'pypsa.Network', result: Any, solve_time: float, solver_name: str, run_id: str) -> Dict[str, Any]:
        """
        Extract solve results from PyPSA network.
        
        Args:
            network: Solved PyPSA Network object
            result: PyPSA solve result
            solve_time: Time taken to solve
            solver_name: Name of solver used
            run_id: Unique run identifier
            
        Returns:
            Dictionary with solve results and metadata
        """
        try:
            # Extract basic solve information
            status = getattr(result, 'status', 'unknown')
            objective_value = getattr(network, 'objective', None)
            
            # Debug logging
            logger.info(f"Raw PyPSA result attributes: {dir(result) if result else 'None'}")
            if hasattr(result, 'termination_condition'):
                logger.info(f"Termination condition: {result.termination_condition}")
            if hasattr(result, 'solver'):
                logger.info(f"Solver info: {result.solver}")
            
            # Convert PyPSA result to dictionary format
            result_dict = self._convert_pypsa_result_to_dict(result)
            
            # Determine success based on multiple criteria
            success = self._determine_solve_success(result, network, status, objective_value)
            
            solve_result = {
                "success": success,
                "status": status,
                "solve_time": solve_time,
                "solver_name": solver_name,
                "run_id": run_id,
                "objective_value": objective_value,
                "pypsa_result": result_dict,
                "network_name": network.name,
                "num_buses": len(network.buses),
                "num_generators": len(network.generators),
                "num_loads": len(network.loads),
                "num_lines": len(network.lines),
                "num_links": len(network.links),
                "num_snapshots": len(network.snapshots)
            }
            
            # Add multi-period information if available
            if hasattr(network, '_available_years') and network._available_years:
                solve_result["years"] = network._available_years
                solve_result["multi_period"] = len(network._available_years) > 1
            
            return solve_result
            
        except Exception as e:
            logger.error(f"Failed to extract solve results: {e}")
            return {
                "success": False,
                "status": "extraction_failed",
                "error": f"Failed to extract results: {e}",
                "solve_time": solve_time,
                "solver_name": solver_name,
                "run_id": run_id,
                "objective_value": None
            }
    
    def _determine_solve_success(self, result: Any, network: 'pypsa.Network', status: str, objective_value: Optional[float]) -> bool:
        """
        Determine if solve was successful based on multiple criteria.
        
        PyPSA sometimes returns status='unknown' even for successful solves,
        so we need to check multiple indicators.
        """
        try:
            # Check explicit status first
            if status in ['optimal', 'feasible']:
                logger.info(f"Success determined by status: {status}")
                return True
            
            # Check termination condition
            if hasattr(result, 'termination_condition'):
                term_condition = str(result.termination_condition).lower()
                if 'optimal' in term_condition:
                    logger.info(f"Success determined by termination condition: {result.termination_condition}")
                    return True
            
            # Check if we have a valid objective value
            if objective_value is not None and not (objective_value == 0 and status == 'unknown'):
                logger.info(f"Success determined by valid objective value: {objective_value}")
                return True
            
            # Check solver-specific success indicators
            if hasattr(result, 'solver'):
                solver_info = result.solver
                if hasattr(solver_info, 'termination_condition'):
                    term_condition = str(solver_info.termination_condition).lower()
                    if 'optimal' in term_condition:
                        logger.info(f"Success determined by solver termination condition: {solver_info.termination_condition}")
                        return True
            
            logger.warning(f"Could not determine success: status={status}, objective={objective_value}, result_attrs={dir(result) if result else 'None'}")
            return False
            
        except Exception as e:
            logger.error(f"Error determining solve success: {e}")
            return False
    
    def _convert_pypsa_result_to_dict(self, result) -> Dict[str, Any]:
        """
        Convert PyPSA result object to dictionary.
        
        Args:
            result: PyPSA solve result object
            
        Returns:
            Dictionary representation of the result
        """
        try:
            if result is None:
                return {"status": "no_result"}
            
            result_dict = {}
            
            # Extract common attributes
            for attr in ['status', 'success', 'termination_condition', 'solver']:
                if hasattr(result, attr):
                    value = getattr(result, attr)
                    # Convert to serializable format
                    if hasattr(value, '__dict__'):
                        result_dict[attr] = str(value)
                    else:
                        result_dict[attr] = value
            
            # Handle solver-specific information
            if hasattr(result, 'solver_results'):
                solver_results = getattr(result, 'solver_results')
                if hasattr(solver_results, '__dict__'):
                    result_dict['solver_results'] = str(solver_results)
                else:
                    result_dict['solver_results'] = solver_results
            
            return result_dict
            
        except Exception as e:
            logger.warning(f"Failed to convert PyPSA result to dict: {e}")
            return {"status": "conversion_failed", "error": str(e)}
    
    def _calculate_comprehensive_network_statistics(self, network: 'pypsa.Network', solve_time: float, solver_name: str) -> Dict[str, Any]:
        """Calculate comprehensive network statistics including PyPSA statistics and custom metrics"""
        try:
            # Initialize statistics structure
            statistics = {
                "core_summary": {},
                "pypsa_statistics": {},
                "custom_statistics": {},
                "runtime_info": {},
                "solver_info": {}
            }
            
            # Core summary statistics
            total_generation = 0
            total_demand = 0
            unserved_energy = 0
            
            # Calculate generation statistics
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                # Apply snapshot weightings to convert MW to MWh
                weightings = network.snapshot_weightings
                if isinstance(weightings, pd.DataFrame):
                    if 'objective' in weightings.columns:
                        weighting_values = weightings['objective'].values
                    else:
                        weighting_values = weightings.iloc[:, 0].values
                else:
                    weighting_values = weightings.values
                
                total_generation = float((network.generators_t.p.values * weighting_values[:, None]).sum())
                
                # Calculate unserved energy from UNMET_LOAD generators
                if hasattr(network, 'generators') and hasattr(network, '_component_type_map'):
                    unmet_load_gen_names = [name for name, comp_type in network._component_type_map.items() 
                                          if comp_type == 'UNMET_LOAD']
                    
                    for gen_name in unmet_load_gen_names:
                        if gen_name in network.generators_t.p.columns:
                            gen_output = float((network.generators_t.p[gen_name] * weighting_values).sum())
                            unserved_energy += gen_output
            
            # Calculate demand statistics
            if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p'):
                weightings = network.snapshot_weightings
                if isinstance(weightings, pd.DataFrame):
                    if 'objective' in weightings.columns:
                        weighting_values = weightings['objective'].values
                    else:
                        weighting_values = weightings.iloc[:, 0].values
                else:
                    weighting_values = weightings.values
                
                total_demand = float((network.loads_t.p.values * weighting_values[:, None]).sum())
            
            statistics["core_summary"] = {
                "total_generation_mwh": total_generation,
                "total_demand_mwh": total_demand,
                "total_cost": float(network.objective) if hasattr(network, 'objective') else None,
                "load_factor": (total_demand / (total_generation + 1e-6)) if total_generation > 0 else 0,
                "unserved_energy_mwh": unserved_energy
            }
            
            # Calculate PyPSA statistics
            try:
                pypsa_stats = network.statistics()
                if pypsa_stats is not None and not pypsa_stats.empty:
                    statistics["pypsa_statistics"] = self._convert_pypsa_result_to_dict(pypsa_stats)
                else:
                    statistics["pypsa_statistics"] = {}
            except Exception as e:
                logger.error(f"Failed to calculate PyPSA statistics: {e}")
                statistics["pypsa_statistics"] = {}
            
            # Custom statistics - calculate detailed breakdowns
            total_cost = float(network.objective) if hasattr(network, 'objective') else 0.0
            avg_price = (total_cost / (total_generation + 1e-6)) if total_generation > 0 else None
            unmet_load_percentage = (unserved_energy / (total_demand + 1e-6)) * 100 if total_demand > 0 else 0
            
            # Note: For solver statistics, we keep simplified approach since this is just for logging
            # The storage module will calculate proper totals from carrier statistics
            statistics["custom_statistics"] = {
                "total_capital_cost": 0.0,  # Will be calculated properly in storage module
                "total_operational_cost": total_cost,  # PyPSA objective (includes both capital and operational, discounted)
                "total_currency_cost": total_cost,
                "total_emissions_tons_co2": 0.0,  # Will be calculated properly in storage module
                "average_price_per_mwh": avg_price,
                "unmet_load_percentage": unmet_load_percentage,
                "max_unmet_load_hour_mw": 0.0  # TODO: Calculate max hourly unmet load
            }
            
            # Runtime info
            unmet_load_count = 0
            if hasattr(network, '_component_type_map'):
                unmet_load_count = len([name for name, comp_type in network._component_type_map.items() 
                                      if comp_type == 'UNMET_LOAD'])
            
            statistics["runtime_info"] = {
                "solve_time_seconds": solve_time,
                "component_count": (
                    len(network.buses) + len(network.generators) + len(network.loads) + 
                    len(network.lines) + len(network.links)
                ) if hasattr(network, 'buses') else 0,
                "bus_count": len(network.buses) if hasattr(network, 'buses') else 0,
                "generator_count": len(network.generators) if hasattr(network, 'generators') else 0,
                "unmet_load_count": unmet_load_count,
                "load_count": len(network.loads) if hasattr(network, 'loads') else 0,
                "line_count": len(network.lines) if hasattr(network, 'lines') else 0,
                "snapshot_count": len(network.snapshots) if hasattr(network, 'snapshots') else 0
            }
            
            # Solver info
            statistics["solver_info"] = {
                "solver_name": solver_name,
                "termination_condition": "optimal" if hasattr(network, 'objective') else "unknown",
                "objective_value": float(network.objective) if hasattr(network, 'objective') else None
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to calculate comprehensive network statistics: {e}", exc_info=True)
            return {
                "error": str(e),
                "core_summary": {},
                "pypsa_statistics": {},
                "custom_statistics": {},
                "runtime_info": {"solve_time_seconds": solve_time},
                "solver_info": {"solver_name": solver_name}
            }
    
    def _calculate_statistics_by_year(self, network: 'pypsa.Network', solve_time: float, solver_name: str) -> Dict[int, Dict[str, Any]]:
        """Calculate statistics for each year in the network"""
        try:
            # Extract years from network snapshots or manually extracted years
            if hasattr(network.snapshots, 'year'):
                years = sorted(network.snapshots.year.unique())
            elif hasattr(network, '_available_years'):
                years = network._available_years
            elif hasattr(network.snapshots, 'levels'):
                # Multi-period optimization - get years from period level
                period_values = network.snapshots.get_level_values(0)
                years = sorted(period_values.unique())
            else:
                # If no year info, skip year-based calculations
                logger.info("No year information found in network - skipping year-based statistics")
                return {}
            
            logger.info(f"Calculating year-based statistics for years: {years}")
            year_statistics = {}
            
            for year in years:
                try:
                    year_stats = self._calculate_network_statistics_for_year(network, year, solve_time, solver_name)
                    year_statistics[year] = year_stats
                    logger.info(f"Calculated statistics for year {year}")
                except Exception as e:
                    logger.error(f"Failed to calculate statistics for year {year}: {e}")
                    continue
            
            logger.info(f"Successfully calculated year-based statistics for {len(year_statistics)} years")
            return year_statistics
            
        except Exception as e:
            logger.error(f"Failed to calculate year-based statistics: {e}", exc_info=True)
            return {}
    
    def _calculate_network_statistics_for_year(self, network: 'pypsa.Network', year: int, solve_time: float, solver_name: str) -> Dict[str, Any]:
        """Calculate network statistics for a specific year"""
        try:
            # Initialize statistics structure
            statistics = {
                "core_summary": {},
                "custom_statistics": {},
                "runtime_info": {},
                "solver_info": {}
            }
            
            # Core summary statistics for this year
            total_generation = 0
            total_demand = 0
            unserved_energy = 0
            
            # Calculate generation statistics for this year
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                # Filter by year
                year_generation = self._filter_timeseries_by_year(network.generators_t.p, network.snapshots, year)
                if year_generation is not None and not year_generation.empty:
                    # Apply snapshot weightings for this year
                    year_weightings = self._get_year_weightings(network, year)
                    if year_weightings is not None:
                        total_generation = float((year_generation.values * year_weightings[:, None]).sum())
                    else:
                        total_generation = float(year_generation.sum().sum())
                    
                    # Calculate unserved energy for this year
                    if hasattr(network, '_component_type_map'):
                        unmet_load_gen_names = [name for name, comp_type in network._component_type_map.items() 
                                              if comp_type == 'UNMET_LOAD']
                        
                        for gen_name in unmet_load_gen_names:
                            if gen_name in year_generation.columns:
                                if year_weightings is not None:
                                    gen_output = float((year_generation[gen_name] * year_weightings).sum())
                                else:
                                    gen_output = float(year_generation[gen_name].sum())
                                unserved_energy += gen_output
            
            # Calculate demand statistics for this year
            if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p'):
                year_demand = self._filter_timeseries_by_year(network.loads_t.p, network.snapshots, year)
                if year_demand is not None and not year_demand.empty:
                    year_weightings = self._get_year_weightings(network, year)
                    if year_weightings is not None:
                        total_demand = float((year_demand.values * year_weightings[:, None]).sum())
                    else:
                        total_demand = float(year_demand.sum().sum())
            
            statistics["core_summary"] = {
                "total_generation_mwh": total_generation,
                "total_demand_mwh": total_demand,
                "total_cost": None,  # Year-specific cost calculation would be complex
                "load_factor": (total_demand / (total_generation + 1e-6)) if total_generation > 0 else 0,
                "unserved_energy_mwh": unserved_energy
            }
            
            # Custom statistics
            unmet_load_percentage = (unserved_energy / (total_demand + 1e-6)) * 100 if total_demand > 0 else 0
            
            # Calculate year-specific carrier statistics
            year_carrier_stats = self._calculate_year_carrier_statistics(network, year)
            
            statistics["custom_statistics"] = {
                "unmet_load_percentage": unmet_load_percentage,
                "year": year,
                **year_carrier_stats  # Include all carrier-specific statistics for this year
            }
            
            # Runtime info
            year_snapshot_count = self._count_year_snapshots(network.snapshots, year)
            
            statistics["runtime_info"] = {
                "solve_time_seconds": solve_time,
                "year": year,
                "snapshot_count": year_snapshot_count
            }
            
            # Solver info
            statistics["solver_info"] = {
                "solver_name": solver_name,
                "year": year
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Failed to calculate network statistics for year {year}: {e}", exc_info=True)
            return {
                "error": str(e),
                "core_summary": {},
                "custom_statistics": {"year": year},
                "runtime_info": {"solve_time_seconds": solve_time, "year": year},
                "solver_info": {"solver_name": solver_name, "year": year}
            }
    
    def _filter_timeseries_by_year(self, timeseries_df: 'pd.DataFrame', snapshots: 'pd.Index', year: int) -> 'pd.DataFrame':
        """Filter timeseries data by year"""
        try:
            # Handle MultiIndex case (multi-period optimization)
            if hasattr(snapshots, 'levels'):
                period_values = snapshots.get_level_values(0)
                year_mask = period_values == year
                if year_mask.any():
                    year_snapshots = snapshots[year_mask]
                    return timeseries_df.loc[year_snapshots]
            
            # Handle DatetimeIndex case (regular time series)
            elif hasattr(snapshots, 'year'):
                year_mask = snapshots.year == year
                if year_mask.any():
                    return timeseries_df.loc[year_mask]
            
            # Fallback - return None if can't filter
            return None
            
        except Exception as e:
            logger.error(f"Failed to filter timeseries by year {year}: {e}")
            return None
    
    def _get_year_weightings(self, network: 'pypsa.Network', year: int) -> 'np.ndarray':
        """Get snapshot weightings for a specific year"""
        try:
            # Filter snapshot weightings by year
            if hasattr(network.snapshots, 'levels'):
                period_values = network.snapshots.get_level_values(0)
                year_mask = period_values == year
                if year_mask.any():
                    year_snapshots = network.snapshots[year_mask]
                    year_weightings = network.snapshot_weightings.loc[year_snapshots]
                    if isinstance(year_weightings, pd.DataFrame):
                        if 'objective' in year_weightings.columns:
                            return year_weightings['objective'].values
                        else:
                            return year_weightings.iloc[:, 0].values
                    else:
                        return year_weightings.values
            
            elif hasattr(network.snapshots, 'year'):
                year_mask = network.snapshots.year == year
                if year_mask.any():
                    year_weightings = network.snapshot_weightings.loc[year_mask]
                    if isinstance(year_weightings, pd.DataFrame):
                        if 'objective' in year_weightings.columns:
                            return year_weightings['objective'].values
                        else:
                            return year_weightings.iloc[:, 0].values
                    else:
                        return year_weightings.values
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get year weightings for year {year}: {e}")
            return None
    
    def _count_year_snapshots(self, snapshots: 'pd.Index', year: int) -> int:
        """Count snapshots for a specific year"""
        try:
            # Handle MultiIndex case
            if hasattr(snapshots, 'levels'):
                period_values = snapshots.get_level_values(0)
                year_mask = period_values == year
                return year_mask.sum()
            
            # Handle DatetimeIndex case
            elif hasattr(snapshots, 'year'):
                year_mask = snapshots.year == year
                return year_mask.sum()
            
            # Fallback
            return 0
            
        except Exception as e:
            logger.error(f"Failed to count snapshots for year {year}: {e}")
            return 0
    
    def _calculate_year_carrier_statistics(self, network: 'pypsa.Network', year: int) -> Dict[str, Any]:
        """Calculate carrier-specific statistics for a specific year"""
        # Note: This is a simplified implementation that doesn't have database access
        # The proper implementation should be done in the storage module where we have conn and network_id
        # For now, return empty dictionaries - the storage module will handle this properly
        return {
            "dispatch_by_carrier": {},
            "capacity_by_carrier": {},
            "emissions_by_carrier": {},
            "capital_cost_by_carrier": {},
            "operational_cost_by_carrier": {},
            "total_system_cost_by_carrier": {}
        }
    
    def _get_generator_carrier_name(self, generator_name: str) -> Optional[str]:
        """Get carrier name for a generator - simplified implementation"""
        # This is a simplified approach - in practice, this should query the database
        # or use the component type mapping from the network
        
        # Try to extract carrier from generator name patterns
        gen_lower = generator_name.lower()
        
        if 'coal' in gen_lower:
            return 'coal'
        elif 'gas' in gen_lower or 'ccgt' in gen_lower or 'ocgt' in gen_lower:
            return 'gas'
        elif 'nuclear' in gen_lower:
            return 'nuclear'
        elif 'solar' in gen_lower or 'pv' in gen_lower:
            return 'solar'
        elif 'wind' in gen_lower:
            return 'wind'
        elif 'hydro' in gen_lower:
            return 'hydro'
        elif 'biomass' in gen_lower:
            return 'biomass'
        elif 'battery' in gen_lower:
            return 'battery'
        elif 'unmet' in gen_lower:
            return 'Unmet Load'
        else:
            # Default to generator name if no pattern matches
            return generator_name
