"""
Excel importer for PyConvexity energy system models.
Imports network models from Excel workbooks with multiple sheets.
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
import json

# Import functions directly from pyconvexity
from pyconvexity.core.database import open_connection
from pyconvexity.core.types import StaticValue, CreateNetworkRequest
from pyconvexity.core.errors import AttributeNotFound, ValidationError
from pyconvexity.models import (
    list_components_by_type, create_component, update_component, create_network,
    set_network_config, create_carrier, get_master_scenario_id, get_network_time_periods,
    list_carriers, set_static_attribute, set_timeseries_attribute, get_bus_name_to_id_map,
    get_network_info, delete_attribute
)
from pyconvexity.validation import get_validation_rule
from pyconvexity.timeseries import set_timeseries
from pyconvexity.models.attributes import set_timeseries_attribute as set_timeseries_conn

logger = logging.getLogger(__name__)

class ExcelModelImporter:
    """Import network model from Excel workbook"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def import_model_from_excel(
        self,
        db_path: str,
        excel_path: str,
        network_id: Optional[int] = None,
        network_name: Optional[str] = None,
        network_description: Optional[str] = None,
        scenario_id: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Import network model from Excel workbook
        
        Args:
            db_path: Database path
            excel_path: Excel file path
            network_id: Network ID to import into (if updating existing)
            network_name: Name for new network (if creating new)
            network_description: Description for new network (if creating new)
            scenario_id: Scenario ID (defaults to master scenario)
            update_existing: Whether to update existing components
            add_new: Whether to add new components
            progress_callback: Optional callback for progress updates
            
        Returns:
            Import statistics and metadata
        """
        
        conn = None
        try:
            if progress_callback:
                progress_callback(0, "Starting Excel import...")
            
            # Connect to database
            conn = open_connection(db_path)
            
            # Determine if we're creating a new network or updating existing
            create_new_network = network_id is None
            
            if create_new_network:
                if progress_callback:
                    progress_callback(3, "Reading Excel Overview sheet...")
                
                # Read network configuration from Overview sheet
                overview_df = pd.read_excel(excel_path, sheet_name='Overview')
                network_config = self._read_overview_sheet(overview_df)
                
                self.logger.info(f"Network config from Overview: {network_config}")
                
                # Extract network name from Excel if not provided
                excel_network_name = network_config.get('name')
                if excel_network_name:
                    final_network_name = excel_network_name
                    self.logger.info(f"Using network name from Excel: '{final_network_name}'")
                elif network_name:
                    final_network_name = network_name
                    self.logger.info(f"Using provided network name: '{final_network_name}'")
                else:
                    # Fallback to filename if no name in Excel or provided
                    final_network_name = Path(excel_path).stem
                    self.logger.info(f"Using filename as network name: '{final_network_name}'")
                
                # Extract description from Excel if not provided
                excel_description = network_config.get('description')
                if excel_description:
                    final_description = excel_description
                    self.logger.info(f"Using description from Excel: '{final_description}'")
                elif network_description:
                    final_description = network_description
                    self.logger.info(f"Using provided description: '{final_description}'")
                else:
                    final_description = f"Imported from {Path(excel_path).name}"
                    self.logger.info(f"Using default description: '{final_description}'")
                
                if progress_callback:
                    progress_callback(5, f"Creating network '{final_network_name}'...")
                
                # Create new network
                network_request = CreateNetworkRequest(
                    name=final_network_name,
                    description=final_description,
                    time_resolution=network_config.get('time_resolution', "H"),
                    start_time=network_config.get('start_time'),
                    end_time=network_config.get('end_time')
                )
                
                # Validate that we have the required time information
                if not network_request.start_time or not network_request.end_time:
                    missing_fields = []
                    if not network_request.start_time:
                        missing_fields.append("Time Start")
                    if not network_request.end_time:
                        missing_fields.append("Time End")
                    
                    self.logger.error(f"Missing required time information in Overview sheet: {missing_fields}")
                    self.logger.error(f"Available overview data: {network_config}")
                    raise ValueError(f"Excel file is missing required time information: {', '.join(missing_fields)}. "
                                   f"Please ensure the Overview sheet contains 'Time Start' and 'Time End' fields.")
                
                self.logger.info(f"Creating network with: name='{network_request.name}', "
                               f"start_time='{network_request.start_time}', "
                               f"end_time='{network_request.end_time}', "
                               f"time_resolution='{network_request.time_resolution}'")
                
                network_id = create_network(conn, network_request)
                
                # Generate time periods for the network
                self._generate_time_periods(
                    conn, 
                    network_id, 
                    network_request.start_time, 
                    network_request.end_time, 
                    network_request.time_resolution
                )
                
                # Verify time periods were created
                verification_periods = get_network_time_periods(conn, network_id)
                self.logger.info(f"Network {network_id} now has {len(verification_periods)} time periods")
                
                conn.commit()
                
                if progress_callback:
                    progress_callback(5, f"Created network '{final_network_name}' (ID: {network_id})")
            else:
                if progress_callback:
                    progress_callback(3, f"Using existing network ID: {network_id}")
                    
                # For existing networks, validate time axis compatibility
                if progress_callback:
                    progress_callback(5, "Validating time axis compatibility...")
                    
                # Read network configuration from Overview sheet to compare
                try:
                    overview_df = pd.read_excel(excel_path, sheet_name='Overview')
                    excel_time_config = self._read_overview_sheet(overview_df)
                except Exception as e:
                    self.logger.warning(f"Could not read Overview sheet: {e}")
                    self.logger.warning("Skipping time axis validation - assuming Excel is compatible")
                    excel_time_config = {}
                
                # Validate time axis matches existing network
                self._validate_time_axis_compatibility(conn, network_id, excel_time_config)
                
                self.logger.info("Time axis validation passed - Excel matches existing network")
            
            # Set import behavior based on whether this is a new or existing network
            if network_id is None:
                # New network: Always add all components from Excel
                actual_update_existing = False  # No existing components to update
                actual_add_new = True          # Add everything from Excel
                self.logger.info("Import mode: NEW NETWORK - Adding all components from Excel")
            else:
                # Existing network: Always update existing and add new (user's requirement)
                actual_update_existing = True   # Update components that exist
                actual_add_new = True          # Add components that don't exist
                self.logger.info("Import mode: EXISTING NETWORK - Update existing + add new components")
            
            # Get master scenario if no scenario specified
            if scenario_id is None:
                scenario_id = get_master_scenario_id(conn, network_id)
                if scenario_id is None:
                    raise ValueError("No master scenario found for network")
            
            if progress_callback:
                progress_callback(8, "Reading Excel file...")
            
            # Read Excel file
            excel_data = self._read_excel_file(excel_path)
            
            if progress_callback:
                progress_callback(18, "Processing carriers...")
            
            # Import carriers first
            carriers_df = excel_data.get('Carriers', pd.DataFrame())
            carriers_imported = self._import_carriers(conn, network_id, carriers_df)
            
            if progress_callback:
                progress_callback(28, "Processing components...")
            
            # Import components by type
            component_types = ['Buses', 'Generators', 'Loads', 'Lines', 'Links', 'Storage Units', 'Stores', 'Constraints']
            components_imported = {}
            
            for sheet_name in component_types:
                if sheet_name in excel_data:
                    comp_type = self._get_component_type_from_sheet(sheet_name)
                    self.logger.info(f"Processing sheet '{sheet_name}' as component type '{comp_type}' with {len(excel_data[sheet_name])} rows")
                    components_imported[comp_type] = self._import_components(
                        conn, network_id, comp_type, excel_data[sheet_name], 
                        scenario_id, actual_update_existing, actual_add_new
                    )
            
            if progress_callback:
                progress_callback(78, "Processing timeseries data...")
            
            # Import timeseries data
            timeseries_imported = self._import_timeseries_data(
                conn, network_id, excel_data, scenario_id
            )
            
            if progress_callback:
                progress_callback(93, "Processing network configuration...")
            
            # Import network configuration
            network_config_df = excel_data.get('Network Config', pd.DataFrame())
            config_imported = self._import_network_config(
                conn, network_id, network_config_df
            )
            
            conn.commit()
            
            if progress_callback:
                progress_callback(100, "Excel import completed")
            
            # Calculate statistics
            stats = self._calculate_import_stats(
                carriers_imported, components_imported, timeseries_imported, config_imported
            )
            stats['network_id'] = network_id
            stats['created_new_network'] = create_new_network
            
            return {
                "success": True,
                "message": f"Network {'created' if create_new_network else 'updated'} from Excel: {excel_path}",
                "network_id": network_id,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Excel import failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Import failed: {str(e)}")
            raise
        finally:
            # Always close the connection, even on error
            if conn is not None:
                try:
                    conn.close()
                except Exception as e:
                    self.logger.warning(f"Failed to close database connection: {e}")
    
    def _generate_time_periods(self, conn, network_id: int, start_time: str, end_time: str, time_resolution: str) -> None:
        """Generate and insert time periods for the network"""
        import pandas as pd
        from datetime import datetime
        
        try:
            # Parse start and end times
            start_dt = pd.to_datetime(start_time)
            end_dt = pd.to_datetime(end_time)
            
            # Convert time_resolution to pandas frequency string
            if time_resolution == 'H':
                freq_str = 'H'
            elif time_resolution == 'D':
                freq_str = 'D'
            elif time_resolution.endswith('H'):
                hours = int(time_resolution[:-1])
                freq_str = f'{hours}H'
            elif time_resolution.endswith('min'):
                minutes = int(time_resolution[:-3])
                freq_str = f'{minutes}min'
            else:
                self.logger.warning(f"Unknown time resolution '{time_resolution}', defaulting to hourly")
                freq_str = 'H'
            
            # Generate timestamps
            timestamps = pd.date_range(start=start_dt, end=end_dt, freq=freq_str, inclusive='both')
            
            self.logger.info(f"Generating {len(timestamps)} time periods from {start_time} to {end_time} at {time_resolution} resolution")
            
            # Insert optimized time periods metadata
            period_count = len(timestamps)
            start_timestamp = int(timestamps[0].timestamp())
            
            # Calculate interval in seconds
            if len(timestamps) > 1:
                interval_seconds = int((timestamps[1] - timestamps[0]).total_seconds())
            else:
                interval_seconds = 3600  # Default to hourly
            
            conn.execute("""
                INSERT INTO network_time_periods (network_id, period_count, start_timestamp, interval_seconds)
                VALUES (?, ?, ?, ?)
            """, (network_id, period_count, start_timestamp, interval_seconds))
            
            self.logger.info(f"Successfully created {len(timestamps)} time periods for network {network_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to generate time periods: {e}")
            raise

    def _read_overview_sheet(self, overview_df: pd.DataFrame) -> Dict[str, Any]:
        """Extract network configuration from Overview sheet"""
        config = {}
        
        if overview_df.empty:
            self.logger.warning("Overview sheet is empty")
            return config
            
        self.logger.info(f"Overview sheet has {len(overview_df)} rows and columns: {list(overview_df.columns)}")
        self.logger.info(f"First few rows of overview sheet:\n{overview_df.head()}")
        
        # Convert to a simple key-value lookup
        overview_data = {}
        
        # Handle both old single-column format and new two-column format
        if 'Property' in overview_df.columns and 'Value' in overview_df.columns:
            # New two-column format
            for _, row in overview_df.iterrows():
                key = str(row['Property']).strip() if pd.notna(row['Property']) else ""
                value = str(row['Value']).strip() if pd.notna(row['Value']) else ""
                if key and value and value != 'nan':
                    overview_data[key] = value
                    self.logger.debug(f"Parsed overview data: '{key}' = '{value}'")
        elif len(overview_df.columns) >= 2:
            # Old format - try to read from first two columns
            for i, row in overview_df.iterrows():
                key = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                value = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                if key and value and value != 'nan':
                    overview_data[key] = value
                    self.logger.debug(f"Parsed overview data: '{key}' = '{value}'")
        else:
            self.logger.error(f"Overview sheet format not recognized. Columns: {list(overview_df.columns)}")
            return config
        
        self.logger.info(f"Parsed overview data: {overview_data}")
        
        # Extract network configuration
        if 'Name' in overview_data:
            config['name'] = overview_data['Name']
        if 'Description' in overview_data:
            config['description'] = overview_data['Description']
        if 'Time Start' in overview_data:
            config['start_time'] = overview_data['Time Start']
            self.logger.info(f"Found Time Start: {config['start_time']}")
        if 'Time End' in overview_data:
            config['end_time'] = overview_data['Time End']
            self.logger.info(f"Found Time End: {config['end_time']}")
        if 'Time Interval' in overview_data:
            # Convert time interval format to our format
            interval = overview_data['Time Interval'].strip()
            self.logger.info(f"Found Time Interval: '{interval}'")
            
            if interval == 'P1D':
                config['time_resolution'] = 'D'  # Daily
            elif interval == 'PT1H' or interval == 'h' or interval == 'H':
                config['time_resolution'] = 'H'  # Hourly
            elif interval.startswith('PT') and interval.endswith('H'):
                # Extract hours (e.g., 'PT3H' -> '3H')
                hours = interval[2:-1]
                config['time_resolution'] = f'{hours}H'
            elif interval.endswith('h') or interval.endswith('H'):
                # Handle simple formats like '2h', '3H'
                if interval[:-1].isdigit():
                    hours = interval[:-1]
                    config['time_resolution'] = f'{hours}H'
                else:
                    config['time_resolution'] = 'H'  # Default to hourly
            else:
                self.logger.warning(f"Unknown time interval format '{interval}', defaulting to hourly")
                config['time_resolution'] = 'H'  # Default to hourly
        
        self.logger.info(f"Final network config from Overview sheet: {config}")
        return config
    
    def _read_excel_file(self, excel_path: str) -> Dict[str, pd.DataFrame]:
        """Read Excel file and return dictionary of DataFrames by sheet name"""
        excel_data = {}
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(excel_path)
            
            self.logger.info(f"Excel file contains sheets: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                if sheet_name == 'Overview':
                    continue  # Skip overview sheet
                
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                if not df.empty:
                    excel_data[sheet_name] = df
                    self.logger.info(f"Loaded sheet '{sheet_name}' with {len(df)} rows")
                else:
                    self.logger.info(f"Skipped empty sheet '{sheet_name}'")
                    
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")
        
        return excel_data
    
    def _get_component_type_from_sheet(self, sheet_name: str) -> str:
        """Convert sheet name to component type"""
        mapping = {
            'Buses': 'BUS',
            'Generators': 'GENERATOR',
            'Loads': 'LOAD',
            'Lines': 'LINE',
            'Links': 'LINK',
            'Storage Units': 'STORAGE_UNIT',
            'Stores': 'STORE',
            'Constraints': 'CONSTRAINT'
        }
        return mapping.get(sheet_name, sheet_name.upper())
    
    def _import_carriers(self, conn, network_id: int, carriers_df: pd.DataFrame) -> Dict[str, Any]:
        """Import carriers from Excel data"""
        imported = {'created': 0, 'updated': 0, 'errors': 0}
        
        if carriers_df.empty:
            return imported
        
        # Get existing carriers
        existing_carriers = list_carriers(conn, network_id)
        existing_names = {carrier['name'] for carrier in existing_carriers}
        
        for _, row in carriers_df.iterrows():
            try:
                carrier_name = str(row.get('name', '')).strip()
                if not carrier_name:
                    continue
                
                # Check if carrier exists
                if carrier_name in existing_names:
                    imported['updated'] += 1
                else:
                    # Create new carrier
                    create_carrier(
                        conn,
                            network_id,
                            carrier_name,
                        co2_emissions=row.get('co2_emissions', 0.0),
                        color=row.get('color', '#ffffff'),
                        nice_name=row.get('nice_name', carrier_name)
                    )
                    imported['created'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to import carrier {carrier_name}: {e}")
                imported['errors'] += 1
        
        return imported
    
    def _import_components(
        self, 
        conn, 
        network_id: int, 
        component_type: str, 
        components_df: pd.DataFrame,
        scenario_id: int,
        update_existing: bool,
        add_new: bool
    ) -> Dict[str, Any]:
        """Import components of a specific type"""
        imported = {'created': 0, 'updated': 0, 'errors': 0}
        
        if components_df.empty:
            return imported
        
        # Get existing components of this type
        existing_components = list_components_by_type(conn, network_id, component_type)
        existing_names = {comp.name for comp in existing_components}
        
        # Get carriers and buses for foreign key resolution
        carriers = list_carriers(conn, network_id)
        buses = list_components_by_type(conn, network_id, 'BUS')
        
        carrier_name_to_id = {carrier['name']: carrier['id'] for carrier in carriers}
        bus_name_to_id = {bus.name: bus.id for bus in buses}
        
        
        for _, row in components_df.iterrows():
            try:
                component_name = str(row.get('name', '')).strip()
                if not component_name:
                    continue
                
                # Debug logging for CONSTRAINT components (reduced verbosity)
                if component_type == 'CONSTRAINT':
                    self.logger.debug(f"Processing CONSTRAINT '{component_name}'")
                
                # Resolve foreign keys
                carrier_id = None
                # CONSTRAINT components don't have carriers
                if row.get('carrier') and component_type != 'CONSTRAINT':
                    carrier_name = str(row['carrier']).strip()
                    carrier_id = carrier_name_to_id.get(carrier_name)
                    self.logger.info(f"Component '{component_name}' has carrier '{carrier_name}', resolved to carrier_id: {carrier_id}")
                    if carrier_id is None:
                        self.logger.warning(f"Carrier '{carrier_name}' not found for component '{component_name}'. Available carriers: {list(carrier_name_to_id.keys())}")
                elif component_type == 'CONSTRAINT':
                    self.logger.debug(f"CONSTRAINT '{component_name}' - skipping carrier resolution")
                
                bus_id = None
                # CONSTRAINT components don't connect to buses
                if row.get('bus') and component_type != 'CONSTRAINT':
                    bus_name = str(row['bus']).strip()
                    bus_id = bus_name_to_id.get(bus_name)
                    if bus_id is None:
                        self.logger.warning(f"Bus '{bus_name}' not found for component '{component_name}'. Available buses: {list(bus_name_to_id.keys())}")
                
                bus0_id = None
                if row.get('bus0') and component_type != 'CONSTRAINT':
                    bus0_name = str(row['bus0']).strip()
                    bus0_id = bus_name_to_id.get(bus0_name)
                    if bus0_id is None:
                        self.logger.warning(f"Bus0 '{bus0_name}' not found for component '{component_name}'. Available buses: {list(bus_name_to_id.keys())}")
                
                bus1_id = None
                if row.get('bus1') and component_type != 'CONSTRAINT':
                    bus1_name = str(row['bus1']).strip()
                    bus1_id = bus_name_to_id.get(bus1_name)
                    if bus1_id is None:
                        self.logger.warning(f"Bus1 '{bus1_name}' not found for component '{component_name}'. Available buses: {list(bus_name_to_id.keys())}")
                
                # Check if component exists
                if component_name in existing_names and update_existing:
                    # Update existing component
                    existing_comp = next(c for c in existing_components if c.name == component_name)
                    
                    try:
                        # Update component using the proper function
                        # CONSTRAINT components must have carrier_id=None per database schema
                        final_carrier_id = None if component_type == 'CONSTRAINT' else carrier_id
                        update_component(
                            conn,
                            existing_comp.id,
                            carrier_id=final_carrier_id,
                            bus_id=bus_id,
                            bus0_id=bus0_id,
                            bus1_id=bus1_id,
                            latitude=row.get('latitude'),
                            longitude=row.get('longitude')
                        )
                        
                        # Update attributes
                        self._update_component_attributes(conn, existing_comp.id, row, scenario_id)
                        imported['updated'] += 1
                        
                    except Exception as e:
                        self.logger.error(f"Failed to update component '{component_name}': {e}")
                        imported['errors'] += 1
                        continue
                    
                elif component_name not in existing_names and add_new:
                    # Create new component using the proper function
                    # CONSTRAINT components must have carrier_id=None per database schema
                    final_carrier_id = None if component_type == 'CONSTRAINT' else carrier_id
                    
                    # Handle latitude/longitude - CONSTRAINT components don't have location
                    if component_type == 'CONSTRAINT':
                        lat_val = None
                        lon_val = None
                        self.logger.debug(f"CONSTRAINT '{component_name}' - setting latitude/longitude to None")
                    else:
                        # Clean empty strings for other component types
                        lat_val = row.get('latitude')
                        lon_val = row.get('longitude')
                        if lat_val == '' or (isinstance(lat_val, str) and lat_val.strip() == ''):
                            lat_val = None
                        if lon_val == '' or (isinstance(lon_val, str) and lon_val.strip() == ''):
                            lon_val = None
                    
                    component_id = create_component(
                        conn,
                        network_id,
                        component_type,
                        component_name,
                        longitude=lon_val,
                        latitude=lat_val,
                        carrier_id=final_carrier_id,
                        bus_id=bus_id,
                        bus0_id=bus0_id,
                        bus1_id=bus1_id
                    )
                    
                    # Set attributes
                    self._set_component_attributes(conn, component_id, row, scenario_id)
                    imported['created'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to import component '{component_name}' of type '{component_type}': {e}")
                self.logger.error(f"Component data: name='{component_name}', carrier_id={carrier_id}, bus_id={bus_id}, bus0_id={bus0_id}, bus1_id={bus1_id}")
                imported['errors'] += 1
        
        return imported
    
    def _update_component_attributes(self, conn, component_id: int, row: pd.Series, scenario_id: int):
        """Update attributes for an existing component"""
        # Get validation rules for this component type
        cursor = conn.execute(
            "SELECT component_type FROM components WHERE id = ?",
            (component_id,)
        )
        component_type = cursor.fetchone()[0]
        
        # Process each column as potential attribute
        for column, value in row.items():
            if column in ['name', 'carrier', 'bus', 'bus0', 'bus1', 'latitude', 'longitude', 'type']:
                continue  # Skip basic fields
            
            if value == '[timeseries]':
                continue  # Skip timeseries markers
            
            # Check if this is a valid attribute
            validation_rule = get_validation_rule(conn, component_type, column)
            if validation_rule:
                # Handle blank cells (empty strings or NaN) - these should unset the attribute
                if pd.isna(value) or value == '':
                    try:
                        delete_attribute(conn, component_id, column, scenario_id)
                        self.logger.debug(f"Unset attribute '{column}' for component {component_id} due to blank cell")
                    except Exception as e:
                        # Attribute might not exist, which is fine
                        self.logger.debug(f"Could not unset attribute '{column}' for component {component_id}: {e}")
                else:
                    # Set the attribute with the provided value
                    self._set_single_attribute(conn, component_id, column, value, validation_rule, scenario_id)
    
    def _set_component_attributes(self, conn, component_id: int, row: pd.Series, scenario_id: int):
        """Set attributes for a new component"""
        # Get validation rules for this component type
        cursor = conn.execute(
            "SELECT component_type FROM components WHERE id = ?",
            (component_id,)
        )
        component_type = cursor.fetchone()[0]
        
        # Process each column as potential attribute
        for column, value in row.items():
            if column in ['name', 'carrier', 'bus', 'bus0', 'bus1', 'latitude', 'longitude', 'type']:
                continue  # Skip basic fields
            
            if value == '[timeseries]':
                continue  # Skip timeseries markers
            
            # Check if this is a valid attribute
            validation_rule = get_validation_rule(conn, component_type, column)
            if validation_rule:
                # For new components, only set attributes that have actual values
                # Blank cells (empty strings or NaN) are left unset (which is the default state)
                if not (pd.isna(value) or value == ''):
                    # Set the attribute with the provided value
                    self._set_single_attribute(conn, component_id, column, value, validation_rule, scenario_id)
    
    def _set_single_attribute(self, conn, component_id: int, attr_name: str, value: Any, validation_rule: Dict, scenario_id: int):
        """Set a single attribute with proper type conversion"""
        data_type = validation_rule.data_type if hasattr(validation_rule, 'data_type') else validation_rule.get('data_type', 'string')
        
        try:
            if data_type == 'float':
                static_value = StaticValue(float(value))
                set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
            elif data_type == 'int':
                static_value = StaticValue(int(value))
                set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
            elif data_type == 'boolean':
                bool_value = str(value).lower() in ['true', '1', 'yes']
                static_value = StaticValue(bool_value)
                set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
            else:  # string
                static_value = StaticValue(str(value))
                set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
        except (AttributeNotFound, ValidationError):
            # Skip missing attributes or validation errors silently (same as PyPSA solver)
            pass
        except Exception as e:
            self.logger.warning(f"Failed to set attribute {attr_name} for component {component_id}: {e}")
    
    def _import_timeseries_data(self, conn, network_id: int, excel_data: Dict, scenario_id: int) -> Dict[str, Any]:
        """Import timeseries data from Excel sheets"""
        imported = {'attributes': 0, 'errors': 0}
        
        # Get network time periods for timestamp mapping
        network_time_periods = get_network_time_periods(conn, network_id)
        time_period_map = {period.formatted_time: period for period in network_time_periods}
        
        expected_length = len(network_time_periods)
        self.logger.info(f"TIMESERIES DEBUG: Network has {expected_length} time periods for timeseries import")
        if network_time_periods:
            self.logger.info(f"TIMESERIES DEBUG: Time period range: {network_time_periods[0].formatted_time} to {network_time_periods[-1].formatted_time}")
        else:
            self.logger.error("TIMESERIES DEBUG: NO TIME PERIODS FOUND! Timeseries import will fail.")
            return imported
        
        # Look for timeseries sheets
        for sheet_name, df in excel_data.items():
            if 'Timeseries' in sheet_name and not df.empty:
                self.logger.info(f"TIMESERIES DEBUG: Processing sheet '{sheet_name}' with {len(df)} rows")
                component_type = self._get_component_type_from_sheet(sheet_name.replace(' Timeseries', ''))
                
                # Get timestamps
                timestamps = df.get('timestamp', [])
                if timestamps.empty:
                    self.logger.warning(f"TIMESERIES DEBUG: No timestamp column found in {sheet_name}")
                    continue
                
                excel_ts_length = len(timestamps)
                self.logger.info(f"TIMESERIES DEBUG: Sheet '{sheet_name}' has {excel_ts_length} timestamps (expected: {expected_length})")
                if excel_ts_length != expected_length:
                    self.logger.warning(f"TIMESERIES DEBUG: LENGTH MISMATCH in sheet '{sheet_name}': Excel has {excel_ts_length}, network expects {expected_length} (difference: {excel_ts_length - expected_length})")
                
                # Log timestamp range for debugging
                if len(timestamps) > 0:
                    first_ts = str(timestamps.iloc[0]).strip()
                    last_ts = str(timestamps.iloc[-1]).strip()
                    self.logger.info(f"TIMESERIES DEBUG: Sheet timestamp range: '{first_ts}' to '{last_ts}'")
                
                # Process each column (except timestamp)
                for column in df.columns:
                    if column == 'timestamp':
                        continue
                    
                    # Parse component name and attribute from column name
                    # Format: "Component Name_attribute_name"
                    # We need to find the last underscore that separates component name from attribute
                    if '_' in column:
                        # Find all components of this type to match against
                        components = list_components_by_type(conn, network_id, component_type)
                        component_names = [c.name for c in components]
                        
                        # Try to find the component name by matching against known components
                        component_name = None
                        attr_name = None
                        
                        for comp_name in component_names:
                            # Check if column starts with component name + underscore
                            prefix = f"{comp_name}_"
                            if column.startswith(prefix):
                                component_name = comp_name
                                attr_name = column[len(prefix):]
                                break
                        
                        if component_name and attr_name:
                            # Find component by name
                            component = next((c for c in components if c.name == component_name), None)
                        
                        if component:
                            # Create timeseries data using efficient array format
                            timeseries_values = []
                            filled_missing_values = 0
                            
                            # Debug: Show first few timestamps for comparison
                            if len(timestamps) > 0 and len(network_time_periods) > 0:
                                excel_first = str(timestamps.iloc[0]).strip()
                                excel_last = str(timestamps.iloc[-1]).strip() if len(timestamps) > 1 else excel_first
                                network_first = network_time_periods[0].formatted_time
                                network_last = network_time_periods[-1].formatted_time if len(network_time_periods) > 1 else network_first
                                
                                self.logger.info(f"TIMESERIES DEBUG: Timestamp comparison for '{component_name}.{attr_name}':")
                                self.logger.info(f"  Excel range: '{excel_first}' to '{excel_last}' ({len(timestamps)} periods)")
                                self.logger.info(f"  Network range: '{network_first}' to '{network_last}' ({len(network_time_periods)} periods)")
                            
                            # Take the first N values from Excel where N = expected network periods
                            # This puts responsibility on user to format Excel correctly
                            max_periods = min(len(timestamps), len(network_time_periods), len(df[column]))
                            
                            for i in range(max_periods):
                                value = df[column].iloc[i]
                                
                                # Handle missing values - use 0.0 as default
                                if pd.isna(value):
                                    actual_value = 0.0
                                    filled_missing_values += 1
                                else:
                                    try:
                                        actual_value = float(value)
                                    except (ValueError, TypeError):
                                        actual_value = 0.0
                                        filled_missing_values += 1
                                
                                timeseries_values.append(actual_value)
                            
                            final_ts_length = len(timeseries_values)
                            self.logger.info(f"TIMESERIES DEBUG: Component '{component_name}.{attr_name}': "
                                           f"Excel rows={excel_ts_length}, "
                                           f"Network periods={expected_length}, "
                                           f"Used={max_periods}, "
                                           f"Filled missing={filled_missing_values}, "
                                           f"Final length={final_ts_length}")
                            
                            if filled_missing_values > 0:
                                self.logger.warning(f"TIMESERIES DEBUG: Filled {filled_missing_values} missing/invalid values with 0.0 for '{component_name}.{attr_name}'")
                            
                            if excel_ts_length != expected_length:
                                self.logger.warning(f"TIMESERIES DEBUG: LENGTH MISMATCH for '{component_name}.{attr_name}': "
                                                  f"Excel has {excel_ts_length} rows, network expects {expected_length} periods")
                            
                            if final_ts_length != expected_length:
                                self.logger.warning(f"TIMESERIES DEBUG: FINAL LENGTH MISMATCH for '{component_name}.{attr_name}': "
                                                  f"Expected {expected_length}, got {final_ts_length} (difference: {final_ts_length - expected_length})")
                            
                            if timeseries_values:
                                try:
                                    # Use new efficient timeseries API
                                    set_timeseries_conn(
                                        conn, component.id, attr_name, timeseries_values, scenario_id
                                    )
                                    imported['attributes'] += 1
                                    self.logger.info(f"TIMESERIES DEBUG: Successfully imported {final_ts_length} points for '{component_name}.{attr_name}'")
                                except Exception as e:
                                    self.logger.error(f"TIMESERIES DEBUG: Failed to set timeseries attribute {attr_name} for {component_name}: {e}")
                                    imported['errors'] += 1
                            else:
                                self.logger.warning(f"TIMESERIES DEBUG: No valid timeseries data found for {component_name}.{attr_name}")
                        else:
                            self.logger.warning(f"TIMESERIES DEBUG: Component '{component_name}' not found for timeseries import")
                    else:
                        self.logger.warning(f"TIMESERIES DEBUG: Could not parse column '{column}' into component and attribute names")
                else:
                    self.logger.warning(f"TIMESERIES DEBUG: Column '{column}' does not contain underscore separator")
        
        return imported
    
    def _import_network_config(self, conn, network_id: int, config_df: pd.DataFrame) -> Dict[str, Any]:
        """Import network configuration from Excel"""
        imported = {'parameters': 0, 'errors': 0}
        
        # Handle case where config_df might be a list (when sheet doesn't exist)
        if not isinstance(config_df, pd.DataFrame):
            self.logger.info("No Network Config sheet found, using default configuration")
            # Set default network configuration
            default_config = {
                'unmet_load_active': True,
                'discount_rate': 0.01,
                'solver_name': 'highs',
                'currency': 'USD'
            }
            
            for param_name, param_value in default_config.items():
                try:
                    if isinstance(param_value, bool):
                        param_type = 'boolean'
                    elif isinstance(param_value, float):
                        param_type = 'real'
                    elif isinstance(param_value, int):
                        param_type = 'integer'
                    else:
                        param_type = 'string'
                    
                    set_network_config(
                        conn, 
                        network_id, 
                        param_name, 
                        param_value, 
                        param_type, 
                        scenario_id=None,  # Network default
                        description=f"Default {param_name} setting"
                    )
                    imported['parameters'] += 1
                    self.logger.info(f"Set default network config: {param_name} = {param_value}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to set default network config parameter {param_name}: {e}")
                    imported['errors'] += 1
            
            return imported
        
        if config_df.empty:
            self.logger.info("Network Config sheet is empty, using default configuration")
            # Set default network configuration
            default_config = {
                'unmet_load_active': True,
                'discount_rate': 0.01,
                'solver_name': 'default',
                'currency': 'USD'
            }
            
            for param_name, param_value in default_config.items():
                try:
                    if isinstance(param_value, bool):
                        param_type = 'boolean'
                    elif isinstance(param_value, float):
                        param_type = 'real'
                    elif isinstance(param_value, int):
                        param_type = 'integer'
                    else:
                        param_type = 'string'
                    
                    set_network_config(
                        conn, 
                        network_id, 
                        param_name, 
                        param_value, 
                        param_type, 
                        scenario_id=None,  # Network default
                        description=f"Default {param_name} setting"
                    )
                    imported['parameters'] += 1
                    self.logger.info(f"Set default network config: {param_name} = {param_value}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to set default network config parameter {param_name}: {e}")
                    imported['errors'] += 1
            
            return imported
        
        for _, row in config_df.iterrows():
            try:
                param_name = str(row.get('Parameter', '')).strip()
                param_value = row.get('Value', '')
                param_type = str(row.get('Type', 'string')).strip()
                param_description = str(row.get('Description', '')).strip()
                
                if not param_name:
                    continue
                
                # Validate parameter type and map Python types to database types
                valid_types = {'boolean', 'real', 'integer', 'string', 'json'}
                
                # Map Python type names to database type names
                type_mapping = {
                    'bool': 'boolean',
                    'float': 'real', 
                    'int': 'integer',
                    'str': 'string'
                }
                
                # Convert Python type name to database type name if needed
                if param_type in type_mapping:
                    param_type = type_mapping[param_type]
                
                if param_type not in valid_types:
                    self.logger.error(f"Invalid parameter type '{param_type}' for parameter '{param_name}'. Must be one of {valid_types}")
                    imported['errors'] += 1
                    continue
                
                # Convert value based on type
                try:
                    if param_type == 'boolean':
                        # Handle various boolean representations
                        if isinstance(param_value, bool):
                            converted_value = param_value
                        elif isinstance(param_value, str):
                            converted_value = param_value.lower() in {'true', '1', 'yes', 'on'}
                        elif isinstance(param_value, (int, float)):
                            converted_value = bool(param_value)
                        else:
                            converted_value = False
                    elif param_type == 'real':
                        converted_value = float(param_value)
                    elif param_type == 'integer':
                        converted_value = int(float(param_value))  # Handle float strings like "1.0"
                    elif param_type == 'json':
                        if isinstance(param_value, str):
                            import json
                            converted_value = json.loads(param_value)
                        else:
                            converted_value = param_value
                    else:  # string
                        converted_value = str(param_value)
                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    self.logger.error(f"Failed to convert parameter '{param_name}' value '{param_value}' to type '{param_type}': {e}")
                    imported['errors'] += 1
                    continue
                
                # Use the proper set_network_config function from pyconvexity
                set_network_config(
                    conn, 
                    network_id, 
                    param_name, 
                    converted_value, 
                    param_type, 
                    scenario_id=None,  # Network default
                    description=param_description if param_description else None
                    )
                imported['parameters'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to import network config parameter {param_name}: {e}")
                imported['errors'] += 1
        
        return imported
    
    def _validate_time_axis_compatibility(self, conn, network_id: int, excel_time_config: Dict[str, str]) -> None:
        """Validate that Excel time axis matches existing network time axis"""
        try:
            # Get existing network info
            existing_network = get_network_info(conn, network_id)
            
            # Compare time axis parameters
            excel_start = excel_time_config.get('start_time', '').strip()
            excel_end = excel_time_config.get('end_time', '').strip()
            excel_interval = excel_time_config.get('time_resolution', '').strip()
            
            existing_start = existing_network.get('time_start', '').strip()
            existing_end = existing_network.get('time_end', '').strip()
            existing_interval = existing_network.get('time_interval', '').strip()
            
            self.logger.info(f"TIME AXIS DEBUG: Validating time axis compatibility")
            self.logger.info(f"TIME AXIS DEBUG: Excel: {excel_start} to {excel_end}, interval: {excel_interval}")
            self.logger.info(f"TIME AXIS DEBUG: Network: {existing_start} to {existing_end}, interval: {existing_interval}")
            
            # Skip validation if Excel doesn't have time information (allow partial updates)
            if not excel_start or not excel_end or not excel_interval:
                self.logger.warning("TIME AXIS DEBUG: Excel Overview sheet missing time axis information - skipping validation")
                self.logger.warning("TIME AXIS DEBUG: Assuming Excel data is compatible with existing network time axis")
                return
            
            # Normalize case and format for time interval comparison
            excel_interval_normalized = self._normalize_time_interval(excel_interval)
            existing_interval_normalized = self._normalize_time_interval(existing_interval)
            
            self.logger.info(f"TIME AXIS DEBUG: Normalized intervals - Excel: '{excel_interval_normalized}', Network: '{existing_interval_normalized}'")
            
            # Check if they match
            if (excel_start != existing_start or 
                excel_end != existing_end or 
                excel_interval_normalized != existing_interval_normalized):
                
                self.logger.error(f"TIME AXIS DEBUG: MISMATCH DETECTED!")
                self.logger.error(f"TIME AXIS DEBUG: Start times - Excel: '{excel_start}', Network: '{existing_start}' (match: {excel_start == existing_start})")
                self.logger.error(f"TIME AXIS DEBUG: End times - Excel: '{excel_end}', Network: '{existing_end}' (match: {excel_end == existing_end})")
                self.logger.error(f"TIME AXIS DEBUG: Intervals - Excel: '{excel_interval_normalized}', Network: '{existing_interval_normalized}' (match: {excel_interval_normalized == existing_interval_normalized})")
                
                raise ValueError(
                    f"Time axis mismatch! "
                    f"Excel has {excel_start} to {excel_end} ({excel_interval}), "
                    f"but existing network has {existing_start} to {existing_end} ({existing_interval}). "
                    f"Time axis must match exactly when importing into an existing network."
                )
            else:
                self.logger.info(f"TIME AXIS DEBUG: Time axis validation PASSED - Excel and network time axes match")
                
        except Exception as e:
            if "Time axis mismatch" in str(e):
                raise  # Re-raise validation errors
            else:
                # Log other errors but don't fail the import
                self.logger.error(f"Error during time axis validation: {e}")
                self.logger.warning("Continuing with import despite time axis validation error")
    
    def _normalize_time_interval(self, interval: str) -> str:
        """Normalize time interval format for comparison"""
        interval = interval.strip().upper()
        
        # Handle common variations
        if interval in ['H', '1H', 'PT1H', 'HOURLY']:
            return 'H'
        elif interval in ['D', '1D', 'P1D', 'DAILY']:
            return 'D'
        elif interval.endswith('H') and interval[:-1].isdigit():
            return interval  # Already normalized (e.g., '2H', '3H')
        elif interval.startswith('PT') and interval.endswith('H'):
            # Convert PT3H -> 3H
            hours = interval[2:-1]
            return f'{hours}H'
        
        return interval
    
    def _calculate_import_stats(self, carriers_imported: Dict, components_imported: Dict, 
                               timeseries_imported: Dict, config_imported: Dict) -> Dict[str, Any]:
        """Calculate import statistics"""
        total_created = carriers_imported['created'] + sum(
            comp['created'] for comp in components_imported.values()
        )
        total_updated = carriers_imported['updated'] + sum(
            comp['updated'] for comp in components_imported.values()
        )
        total_errors = carriers_imported['errors'] + sum(
            comp['errors'] for comp in components_imported.values()
        ) + timeseries_imported['errors'] + config_imported['errors']
        
        return {
            'total_created': total_created,
            'total_updated': total_updated,
            'total_errors': total_errors,
            'carriers': carriers_imported,
            'components': components_imported,
            'timeseries': timeseries_imported,
            'network_config': config_imported
        }
