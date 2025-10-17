"""
NetCDF importer for PyConvexity energy system models.
Imports PyPSA NetCDF files into PyConvexity database format.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Callable, Tuple, List
from pathlib import Path
import random
import math

# Import functions directly from pyconvexity
from pyconvexity.core.database import open_connection, create_database_with_schema
from pyconvexity.core.types import (
    StaticValue, CreateNetworkRequest, CreateComponentRequest
)
from pyconvexity.core.errors import PyConvexityError as DbError, ValidationError
from pyconvexity.models import (
    create_network, create_carrier, insert_component, set_static_attribute,
    get_bus_name_to_id_map, set_timeseries_attribute, get_component_type, get_attribute,
    get_network_time_periods
)
from pyconvexity.validation import get_validation_rule
from pyconvexity.timeseries import set_timeseries

logger = logging.getLogger(__name__)

class NetCDFModelImporter:
    """Import PyPSA NetCDF files into PyConvexity database format"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Set random seed for reproducible coordinate generation
        random.seed(42)
        np.random.seed(42)
        self._used_names = set()  # Global registry of all used names
    
    def import_netcdf_to_database(
        self, 
        netcdf_path: str, 
        db_path: str, 
        network_name: str,
        network_description: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        strict_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Import a PyPSA NetCDF file into a new database.
        
        Args:
            netcdf_path: Path to the PyPSA NetCDF file
            db_path: Path where to create the database
            network_name: Name for the imported network
            network_description: Optional description
            progress_callback: Optional callback for progress updates (progress: int, message: str)
            strict_validation: Whether to skip undefined attributes rather than failing completely.
                               If True, will fail on any attribute not defined in the database schema.
                               If False (default), will skip undefined attributes with warnings.
        
        Returns:
            Dictionary with import results and statistics
        """
        try:
            if progress_callback:
                progress_callback(0, "Starting NetCDF import...")
            
            # Import PyPSA
            pypsa = self._import_pypsa()
            
            if progress_callback:
                progress_callback(5, "Loading PyPSA network from NetCDF...")
            
            # Load the PyPSA network
            network = pypsa.Network(netcdf_path)
            
            if progress_callback:
                progress_callback(15, f"Loaded network: {len(network.buses)} buses, {len(network.generators)} generators")
            
            # Use the shared import logic
            return self._import_network_to_database(
                network=network,
                db_path=db_path,
                network_name=network_name,
                network_description=network_description,
                progress_callback=progress_callback,
                strict_validation=strict_validation,
                import_source="NetCDF",
                netcdf_path=netcdf_path
            )
            
        except Exception as e:
            self.logger.error(f"Error importing NetCDF: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Error: {str(e)}")
            raise

    def import_csv_to_database(
        self, 
        csv_directory: str, 
        db_path: str, 
        network_name: str,
        network_description: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        strict_validation: bool = False
    ) -> Dict[str, Any]:
        """
        Import a PyPSA network from CSV files into a new database.
        
        Args:
            csv_directory: Path to the directory containing PyPSA CSV files
            db_path: Path where to create the database
            network_name: Name for the imported network
            network_description: Optional description
            progress_callback: Optional callback for progress updates (progress: int, message: str)
            strict_validation: Whether to skip undefined attributes rather than failing
            
        Returns:
            Dictionary with import results and statistics
        """
        try:
            if progress_callback:
                progress_callback(0, "Starting PyPSA CSV import...")
            
            # Import PyPSA
            pypsa = self._import_pypsa()
            
            if progress_callback:
                progress_callback(5, "Validating CSV files...")
            
            # Validate CSV directory and files before attempting import
            self._validate_csv_directory(csv_directory)
            
            if progress_callback:
                progress_callback(10, "Loading PyPSA network from CSV files...")
            
            # Load the PyPSA network from CSV directory
            network = pypsa.Network()
            
            try:
                network.import_from_csv_folder(csv_directory)
            except Exception as e:
                # Provide more helpful error message
                error_msg = f"PyPSA CSV import failed: {str(e)}"
                if "'name'" in str(e):
                    error_msg += "\n\nThis usually means one of your CSV files is missing a 'name' column. PyPSA CSV files require:\n"
                    error_msg += "- All component CSV files (buses.csv, generators.csv, etc.) must have a 'name' column as the first column\n"
                    error_msg += "- The 'name' column should contain unique identifiers for each component\n"
                    error_msg += "- Check that your CSV files follow the PyPSA CSV format specification"
                elif "KeyError" in str(e):
                    error_msg += f"\n\nThis indicates a required column is missing from one of your CSV files. "
                    error_msg += "Please ensure your CSV files follow the PyPSA format specification."
                
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            if progress_callback:
                progress_callback(20, f"Loaded network: {len(network.buses)} buses, {len(network.generators)} generators")
            
            # Use the shared import logic
            return self._import_network_to_database(
                network=network,
                db_path=db_path,
                network_name=network_name,
                network_description=network_description,
                progress_callback=progress_callback,
                strict_validation=strict_validation,
                import_source="CSV"
            )
            
        except Exception as e:
            self.logger.error(f"Error importing PyPSA CSV: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Error: {str(e)}")
            raise

    def _import_pypsa(self):
        """Import PyPSA with standard error handling."""
        try:
            import pypsa
            return pypsa
        except ImportError as e:
            self.logger.error(f"Failed to import PyPSA: {e}", exc_info=True)
            raise ImportError(
                "PyPSA is not installed or could not be imported. "
                "Please ensure it is installed correctly in the environment."
            ) from e
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during PyPSA import: {e}", exc_info=True)
            raise

    def _validate_csv_directory(self, csv_directory: str) -> None:
        """Validate that the CSV directory contains valid PyPSA CSV files"""
        import os
        import pandas as pd
        
        csv_path = Path(csv_directory)
        if not csv_path.exists():
            raise ValueError(f"CSV directory does not exist: {csv_directory}")
        
        if not csv_path.is_dir():
            raise ValueError(f"Path is not a directory: {csv_directory}")
        
        # Find CSV files
        csv_files = list(csv_path.glob("*.csv"))
        if not csv_files:
            raise ValueError(f"No CSV files found in directory: {csv_directory}")
        
        # Check each CSV file for basic validity
        component_files = ['buses.csv', 'generators.csv', 'loads.csv', 'lines.csv', 'links.csv', 'storage_units.csv', 'stores.csv']
        required_files = ['buses.csv']  # At minimum, we need buses
        
        # Check for required files
        existing_files = [f.name for f in csv_files]
        missing_required = [f for f in required_files if f not in existing_files]
        if missing_required:
            raise ValueError(f"Missing required CSV files: {missing_required}")
        
        # Validate each component CSV file that exists
        for csv_file in csv_files:
            if csv_file.name in component_files:
                try:
                    df = pd.read_csv(csv_file, nrows=0)  # Just read headers
                    if 'name' not in df.columns:
                        raise ValueError(f"CSV file '{csv_file.name}' is missing required 'name' column. Found columns: {list(df.columns)}")
                except Exception as e:
                    raise ValueError(f"Error reading CSV file '{csv_file.name}': {str(e)}")

    def _import_network_to_database(
        self,
        network,
        db_path: str,
        network_name: str,
        network_description: Optional[str] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        strict_validation: bool = False,
        import_source: str = "PyPSA",
        netcdf_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Shared logic to import a PyPSA network object into a database.
        This method is used by both NetCDF and CSV import functions.
        """
        try:
            if progress_callback:
                progress_callback(0, "Starting network import...")
            
            # Create the database with schema using atomic utility
            create_database_with_schema(db_path)
            
            if progress_callback:
                progress_callback(5, "Database schema created")
            
            # Connect to database
            conn = open_connection(db_path)
            
            try:
                # Load companion location CSV if available (for NetCDF imports only)
                location_map = None
                if import_source == "NetCDF" and netcdf_path:
                    location_map = self._detect_and_load_location_csv(netcdf_path)
                
                # Create the network record
                network_id = self._create_network_record(
                    conn, network, network_name, network_description
                )
                
                if progress_callback:
                    progress_callback(10, f"Created network record (ID: {network_id})")
                
                # Verify that the "Main" scenario was created by the database trigger
                cursor = conn.execute("SELECT id, name, is_master FROM scenarios WHERE network_id = ?", (network_id,))
                scenarios = cursor.fetchall()
                if scenarios:
                    main_scenario = next((s for s in scenarios if s[2] == True), None)  # is_master = True
                    if not main_scenario:
                        self.logger.warning(f"No master scenario found in scenarios: {scenarios}")
                else:
                    self.logger.error(f"No scenarios found after network creation - database trigger may have failed")
                
                # Create network time periods from PyPSA snapshots
                self._create_network_time_periods(conn, network, network_id)
                
                if progress_callback:
                    progress_callback(15, f"Created network time periods")
                
                # Import carriers
                carriers_count = self._import_carriers(conn, network, network_id)
                
                if progress_callback:
                    progress_callback(20, f"Imported {carriers_count} carriers")
                
                # Import buses
                buses_count = self._import_buses(conn, network, network_id, strict_validation)
                
                if progress_callback:
                    progress_callback(25, f"Imported {buses_count} buses")
                
                # Calculate scatter radius for non-bus components based on bus separation
                bus_coordinates = self._get_bus_coordinates(conn, network_id)
                scatter_radius = self._calculate_bus_separation_radius(bus_coordinates)
                
                # Import generators
                generators_count = self._import_generators(conn, network, network_id, strict_validation, scatter_radius, location_map)
                
                if progress_callback:
                    progress_callback(30, f"Imported {generators_count} generators")
                
                # Import loads
                loads_count = self._import_loads(conn, network, network_id, strict_validation, scatter_radius, location_map)
                
                if progress_callback:
                    progress_callback(35, f"Imported {loads_count} loads")
                
                # Import lines
                lines_count = self._import_lines(conn, network, network_id, strict_validation, location_map)
                
                if progress_callback:
                    progress_callback(40, f"Imported {lines_count} lines")
                
                # Import links
                links_count = self._import_links(conn, network, network_id, strict_validation, location_map)
                
                if progress_callback:
                    progress_callback(45, f"Imported {links_count} links")
                
                # Import storage units
                storage_units_count = self._import_storage_units(conn, network, network_id, strict_validation, scatter_radius, location_map)
                
                if progress_callback:
                    progress_callback(50, f"Imported {storage_units_count} storage units")
                
                # Import stores
                stores_count = self._import_stores(conn, network, network_id, strict_validation, scatter_radius, location_map)
                
                if progress_callback:
                    progress_callback(55, f"Imported {stores_count} stores")
                
                conn.commit()
                
                if progress_callback:
                    progress_callback(100, "Import completed successfully")
                
                # Collect final statistics
                stats = {
                    "network_id": network_id,
                    "network_name": network_name,
                    "carriers": carriers_count,
                    "buses": buses_count,
                    "generators": generators_count,
                    "loads": loads_count,
                    "lines": lines_count,
                    "links": links_count,
                    "storage_units": storage_units_count,
                    "stores": stores_count,
                    "total_components": (buses_count + generators_count + loads_count + 
                                       lines_count + links_count + storage_units_count + stores_count),
                    "snapshots": len(network.snapshots) if hasattr(network, 'snapshots') else 0,
                }
                
                return {
                    "success": True,
                    "message": f"Network imported successfully from {import_source}",
                    "db_path": db_path,
                    "stats": stats
                }
                
            finally:
                conn.close()
                
        except Exception as e:
            self.logger.error(f"Error importing network: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Error: {str(e)}")
            raise

    # Helper methods for the import process
    # Note: These are simplified versions of the methods from the original netcdf_importer.py
    # The full implementation would include all the detailed import logic for each component type
    
    def _extract_datetime_snapshots(self, network) -> pd.DatetimeIndex:
        """Extract datetime snapshots from a PyPSA network"""
        if not hasattr(network, 'snapshots') or len(network.snapshots) == 0:
            self.logger.warning("No snapshots found in PyPSA network")
            return pd.DatetimeIndex([])
        
        snapshots = network.snapshots
        
        try:
            # Try direct conversion first (works for simple DatetimeIndex)
            return pd.to_datetime(snapshots)
        except (TypeError, ValueError) as e:
            # Handle MultiIndex case
            if hasattr(snapshots, 'nlevels') and snapshots.nlevels > 1:
                # Try to use the timesteps attribute if available (common in multi-period networks)
                if hasattr(network, 'timesteps') and isinstance(network.timesteps, pd.DatetimeIndex):
                    return network.timesteps
                
                # Try to extract datetime from the last level of the MultiIndex
                try:
                    # Get the last level (usually the timestep level)
                    last_level = snapshots.get_level_values(snapshots.nlevels - 1)
                    datetime_snapshots = pd.to_datetime(last_level)
                    return datetime_snapshots
                except Exception as multi_e:
                    self.logger.warning(f"Failed to extract datetime from MultiIndex: {multi_e}")
            
            # Final fallback: create a default hourly range
            self.logger.warning("Could not extract datetime snapshots, creating default hourly range")
            default_start = pd.Timestamp('2024-01-01 00:00:00')
            default_end = pd.Timestamp('2024-01-01 23:59:59')
            return pd.date_range(start=default_start, end=default_end, freq='H')

    def _create_network_record(
        self, 
        conn, 
        network, 
        network_name: str,
        network_description: Optional[str] = None
    ) -> int:
        """Create the network record and return network ID"""
        
        # Extract time information from PyPSA network using our robust helper
        snapshots = self._extract_datetime_snapshots(network)
        
        if len(snapshots) > 0:
            time_start = snapshots.min().strftime('%Y-%m-%d %H:%M:%S')
            time_end = snapshots.max().strftime('%Y-%m-%d %H:%M:%S')
            
            # Try to infer time interval
            if len(snapshots) > 1:
                freq = pd.infer_freq(snapshots)
                time_interval = freq or 'H'  # Default to hourly if can't infer
            else:
                time_interval = 'H'
        else:
            # Default time range if no snapshots
            time_start = '2024-01-01 00:00:00'
            time_end = '2024-01-01 23:59:59'
            time_interval = 'H'
        
        description = network_description or f"Imported from PyPSA NetCDF on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        request = CreateNetworkRequest(
            name=network_name,
            description=description,
            time_resolution=time_interval,
            start_time=time_start,
            end_time=time_end
        )
        return create_network(conn, request)

    def _create_network_time_periods(self, conn, network, network_id: int) -> None:
        """Create network time periods from PyPSA snapshots using optimized approach"""
        # Use our robust helper to extract datetime snapshots
        snapshots = self._extract_datetime_snapshots(network)
        
        if len(snapshots) == 0:
            self.logger.warning("No valid snapshots found in PyPSA network, skipping time periods creation")
            return
        
        # Insert optimized time periods metadata
        period_count = len(snapshots)
        start_timestamp = int(snapshots[0].timestamp())
        
        # Calculate interval in seconds
        if len(snapshots) > 1:
            interval_seconds = int((snapshots[1] - snapshots[0]).total_seconds())
        else:
            interval_seconds = 3600  # Default to hourly
        
        conn.execute("""
            INSERT INTO network_time_periods (network_id, period_count, start_timestamp, interval_seconds)
            VALUES (?, ?, ?, ?)
        """, (network_id, period_count, start_timestamp, interval_seconds))

    # Placeholder methods - in a full implementation, these would contain
    # the detailed import logic from the original netcdf_importer.py
    
    def _import_carriers(self, conn, network, network_id: int) -> int:
        """Import carriers from PyPSA network, discovering from both network and component levels"""
        count = 0
        created_carriers = set()
        
        # Discover all carriers from components (not just n.carriers table)
        all_carriers = set()
        
        # Get carriers from network.carriers table if it exists
        if hasattr(network, 'carriers') and not network.carriers.empty:
            all_carriers.update(network.carriers.index)
        
        # Get carriers from generators
        if hasattr(network, 'generators') and not network.generators.empty and 'carrier' in network.generators.columns:
            component_carriers = set(network.generators.carrier.dropna().unique())
            all_carriers.update(component_carriers)
        
        # Get carriers from storage units
        if hasattr(network, 'storage_units') and not network.storage_units.empty and 'carrier' in network.storage_units.columns:
            component_carriers = set(network.storage_units.carrier.dropna().unique())
            all_carriers.update(component_carriers)
        
        # Get carriers from stores
        if hasattr(network, 'stores') and not network.stores.empty and 'carrier' in network.stores.columns:
            component_carriers = set(network.stores.carrier.dropna().unique())
            all_carriers.update(component_carriers)
        
        # Get carriers from loads (if they have carriers)
        if hasattr(network, 'loads') and not network.loads.empty and 'carrier' in network.loads.columns:
            component_carriers = set(network.loads.carrier.dropna().unique())
            all_carriers.update(component_carriers)
        
        # Get carriers from buses (if they have carriers)
        if hasattr(network, 'buses') and not network.buses.empty and 'carrier' in network.buses.columns:
            component_carriers = set(network.buses.carrier.dropna().unique())
            all_carriers.update(component_carriers)
        
        # Convert to sorted list for consistent ordering
        all_carriers = sorted(list(all_carriers))
        
        # Define a color palette similar to the Python code
        color_palette = [
            '#1f77b4',  # C0 - blue
            '#ff7f0e',  # C1 - orange
            '#2ca02c',  # C2 - green
            '#d62728',  # C3 - red
            '#9467bd',  # C4 - purple
            '#8c564b',  # C5 - brown
            '#e377c2',  # C6 - pink
            '#7f7f7f',  # C7 - gray
            '#bcbd22',  # C8 - olive
            '#17becf',  # C9 - cyan
            '#aec7e8',  # light blue
            '#ffbb78',  # light orange
            '#98df8a',  # light green
            '#ff9896',  # light red
            '#c5b0d5',  # light purple
        ]
        
        # Create carriers from discovered list
        for i, carrier_name in enumerate(all_carriers):
            # Get carrier data from network.carriers if available
            carrier_data = {}
            if hasattr(network, 'carriers') and not network.carriers.empty and carrier_name in network.carriers.index:
                # Use .iloc with index position to avoid fragmentation
                carrier_idx = network.carriers.index.get_loc(carrier_name)
                carrier_data = network.carriers.iloc[carrier_idx]
            
            # Extract attributes with defaults
            co2_emissions = carrier_data.get('co2_emissions', 0.0)
            
            # Use color from network.carriers if available, otherwise assign from palette
            if 'color' in carrier_data and pd.notna(carrier_data['color']):
                color = carrier_data['color']
            else:
                color = color_palette[i % len(color_palette)]
            
            nice_name = carrier_data.get('nice_name', None)
            
            # Create the carrier
            create_carrier(conn, network_id, carrier_name, co2_emissions, color, nice_name)
            created_carriers.add(carrier_name)
            count += 1
        
        # Ensure we have essential carriers for bus validation
        # Buses can only use AC, DC, heat, or gas carriers according to database constraints
        essential_carriers = {
            'AC': {'co2_emissions': 0.0, 'color': '#3498db', 'nice_name': 'AC Electricity'},
            'electricity': {'co2_emissions': 0.0, 'color': '#2ecc71', 'nice_name': 'Electricity'}
        }
        
        for carrier_name, carrier_props in essential_carriers.items():
            if carrier_name not in created_carriers:
                create_carrier(
                    conn, 
                    network_id, 
                    carrier_name, 
                    carrier_props['co2_emissions'], 
                    carrier_props['color'], 
                    carrier_props['nice_name']
                )
                created_carriers.add(carrier_name)
                count += 1
        
        return count

    def _import_buses(self, conn, network, network_id: int, strict_validation: bool) -> int:
        """Import buses from PyPSA network"""
        count = 0
        
        if not hasattr(network, 'buses') or network.buses.empty:
            return count
            
        for bus_name, bus_data in network.buses.iterrows():
            try:
                # Generate a unique name for this bus
                unique_name = self._generate_unique_name(str(bus_name), 'BUS')
                
                # Extract and log coordinate data for debugging
                x_value = bus_data.get('x', None)
                y_value = bus_data.get('y', None)
                self.logger.debug(f"Bus '{bus_name}' -> '{unique_name}': x={x_value} (type: {type(x_value)}), y={y_value} (type: {type(y_value)})")
                
                # Handle NaN/None values properly
                longitude = None if x_value is None or (hasattr(x_value, '__iter__') and len(str(x_value)) == 0) else float(x_value) if x_value != '' else None
                latitude = None if y_value is None or (hasattr(y_value, '__iter__') and len(str(y_value)) == 0) else float(y_value) if y_value != '' else None
                
                # Additional check for pandas NaN values
                if longitude is not None and pd.isna(longitude):
                    longitude = None
                if latitude is not None and pd.isna(latitude):
                    latitude = None
                
                # Get or create carrier
                carrier_name = bus_data.get('carrier', 'AC')
                carrier_id = self._get_or_create_carrier(conn, network_id, carrier_name)
                
                # Create component record using atomic function
                # Note: PyPSA 'x'/'y' coordinates are mapped to 'longitude'/'latitude' columns here
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='BUS',
                    name=unique_name,  # Use globally unique name
                    latitude=latitude,  # PyPSA y -> latitude
                    longitude=longitude,  # PyPSA x -> longitude
                    carrier_id=carrier_id
                )
                component_id = insert_component(conn, request)
                
                # Import bus attributes (location/coordinate data is handled above, not as attributes)
                self._import_component_attributes(conn, component_id, bus_data, 'BUS', strict_validation)
                
                # Import timeseries attributes for buses
                self._import_component_timeseries(conn, network, component_id, bus_name, 'BUS', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import bus {bus_name}: {e}")
                continue
        
        return count

    # Additional placeholder methods for other component types
    def _import_generators(self, conn, network, network_id: int, strict_validation: bool, scatter_radius: float, location_map) -> int:
        """Import generators from PyPSA network"""
        count = 0
        
        if not hasattr(network, 'generators') or network.generators.empty:
            return count
            
        # Get bus name to ID mapping
        bus_name_to_id = get_bus_name_to_id_map(conn, network_id)
        
        # Get master scenario ID
        master_scenario_id = self._get_master_scenario_id(conn, network_id)
        
        for gen_name, gen_data in network.generators.iterrows():
            try:
                # Get bus connection
                bus_name = gen_data.get('bus')
                bus_id = bus_name_to_id.get(bus_name) if bus_name else None
                
                if not bus_id:
                    self.logger.warning(f"Generator {gen_name}: bus '{bus_name}' not found, skipping")
                    continue
                
                # Get or create carrier
                carrier_name = gen_data.get('carrier', 'AC')
                carrier_id = self._get_or_create_carrier(conn, network_id, carrier_name)
                
                # Generate coordinates near the bus
                latitude, longitude = self._generate_component_coordinates(
                    conn, bus_id, scatter_radius, location_map, gen_name
                )
                
                # Create component record
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='GENERATOR',
                    name=str(gen_name),
                    latitude=latitude,
                    longitude=longitude,
                    carrier_id=carrier_id,
                    bus_id=bus_id
                )
                component_id = insert_component(conn, request)
                
                # Import generator attributes
                self._import_component_attributes(conn, component_id, gen_data, 'GENERATOR', strict_validation)
                
                # Import timeseries attributes for generators
                self._import_component_timeseries(conn, network, component_id, gen_name, 'GENERATOR', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import generator {gen_name}: {e}")
                continue
        
        return count

    def _import_loads(self, conn, network, network_id: int, strict_validation: bool, scatter_radius: float, location_map) -> int:
        """Import loads from PyPSA network"""
        count = 0
        
        if not hasattr(network, 'loads') or network.loads.empty:
            return count
            
        bus_map = get_bus_name_to_id_map(conn, network_id)
        bus_coords = self._get_bus_coordinates_map(conn, network_id)
        
        # Count components per bus for better distribution
        components_per_bus = {}
        for load_name, load_data in network.loads.iterrows():
            bus_name = load_data['bus']
            components_per_bus[bus_name] = components_per_bus.get(bus_name, 0) + 1
        
        bus_component_counters = {}
        
        for load_name, load_data in network.loads.iterrows():
            try:
                bus_id = bus_map.get(load_data['bus'])
                if bus_id is None:
                    self.logger.warning(f"Bus '{load_data['bus']}' not found for load '{load_name}'")
                    continue
                
                # Generate a unique name for this load
                unique_name = self._generate_unique_name(str(load_name), 'LOAD')
                
                # Try to get coordinates from CSV first, then fall back to scattered coordinates
                latitude, longitude = None, None
                
                # Check CSV coordinates first
                csv_coords = self._get_csv_coordinates(unique_name, location_map)
                if csv_coords:
                    latitude, longitude = csv_coords
                elif bus_id in bus_coords:
                    # Fall back to scattered coordinates around the connected bus
                    bus_lat, bus_lon = bus_coords[bus_id]
                    bus_name = load_data['bus']
                    
                    # Get component index for this bus
                    component_index = bus_component_counters.get(bus_name, 0)
                    bus_component_counters[bus_name] = component_index + 1
                    
                    latitude, longitude = self._generate_scattered_coordinates(
                        bus_lat, bus_lon, scatter_radius,
                        components_per_bus[bus_name], component_index
                    )
                
                # Get carrier ID if carrier is specified
                carrier_id = None
                if 'carrier' in load_data and pd.notna(load_data['carrier']):
                    carrier_id = self._get_or_create_carrier(conn, network_id, load_data['carrier'])
                
                # Create component record using atomic function
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='LOAD',
                    name=unique_name,  # Use globally unique name
                    bus_id=bus_id,
                    carrier_id=carrier_id,
                    latitude=latitude,
                    longitude=longitude
                )
                component_id = insert_component(conn, request)
                
                # Import load attributes
                self._import_component_attributes(conn, component_id, load_data, 'LOAD', strict_validation)
                
                # Import timeseries attributes for loads
                self._import_component_timeseries(conn, network, component_id, load_name, 'LOAD', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import load {load_name}: {e}")
                continue
        
        return count

    def _import_lines(self, conn, network, network_id: int, strict_validation: bool, location_map) -> int:
        """Import lines from PyPSA network"""
        count = 0
        name_counter = {}  # Track duplicate names
        
        if not hasattr(network, 'lines') or network.lines.empty:
            return count
            
        bus_map = get_bus_name_to_id_map(conn, network_id)
        
        for line_name, line_data in network.lines.iterrows():
            try:
                bus0_id = bus_map.get(line_data['bus0'])
                bus1_id = bus_map.get(line_data['bus1'])
                
                if bus0_id is None or bus1_id is None:
                    self.logger.warning(f"Bus not found for line '{line_name}': bus0='{line_data['bus0']}', bus1='{line_data['bus1']}'")
                    continue
                
                # Handle duplicate names by appending counter
                unique_name = line_name
                if line_name in name_counter:
                    name_counter[line_name] += 1
                    unique_name = f"{line_name}_{name_counter[line_name]}"
                    self.logger.warning(f"Duplicate line name '{line_name}' renamed to '{unique_name}'")
                else:
                    name_counter[line_name] = 0
                
                # Check for CSV coordinates
                latitude, longitude = None, None
                csv_coords = self._get_csv_coordinates(unique_name, location_map)
                if csv_coords:
                    latitude, longitude = csv_coords
                
                # Lines always use AC carrier
                carrier_id = self._get_or_create_carrier(conn, network_id, 'AC')
                
                # Create component record using atomic function
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='LINE',
                    name=unique_name,  # Use deduplicated name
                    bus0_id=bus0_id,
                    bus1_id=bus1_id,
                    carrier_id=carrier_id,
                    latitude=latitude,
                    longitude=longitude
                )
                component_id = insert_component(conn, request)
                
                # Import line attributes
                self._import_component_attributes(conn, component_id, line_data, 'LINE', strict_validation)
                
                # Import timeseries attributes for lines
                self._import_component_timeseries(conn, network, component_id, line_name, 'LINE', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import line {line_name}: {e}")
                continue
        
        return count

    def _import_links(self, conn, network, network_id: int, strict_validation: bool, location_map) -> int:
        """Import links from PyPSA network"""
        count = 0
        
        if not hasattr(network, 'links') or network.links.empty:
            return count
            
        bus_map = get_bus_name_to_id_map(conn, network_id)
        
        for link_name, link_data in network.links.iterrows():
            try:
                bus0_id = bus_map.get(link_data['bus0'])
                bus1_id = bus_map.get(link_data['bus1'])
                
                if bus0_id is None or bus1_id is None:
                    self.logger.warning(f"Bus not found for link '{link_name}': bus0='{link_data['bus0']}', bus1='{link_data['bus1']}'")
                    continue
                
                # Generate a unique name for this link
                unique_name = self._generate_unique_name(str(link_name), 'LINK')
                
                # Check for CSV coordinates
                latitude, longitude = None, None
                csv_coords = self._get_csv_coordinates(unique_name, location_map)
                if csv_coords:
                    latitude, longitude = csv_coords
                
                # Get carrier ID if carrier is specified
                carrier_id = None
                if 'carrier' in link_data and pd.notna(link_data['carrier']):
                    carrier_id = self._get_or_create_carrier(conn, network_id, link_data['carrier'])
                else:
                    # Default to DC for links
                    carrier_id = self._get_or_create_carrier(conn, network_id, 'DC')
                
                # Create component record using atomic function
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='LINK',
                    name=unique_name,  # Use globally unique name
                    bus0_id=bus0_id,
                    bus1_id=bus1_id,
                    carrier_id=carrier_id,
                    latitude=latitude,
                    longitude=longitude
                )
                component_id = insert_component(conn, request)
                
                # Import link attributes
                self._import_component_attributes(conn, component_id, link_data, 'LINK', strict_validation)
                
                # Import timeseries attributes for links
                self._import_component_timeseries(conn, network, component_id, link_name, 'LINK', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import link {link_name}: {e}")
                continue
        
        return count

    def _import_storage_units(self, conn, network, network_id: int, strict_validation: bool, scatter_radius: float, location_map) -> int:
        """Import storage units from PyPSA network"""
        count = 0
        
        if not hasattr(network, 'storage_units') or network.storage_units.empty:
            return count
            
        bus_map = get_bus_name_to_id_map(conn, network_id)
        bus_coords = self._get_bus_coordinates_map(conn, network_id)
        
        # Count components per bus for better distribution
        components_per_bus = {}
        for su_name, su_data in network.storage_units.iterrows():
            bus_name = su_data['bus']
            components_per_bus[bus_name] = components_per_bus.get(bus_name, 0) + 1
        
        bus_component_counters = {}
        
        for su_name, su_data in network.storage_units.iterrows():
            try:
                bus_id = bus_map.get(su_data['bus'])
                if bus_id is None:
                    self.logger.warning(f"Bus '{su_data['bus']}' not found for storage unit '{su_name}'")
                    continue
                
                # Generate a unique name for this storage unit
                unique_name = self._generate_unique_name(str(su_name), 'STORAGE_UNIT')
                
                # Try to get coordinates from CSV first, then fall back to scattered coordinates
                latitude, longitude = None, None
                
                # Check CSV coordinates first
                csv_coords = self._get_csv_coordinates(unique_name, location_map)
                if csv_coords:
                    latitude, longitude = csv_coords
                elif bus_id in bus_coords:
                    # Fall back to scattered coordinates around the connected bus
                    bus_lat, bus_lon = bus_coords[bus_id]
                    bus_name = su_data['bus']
                    
                    # Get component index for this bus
                    component_index = bus_component_counters.get(bus_name, 0)
                    bus_component_counters[bus_name] = component_index + 1
                    
                    latitude, longitude = self._generate_scattered_coordinates(
                        bus_lat, bus_lon, scatter_radius,
                        components_per_bus[bus_name], component_index
                    )
                
                # Get carrier ID if carrier is specified
                carrier_id = None
                if 'carrier' in su_data and pd.notna(su_data['carrier']):
                    carrier_id = self._get_or_create_carrier(conn, network_id, su_data['carrier'])
                
                # Create component record using atomic function
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='STORAGE_UNIT',
                    name=unique_name,  # Use globally unique name
                    bus_id=bus_id,
                    carrier_id=carrier_id,
                    latitude=latitude,
                    longitude=longitude
                )
                component_id = insert_component(conn, request)
                
                # Import storage unit attributes
                self._import_component_attributes(conn, component_id, su_data, 'STORAGE_UNIT', strict_validation)
                
                # Import timeseries attributes for storage units
                self._import_component_timeseries(conn, network, component_id, su_name, 'STORAGE_UNIT', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import storage unit {su_name}: {e}")
                continue
        
        return count

    def _import_stores(self, conn, network, network_id: int, strict_validation: bool, scatter_radius: float, location_map) -> int:
        """Import stores from PyPSA network"""
        count = 0
        name_counter = {}  # Track duplicate names
        
        if not hasattr(network, 'stores') or network.stores.empty:
            return count
            
        bus_map = get_bus_name_to_id_map(conn, network_id)
        bus_coords = self._get_bus_coordinates_map(conn, network_id)
        
        # Count components per bus for better distribution
        components_per_bus = {}
        for store_name, store_data in network.stores.iterrows():
            bus_name = store_data['bus']
            components_per_bus[bus_name] = components_per_bus.get(bus_name, 0) + 1
        
        bus_component_counters = {}  # Track how many components we've placed at each bus
        
        for store_name, store_data in network.stores.iterrows():
            try:
                bus_id = bus_map.get(store_data['bus'])
                if bus_id is None:
                    self.logger.warning(f"Bus '{store_data['bus']}' not found for store '{store_name}'")
                    continue
                
                # Handle duplicate names by appending counter
                unique_name = store_name
                if store_name in name_counter:
                    name_counter[store_name] += 1
                    unique_name = f"{store_name}_{name_counter[store_name]}"
                    self.logger.warning(f"Duplicate store name '{store_name}' renamed to '{unique_name}'")
                else:
                    name_counter[store_name] = 0
                
                # Try to get coordinates from CSV first, then fall back to scattered coordinates
                latitude, longitude = None, None
                
                # Check CSV coordinates first
                csv_coords = self._get_csv_coordinates(unique_name, location_map)
                if csv_coords:
                    latitude, longitude = csv_coords
                elif bus_id in bus_coords:
                    # Fall back to scattered coordinates around the connected bus
                    bus_lat, bus_lon = bus_coords[bus_id]
                    bus_name = store_data['bus']
                    
                    # Get component index for this bus
                    component_index = bus_component_counters.get(bus_name, 0)
                    bus_component_counters[bus_name] = component_index + 1
                    
                    latitude, longitude = self._generate_scattered_coordinates(
                        bus_lat, bus_lon, scatter_radius,
                        components_per_bus[bus_name], component_index
                    )
                
                # Get carrier ID if carrier is specified
                carrier_id = None
                if 'carrier' in store_data and pd.notna(store_data['carrier']):
                    carrier_id = self._get_or_create_carrier(conn, network_id, store_data['carrier'])
                
                # Create component record using atomic function
                request = CreateComponentRequest(
                    network_id=network_id,
                    component_type='STORE',
                    name=unique_name,  # Use deduplicated name
                    bus_id=bus_id,
                    carrier_id=carrier_id,
                    latitude=latitude,
                    longitude=longitude
                )
                component_id = insert_component(conn, request)
                
                # Import store attributes
                self._import_component_attributes(conn, component_id, store_data, 'STORE', strict_validation)
                
                # Import timeseries attributes for stores
                self._import_component_timeseries(conn, network, component_id, store_name, 'STORE', strict_validation)
                
                count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                self.logger.warning(f"Failed to import store {store_name}: {e}")
                continue
        
        return count

    def _get_bus_coordinates(self, conn, network_id: int) -> List[Tuple[float, float]]:
        """Get coordinates of all buses in the network that have valid coordinates"""
        cursor = conn.execute("""
            SELECT latitude, longitude FROM components 
            WHERE network_id = ? AND component_type = 'BUS' 
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            AND NOT (latitude = 0 AND longitude = 0)
        """, (network_id,))
        
        coordinates = [(row[0], row[1]) for row in cursor.fetchall()]
        return coordinates

    def _calculate_bus_separation_radius(self, bus_coordinates: List[Tuple[float, float]]) -> float:
        """Calculate the minimum separation between buses and return a radius for scattering"""
        if len(bus_coordinates) < 2:
            return 0.01  # ~1km at equator
        
        min_distance_degrees = float('inf')
        min_separation_threshold = 0.001  # ~100m threshold to exclude co-located buses
        
        for i, (lat1, lon1) in enumerate(bus_coordinates):
            for j, (lat2, lon2) in enumerate(bus_coordinates[i+1:], i+1):
                # Simple Euclidean distance in degrees
                distance_degrees = math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)
                
                if distance_degrees > min_separation_threshold:
                    min_distance_degrees = min(min_distance_degrees, distance_degrees)
        
        if min_distance_degrees == float('inf'):
            scatter_radius_degrees = 0.05  # ~5km default
        else:
            scatter_radius_degrees = min_distance_degrees * 0.25
        
        # Ensure reasonable bounds: between 1km and 100km equivalent in degrees
        min_radius = 0.01   # ~1km
        max_radius = 1.0    # ~100km
        scatter_radius_degrees = max(min_radius, min(max_radius, scatter_radius_degrees))
        
        return scatter_radius_degrees

    def _detect_and_load_location_csv(self, netcdf_path: str) -> Optional[Dict[str, Tuple[float, float]]]:
        """
        Detect and load companion CSV file with component locations.
        
        Args:
            netcdf_path: Path to the NetCDF file (e.g., /path/to/fileX.nc)
            
        Returns:
            Dictionary mapping component names to (latitude, longitude) tuples, or None if no CSV found
        """
        try:
            # Construct expected CSV path: replace .nc with _locations.csv
            netcdf_file = Path(netcdf_path)
            csv_path = netcdf_file.parent / f"{netcdf_file.stem}_locations.csv"
            
            if not csv_path.exists():
                return None
            
            # Parse the CSV file
            try:
                location_df = pd.read_csv(csv_path)
                
                # Validate required columns
                required_columns = {'name', 'longitude', 'latitude'}
                if not required_columns.issubset(location_df.columns):
                    missing_cols = required_columns - set(location_df.columns)
                    self.logger.warning(f"Location CSV missing required columns: {missing_cols}. Found columns: {list(location_df.columns)}")
                    return None
                
                # Create lookup dictionary
                location_map = {}
                skipped_count = 0
                
                for _, row in location_df.iterrows():
                    name = row['name']
                    longitude = row['longitude']
                    latitude = row['latitude']
                    
                    # Skip rows with missing data
                    if pd.isna(name) or pd.isna(longitude) or pd.isna(latitude):
                        skipped_count += 1
                        continue
                    
                    # Validate coordinate ranges
                    if not (-180 <= longitude <= 180) or not (-90 <= latitude <= 90):
                        self.logger.warning(f"Invalid coordinates for '{name}': longitude={longitude}, latitude={latitude}")
                        skipped_count += 1
                        continue
                    
                    location_map[str(name).strip()] = (float(latitude), float(longitude))
                
                self.logger.info(f"Loaded {len(location_map)} component locations from CSV (skipped {skipped_count} invalid entries)")
                return location_map
                
            except Exception as e:
                self.logger.error(f"Failed to parse location CSV {csv_path}: {e}")
                return None
                
        except Exception as e:
            self.logger.warning(f"Error detecting location CSV: {e}")
            return None
    
    def _get_master_scenario_id(self, conn, network_id: int) -> int:
        """Get the master scenario ID for a network"""
        cursor = conn.execute(
            "SELECT id FROM scenarios WHERE network_id = ? AND is_master = 1",
            (network_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise ValueError(f"No master scenario found for network {network_id}")
        return result[0]
    
    def _get_or_create_carrier(self, conn, network_id: int, carrier_name: str) -> int:
        """Get existing carrier ID or create new carrier"""
        # Try to find existing carrier
        cursor = conn.execute(
            "SELECT id FROM carriers WHERE network_id = ? AND name = ?",
            (network_id, carrier_name)
        )
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create new carrier
        carrier_id = create_carrier(conn, network_id, carrier_name, 0.0, '#3498db', carrier_name)
        return carrier_id
    
    def _generate_component_coordinates(
        self, 
        conn, 
        bus_id: int, 
        scatter_radius: float, 
        location_map: Optional[Dict], 
        component_name: str
    ) -> Tuple[Optional[float], Optional[float]]:
        """Generate coordinates for a component near its connected bus"""
        # Check location map first
        if location_map and component_name in location_map:
            return location_map[component_name]
        
        # Get bus coordinates
        cursor = conn.execute(
            "SELECT latitude, longitude FROM components WHERE id = ?",
            (bus_id,)
        )
        result = cursor.fetchone()
        if not result or result[0] is None or result[1] is None:
            return None, None
        
        bus_lat, bus_lon = result[0], result[1]
        
        # Generate unique name-based offset
        name_hash = hash(component_name) % 1000
        angle = (name_hash / 1000.0) * 2 * math.pi
        
        # Apply scatter radius
        lat_offset = scatter_radius * math.cos(angle)
        lon_offset = scatter_radius * math.sin(angle)
        
        return bus_lat + lat_offset, bus_lon + lon_offset
    
    def _import_component_attributes(
        self, 
        conn, 
        component_id: int, 
        component_data: pd.Series, 
        component_type: str,
        strict_validation: bool
    ):
        """Import component attributes, excluding bus connection columns"""
        
        # Get master scenario ID
        network_id_result = conn.execute("SELECT network_id FROM components WHERE id = ?", (component_id,)).fetchone()
        if not network_id_result:
            self.logger.error(f"Could not find network_id for component {component_id}")
            return
        
        network_id = network_id_result[0]
        scenario_id = self._get_master_scenario_id(conn, network_id)
        
        # Skip these columns as they're handled in the components table
        skip_columns = {
            'bus', 'bus0', 'bus1', 'name',      # Bus connections and name
            'x', 'y', 'location',               # Coordinate/location data (stored as latitude/longitude columns)
            'carrier'                           # Carrier reference (stored as carrier_id column)
        }
        
        attribute_count = 0
        skipped_count = 0
        
        for attr_name, value in component_data.items():
            if attr_name in skip_columns:
                skipped_count += 1
                continue
            
            if pd.isna(value):
                skipped_count += 1
                continue
            
            # Convert value to appropriate format for our database and use smart attribute setting
            try:
                # Get validation rule to check expected data type
                try:
                    rule = get_validation_rule(conn, component_type, attr_name)
                    expected_type = rule.data_type
                except:
                    expected_type = None
                
                # Convert based on expected type or infer from value
                if expected_type == 'boolean':
                    # Handle boolean attributes that might come as int/float from PyPSA
                    if isinstance(value, (bool, np.bool_)):
                        static_value = StaticValue(bool(value))
                    elif isinstance(value, (int, np.integer)):
                        static_value = StaticValue(bool(value))  # 0 -> False, 1 -> True
                    elif isinstance(value, (float, np.floating)):
                        static_value = StaticValue(bool(int(value)))  # 0.0 -> False, 1.0 -> True
                    else:
                        static_value = StaticValue(str(value).lower() == 'true')
                elif expected_type == 'int':
                    # Handle integer attributes
                    if isinstance(value, (int, np.integer)):
                        static_value = StaticValue(int(value))
                    elif isinstance(value, (float, np.floating)):
                        if np.isfinite(value):
                            static_value = StaticValue(int(value))
                        else:
                            skipped_count += 1
                            continue
                    elif isinstance(value, bool):
                        static_value = StaticValue(int(value))
                    else:
                        static_value = StaticValue(int(float(str(value))))
                elif expected_type == 'float':
                    # Handle float attributes
                    if isinstance(value, (float, np.floating)):
                        if np.isfinite(value):
                            static_value = StaticValue(float(value))
                        else:
                            skipped_count += 1
                            continue
                    elif isinstance(value, (int, np.integer)):
                        static_value = StaticValue(float(value))
                    elif isinstance(value, bool):
                        static_value = StaticValue(float(value))
                    else:
                        static_value = StaticValue(float(str(value)))
                else:
                    # Fallback to type inference for unknown or string types
                    if isinstance(value, bool):
                        static_value = StaticValue(bool(value))
                    elif isinstance(value, (int, np.integer)):
                        static_value = StaticValue(int(value))
                    elif isinstance(value, (float, np.floating)):
                        if np.isfinite(value):
                            static_value = StaticValue(float(value))
                        else:
                            skipped_count += 1
                            continue  # Skip infinite/NaN values
                    else:
                        static_value = StaticValue(str(value))
                
                # Use direct static attribute setting
                set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
                attribute_count += 1
                
            except Exception as e:
                # Handle validation errors from db_utils functions
                if ("No validation rule found" in str(e) or 
                    "does not allow" in str(e) or
                    "ValidationError" in str(type(e).__name__)):
                    if strict_validation:
                        raise
                    else:
                        self.logger.warning(f"Skipping undefined/invalid attribute '{attr_name}' for {component_type} component {component_id}: {e}")
                        skipped_count += 1
                        continue
                else:
                    # Log but don't fail on other attribute import errors (like type conversion issues)
                    self.logger.warning(f"Skipping attribute {attr_name} for component {component_id}: {e}")
                    skipped_count += 1
    
    def _import_component_timeseries(
        self,
        conn,
        network,
        component_id: int,
        component_name: str,
        component_type: str,
        strict_validation: bool
    ):
        """Import timeseries attributes from PyPSA network"""
        
        # Get master scenario ID
        network_id_result = conn.execute("SELECT network_id FROM components WHERE id = ?", (component_id,)).fetchone()
        if not network_id_result:
            self.logger.error(f"Could not find network_id for component {component_id}")
            return
        
        network_id = network_id_result[0]
        scenario_id = self._get_master_scenario_id(conn, network_id)
        
        # Map component types to their PyPSA timeseries DataFrames
        timeseries_map = {
            'BUS': getattr(network, 'buses_t', {}),
            'GENERATOR': getattr(network, 'generators_t', {}),
            'LOAD': getattr(network, 'loads_t', {}),
            'LINE': getattr(network, 'lines_t', {}),
            'LINK': getattr(network, 'links_t', {}),
            'STORAGE_UNIT': getattr(network, 'storage_units_t', {}),
            'STORE': getattr(network, 'stores_t', {})
        }
        
        component_timeseries = timeseries_map.get(component_type, {})
        
        if not component_timeseries:
            return
        
        timeseries_count = 0
        
        # Iterate through each timeseries attribute (e.g., 'p', 'q', 'p_set', 'p_max_pu', etc.)
        for attr_name, timeseries_df in component_timeseries.items():
            if component_name not in timeseries_df.columns:
                continue
            
            # Get the timeseries data for this component
            component_series = timeseries_df[component_name]
            
            # Skip if all values are NaN
            if component_series.isna().all():
                continue
            
            try:
                # Convert pandas Series to list of values (using optimized approach)
                values = []
                
                for value in component_series:
                    # Skip NaN values by using 0.0 as default (PyPSA convention)
                    if pd.isna(value):
                        values.append(0.0)
                    else:
                        values.append(float(value))
                
                if not values:
                    self.logger.warning(f"No valid timeseries points for '{attr_name}' on {component_type} '{component_name}'")
                    continue
                
                # Use optimized timeseries attribute setting
                set_timeseries_attribute(conn, component_id, attr_name, values, scenario_id)
                timeseries_count += 1
                
            except Exception as e:
                if strict_validation:
                    raise
                else:
                    self.logger.warning(f"Skipping timeseries attribute '{attr_name}' for {component_type} component '{component_name}': {e}")
                    continue
        
        if timeseries_count > 0:
            self.logger.debug(f"Imported {timeseries_count} timeseries attributes for {component_type} '{component_name}'")
    
    def _generate_unique_name(self, base_name: str, component_type: str) -> str:
        """
        Generate a unique name for a component, ensuring no duplicates across all component types.
        
        Args:
            base_name: The original name to start with
            component_type: The type of component (used in the suffix if needed)
            
        Returns:
            A unique name that hasn't been used yet
        """
        # First try the base name
        if base_name not in self._used_names:
            self._used_names.add(base_name)
            return base_name
            
        # If base name is taken, try appending the component type
        typed_name = f"{base_name}_{component_type.lower()}"
        if typed_name not in self._used_names:
            self._used_names.add(typed_name)
            return typed_name
            
        # If that's taken too, start adding numbers
        counter = 1
        while True:
            unique_name = f"{base_name}_{counter}"
            if unique_name not in self._used_names:
                self._used_names.add(unique_name)
                return unique_name
            counter += 1
    
    def _generate_scattered_coordinates(
        self, 
        bus_lat: float, 
        bus_lon: float, 
        scatter_radius: float,
        component_count_at_bus: int,
        component_index: int
    ) -> Tuple[float, float]:
        """
        Generate scattered coordinates around a bus location.
        
        Args:
            bus_lat: Bus latitude
            bus_lon: Bus longitude  
            scatter_radius: Radius in degrees to scatter within
            component_count_at_bus: Total number of components at this bus
            component_index: Index of this component (0-based)
            
        Returns:
            Tuple of (latitude, longitude) for the scattered position
        """
        if component_count_at_bus == 1:
            # Single component - place it at a moderate distance from the bus
            angle = random.uniform(0, 2 * math.pi)
            distance = scatter_radius * random.uniform(0.5, 0.8)  # 50-80% of scatter radius
        else:
            # Multiple components - arrange in a rough circle with some randomness
            base_angle = (2 * math.pi * component_index) / component_count_at_bus
            angle_jitter = random.uniform(-math.pi/8, math.pi/8)  # ±22.5 degrees jitter
            angle = base_angle + angle_jitter
            
            # Vary distance randomly within the radius (use more of the available radius)
            distance = scatter_radius * random.uniform(0.6, 1.0)  # 60-100% of scatter radius
        
        # Calculate new coordinates
        new_lat = bus_lat + distance * math.cos(angle)
        new_lon = bus_lon + distance * math.sin(angle)
        
        return new_lat, new_lon
    
    def _get_bus_coordinates_map(self, conn, network_id: int) -> Dict[int, Tuple[float, float]]:
        """
        Get a mapping from bus component ID to coordinates.
        
        Returns:
            Dictionary mapping bus component ID to (latitude, longitude) tuple
        """
        cursor = conn.execute("""
            SELECT id, latitude, longitude FROM components 
            WHERE network_id = ? AND component_type = 'BUS' 
            AND latitude IS NOT NULL AND longitude IS NOT NULL
            AND NOT (latitude = 0 AND longitude = 0)
        """, (network_id,))
        
        bus_coords = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}
        return bus_coords
    
    def _resolve_original_component_name(self, unique_name: str) -> str:
        """
        Resolve a potentially modified unique name back to its original name for CSV lookup.
        
        Args:
            unique_name: The unique name that may have been modified (e.g., "component_1", "component_generator")
            
        Returns:
            The original name for CSV lookup
        """
        # Remove common suffixes added by _generate_unique_name
        # Pattern 1: Remove "_NUMBER" suffix (e.g., "component_1" -> "component")
        import re
        
        # First try removing "_NUMBER" pattern
        no_number_suffix = re.sub(r'_\d+$', '', unique_name)
        if no_number_suffix != unique_name:
            return no_number_suffix
        
        # Then try removing "_COMPONENT_TYPE" pattern (e.g., "component_generator" -> "component")
        component_types = ['bus', 'generator', 'load', 'line', 'link', 'storage_unit', 'store']
        for comp_type in component_types:
            suffix = f"_{comp_type.lower()}"
            if unique_name.endswith(suffix):
                return unique_name[:-len(suffix)]
        
        # If no patterns match, return the original name
        return unique_name
    
    def _get_csv_coordinates(
        self, 
        component_name: str, 
        location_map: Optional[Dict[str, Tuple[float, float]]]
    ) -> Optional[Tuple[float, float]]:
        """
        Get coordinates for a component from the CSV location map.
        
        Args:
            component_name: The component name (potentially modified for uniqueness)
            location_map: Dictionary mapping original names to coordinates
            
        Returns:
            (latitude, longitude) tuple if found, None otherwise
        """
        if not location_map:
            return None
        
        # Try exact match first
        if component_name in location_map:
            coordinates = location_map[component_name]
            self.logger.debug(f"CSV location exact match for '{component_name}': {coordinates}")
            return coordinates
        
        # Try resolving back to original name
        original_name = self._resolve_original_component_name(component_name)
        if original_name != component_name and original_name in location_map:
            coordinates = location_map[original_name]
            self.logger.debug(f"CSV location resolved match for '{component_name}' -> '{original_name}': {coordinates}")
            return coordinates
        
        # No match found
        self.logger.debug(f"No CSV location found for component '{component_name}' (original: '{original_name}')")
        return None
