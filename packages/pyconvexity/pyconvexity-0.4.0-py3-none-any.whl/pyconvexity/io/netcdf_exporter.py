"""
NetCDF exporter for PyConvexity energy system models.
Exports networks to PyPSA NetCDF format using existing PyPSA infrastructure.
"""

import logging
from typing import Dict, Any, Optional, Callable
from pathlib import Path

# Import existing PyPSA functionality from pyconvexity
from pyconvexity.core.database import open_connection
from pyconvexity.solvers.pypsa import build_pypsa_network

logger = logging.getLogger(__name__)

class NetCDFModelExporter:
    """Export network model to PyPSA NetCDF format"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_to_netcdf(
        self,
        db_path: str,
        network_id: int,
        output_path: str,
        scenario_id: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Export network from database to PyPSA NetCDF format
        
        This method leverages the existing pyconvexity PyPSA infrastructure to build
        a network from the database and then export it to NetCDF format.
        
        Args:
            db_path: Path to the database file
            network_id: ID of the network to export
            output_path: Path where to save the NetCDF file
            scenario_id: Optional scenario ID (uses master scenario if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with export results and statistics
        """
        try:
            if progress_callback:
                progress_callback(0, "Starting NetCDF export...")
            
            # Build PyPSA network from database using existing infrastructure
            if progress_callback:
                progress_callback(10, "Building PyPSA network from database...")
            
            network = build_pypsa_network(
                db_path=db_path,
                network_id=network_id,
                scenario_id=scenario_id,
                progress_callback=self._wrap_progress_callback(progress_callback, 10, 80)
            )
            
            if progress_callback:
                progress_callback(80, "Exporting to NetCDF...")
            
            # Export to NetCDF using PyPSA's built-in method
            network.export_to_netcdf(output_path)
            
            if progress_callback:
                progress_callback(100, "NetCDF export completed")
            
            # Get statistics
            stats = self._get_network_stats(network)
            
            return {
                "success": True,
                "message": f"Network exported to NetCDF: {output_path}",
                "output_path": output_path,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"NetCDF export failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Export failed: {str(e)}")
            raise
    
    def export_to_csv(
        self,
        db_path: str,
        network_id: int,
        output_directory: str,
        scenario_id: Optional[int] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Export network from database to PyPSA CSV format
        
        Args:
            db_path: Path to the database file
            network_id: ID of the network to export
            output_directory: Directory where to save CSV files
            scenario_id: Optional scenario ID (uses master scenario if None)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with export results and statistics
        """
        try:
            if progress_callback:
                progress_callback(0, "Starting CSV export...")
            
            # Ensure output directory exists
            Path(output_directory).mkdir(parents=True, exist_ok=True)
            
            # Build PyPSA network from database using existing infrastructure
            if progress_callback:
                progress_callback(10, "Building PyPSA network from database...")
            
            network = build_pypsa_network(
                db_path=db_path,
                network_id=network_id,
                scenario_id=scenario_id,
                progress_callback=self._wrap_progress_callback(progress_callback, 10, 80)
            )
            
            if progress_callback:
                progress_callback(80, "Exporting to CSV...")
            
            # Export to CSV using PyPSA's built-in method
            network.export_to_csv_folder(output_directory)
            
            if progress_callback:
                progress_callback(100, "CSV export completed")
            
            # Get statistics
            stats = self._get_network_stats(network)
            
            return {
                "success": True,
                "message": f"Network exported to CSV: {output_directory}",
                "output_directory": output_directory,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Export failed: {str(e)}")
            raise
    
    def _wrap_progress_callback(
        self, 
        callback: Optional[Callable[[int, str], None]], 
        start_percent: int, 
        end_percent: int
    ) -> Optional[Callable[[int, str], None]]:
        """
        Wrap a progress callback to map progress from one range to another
        
        Args:
            callback: Original callback function
            start_percent: Starting percentage for the wrapped range
            end_percent: Ending percentage for the wrapped range
            
        Returns:
            Wrapped callback function or None if original callback is None
        """
        if callback is None:
            return None
        
        def wrapped_callback(progress: Optional[int], message: Optional[str]):
            if progress is not None:
                # Map progress from 0-100 to start_percent-end_percent
                mapped_progress = start_percent + (progress * (end_percent - start_percent) // 100)
                callback(mapped_progress, message)
            else:
                callback(progress, message)
        
        return wrapped_callback
    
    def _get_network_stats(self, network: 'pypsa.Network') -> Dict[str, int]:
        """Get component counts from the network"""
        return {
            "buses": len(network.buses),
            "generators": len(network.generators) if hasattr(network, 'generators') else 0,
            "loads": len(network.loads) if hasattr(network, 'loads') else 0,
            "lines": len(network.lines) if hasattr(network, 'lines') else 0,
            "links": len(network.links) if hasattr(network, 'links') else 0,
            "storage_units": len(network.storage_units) if hasattr(network, 'storage_units') else 0,
            "stores": len(network.stores) if hasattr(network, 'stores') else 0,
            "carriers": len(network.carriers) if hasattr(network, 'carriers') else 0,
            "snapshots": len(network.snapshots) if hasattr(network, 'snapshots') else 0,
        }
