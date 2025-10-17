"""
Solver module for PyConvexity.

Provides interfaces to various optimization solvers for energy system modeling.
"""

# Try to import PyPSA solver with graceful fallback
try:
    from pyconvexity.solvers.pypsa import (
        solve_network,
        build_pypsa_network,
        solve_pypsa_network,
        load_network_components,
        apply_constraints,
        store_solve_results
    )
    
    __all__ = [
        "solve_network",
        "build_pypsa_network", 
        "solve_pypsa_network",
        "load_network_components",
        "apply_constraints",
        "store_solve_results"
    ]
    
except ImportError:
    # PyPSA not available
    __all__ = []
