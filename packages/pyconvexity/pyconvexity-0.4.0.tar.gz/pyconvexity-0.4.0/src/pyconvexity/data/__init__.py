"""
PyConvexity Data Module

Provides functions for loading external energy data and integrating it with PyConvexity models.
This module offers a simple, expert-friendly toolbox for working with real-world energy data.
"""

from .sources.gem import get_generators_from_gem, add_gem_generators_to_network
from .loaders.cache import DataCache

__all__ = [
    # GEM (Global Energy Monitor) functions
    "get_generators_from_gem",
    "add_gem_generators_to_network",
    
    # Caching utilities
    "DataCache",
]
