"""
Input/Output operations for PyConvexity.

Provides functionality for importing and exporting energy system models
in various formats including Excel, CSV, and other data formats.
"""

# Import main classes for easy access
try:
    from .excel_exporter import ExcelModelExporter
    from .excel_importer import ExcelModelImporter
    
    __all__ = [
        "ExcelModelExporter",
        "ExcelModelImporter"
    ]
except ImportError:
    # Excel dependencies not available
    __all__ = []

# NetCDF I/O functionality
try:
    from .netcdf_exporter import NetCDFModelExporter
    from .netcdf_importer import NetCDFModelImporter
    
    __all__.extend([
        "NetCDFModelExporter",
        "NetCDFModelImporter"
    ])
except ImportError:
    # NetCDF/PyPSA dependencies not available
    pass
