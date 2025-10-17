"""
Excel exporter for PyConvexity energy system models.
Exports complete network models to Excel workbooks with multiple sheets.
"""

import logging
import sqlite3
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

# Import functions directly from pyconvexity
from pyconvexity.core.database import open_connection
from pyconvexity.core.errors import AttributeNotFound
from pyconvexity.models import (
    list_components_by_type, list_carriers, get_network_info,
    get_network_time_periods, get_attribute, list_component_attributes,
    get_network_config
)
from pyconvexity.validation import list_validation_rules
from pyconvexity.models.attributes import get_timeseries as get_timeseries_conn

logger = logging.getLogger(__name__)

class ExcelModelExporter:
    """Export entire network model to Excel workbook"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def export_model_to_excel(
        self,
        db_path: str,
        network_id: int,
        output_path: str,
        scenario_id: Optional[int] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Export complete network model to Excel workbook
        
        Args:
            db_path: Database path
            network_id: Network ID to export
            output_path: Excel file output path
            scenario_id: Scenario ID (defaults to master scenario)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Export statistics and metadata
        """
        
        try:
            if progress_callback:
                progress_callback(0, "Starting Excel export...")
            
            # Connect to database
            conn = open_connection(db_path)
            
            if progress_callback:
                progress_callback(5, "Loading network information...")
            
            # Get network information
            network_info = get_network_info(conn, network_id)
            
            # Get master scenario if no scenario specified
            if scenario_id is None:
                cursor = conn.execute(
                    "SELECT id FROM scenarios WHERE network_id = ? AND is_master = TRUE",
                    (network_id,)
                )
                scenario_result = cursor.fetchone()
                if scenario_result:
                    scenario_id = scenario_result[0]
                else:
                    raise ValueError("No master scenario found for network")
            
            if progress_callback:
                progress_callback(10, "Loading carriers...")
            
            # Get carriers
            carriers = list_carriers(conn, network_id)
            
            if progress_callback:
                progress_callback(15, "Loading components...")
            
            # Get all component types
            component_types = ['BUS', 'GENERATOR', 'LOAD', 'LINE', 'LINK', 'STORAGE_UNIT', 'STORE', 'CONSTRAINT']
            
            # Load components by type
            components_by_type = {}
            for comp_type in component_types:
                components = list_components_by_type(conn, network_id, comp_type)
                components_by_type[comp_type] = components
            
            if progress_callback:
                progress_callback(25, "Processing component attributes...")
            
            # Process components and their attributes
            processed_components = {}
            timeseries_data = {}
            
            for comp_type, components in components_by_type.items():
                processed_components[comp_type] = []
                timeseries_data[comp_type] = {}
                
                for component in components:
                    # Check for cancellation during processing
                    if progress_callback:
                        try:
                            progress_callback(None, None)  # Check for cancellation
                        except KeyboardInterrupt:
                            self.logger.info("Excel export cancelled by user")
                            raise
                    
                    # Get component attributes (all possible attributes for this component type)
                    attributes = self._get_component_attributes(conn, component.id, scenario_id, comp_type)
                    
                    # Process component data
                    processed_component = self._process_component_for_excel(
                        component, attributes, carriers, components_by_type
                    )
                    processed_components[comp_type].append(processed_component)
                    
                    # Extract timeseries data
                    for attr_name, attr_data in attributes.items():
                        if isinstance(attr_data, dict) and 'Timeseries' in attr_data:
                            if comp_type not in timeseries_data:
                                timeseries_data[comp_type] = {}
                            if attr_name not in timeseries_data[comp_type]:
                                timeseries_data[comp_type][attr_name] = {}
                            
                            # Handle both new efficient format and legacy format
                            if 'values' in attr_data:
                                # New efficient format - store values directly
                                timeseries_data[comp_type][attr_name][component.name] = attr_data['values']
                            elif 'points' in attr_data:
                                # Legacy format - store the timeseries points
                                timeseries_data[comp_type][attr_name][component.name] = attr_data['points']
            
            if progress_callback:
                progress_callback(50, "Creating Excel workbook...")
            
            # Check for cancellation before starting Excel creation
            if progress_callback:
                try:
                    progress_callback(None, None)  # Check for cancellation
                except KeyboardInterrupt:
                    self.logger.info("Excel export cancelled before workbook creation")
                    raise
            
            # Get scenario information if scenario_id is provided
            scenario_info = None
            if scenario_id is not None:
                scenario_info = self._get_scenario_info(conn, scenario_id)
            
            # Create Excel workbook
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Create overview sheet
                self._create_overview_sheet(writer, network_info, processed_components, scenario_info)
                
                # Create component sheets
                for comp_type in component_types:
                    if processed_components[comp_type]:
                        # Check for cancellation during sheet creation
                        if progress_callback:
                            try:
                                progress_callback(None, None)  # Check for cancellation
                            except KeyboardInterrupt:
                                self.logger.info(f"Excel export cancelled during {comp_type} sheet creation")
                                raise
                        
                        self._create_component_sheet(writer, conn, comp_type, processed_components[comp_type])
                        
                        # Create timeseries sheet if there's timeseries data
                        if comp_type in timeseries_data and timeseries_data[comp_type]:
                            self._create_timeseries_sheet(
                                writer, comp_type, timeseries_data[comp_type], network_id, conn
                            )
                
                # Create carriers sheet
                self._create_carriers_sheet(writer, carriers)
                
                # Create network config sheet
                self._create_network_config_sheet(writer, network_id, conn)
                
                # Create statistics sheet if solve results are available
                self._create_statistics_sheet(writer, network_id, scenario_id, conn)
                
                # Create per-year statistics sheet if available
                self._create_per_year_statistics_sheet(writer, network_id, scenario_id, conn)
            
            if progress_callback:
                progress_callback(100, "Excel export completed")
            
            # Calculate statistics
            stats = self._calculate_export_stats(processed_components, timeseries_data)
            
            return {
                "success": True,
                "message": f"Network exported to Excel: {output_path}",
                "output_path": output_path,
                "stats": stats
            }
            
        except Exception as e:
            self.logger.error(f"Excel export failed: {e}", exc_info=True)
            if progress_callback:
                progress_callback(None, f"Export failed: {str(e)}")
            raise
    
    def _get_component_attributes(self, conn, component_id: int, scenario_id: int, component_type: str) -> Dict[str, Any]:
        """Get all possible attributes for a component type, with values where set"""
        attributes = {}
        
        # Get ALL possible attribute names for this component type from validation rules
        validation_rules = list_validation_rules(conn, component_type)
        
        for rule in validation_rules:
            attr_name = rule.attribute_name
            try:
                # Try to get the attribute value (may not exist)
                attr_value = get_attribute(conn, component_id, attr_name, scenario_id)
                
                if attr_value.variant == "Static":
                    # Extract static value
                    static_value = attr_value.static_value
                    if static_value.data_type() == "float":
                        attributes[attr_name] = static_value.as_f64()
                    elif static_value.data_type() == "int":
                        attributes[attr_name] = int(static_value.as_f64())
                    elif static_value.data_type() == "boolean":
                        attributes[attr_name] = static_value.data["Boolean"]
                    elif static_value.data_type() == "string":
                        attributes[attr_name] = static_value.data["String"]
                    else:
                        attributes[attr_name] = static_value.data
                        
                elif attr_value.variant == "Timeseries":
                    # Use new efficient timeseries access
                    try:
                        timeseries = get_timeseries_conn(conn, component_id, attr_name, scenario_id)
                        if timeseries and timeseries.values:
                            attributes[attr_name] = {
                                'Timeseries': True,
                                'values': timeseries.values
                            }
                        else:
                            # Fallback to legacy method if new method fails
                            attributes[attr_name] = {
                                'Timeseries': True,
                                'points': attr_value.timeseries_value
                            }
                    except Exception as ts_e:
                        self.logger.warning(f"Failed to load timeseries {attr_name} for component {component_id}: {ts_e}")
                        # Fallback to legacy method
                        attributes[attr_name] = {
                            'Timeseries': True,
                            'points': attr_value.timeseries_value
                        }
                    
            except AttributeNotFound:
                # Attribute not set - always use empty string for blank Excel cell
                attributes[attr_name] = ""
                        
            except Exception as e:
                self.logger.warning(f"Failed to load attribute {attr_name} for component {component_id}: {e}")
                # Still include the attribute with empty value
                attributes[attr_name] = ""
                continue
        
        return attributes
    
    def _process_component_for_excel(self, component, attributes: Dict, carriers: List, components_by_type: Dict) -> Dict[str, Any]:
        """Process a component for Excel export"""
        processed = {
            'name': component.name,
            'type': component.component_type.lower(),
        }
        
        # Add carrier name
        if component.carrier_id:
            carrier = next((c for c in carriers if c['id'] == component.carrier_id), None)
            carrier_name = carrier['name'] if carrier else 'CARRIER_NOT_FOUND'
            processed['carrier'] = carrier_name
            self.logger.info(f"Component '{component.name}' has carrier_id={component.carrier_id}, resolved to carrier: {carrier_name}")
        else:
            processed['carrier'] = ''  # Use empty string for no carrier
            self.logger.info(f"Component '{component.name}' has no carrier_id (carrier_id={component.carrier_id})")
        
        # Add bus connections
        if component.bus_id:
            bus = next((b for b in components_by_type.get('BUS', []) if b.id == component.bus_id), None)
            processed['bus'] = bus.name if bus else ''
        else:
            processed['bus'] = ''
        
        if component.bus0_id:
            bus0 = next((b for b in components_by_type.get('BUS', []) if b.id == component.bus0_id), None)
            processed['bus0'] = bus0.name if bus0 else ''
        else:
            processed['bus0'] = ''
        
        if component.bus1_id:
            bus1 = next((b for b in components_by_type.get('BUS', []) if b.id == component.bus1_id), None)
            processed['bus1'] = bus1.name if bus1 else ''
        else:
            processed['bus1'] = ''
        
        # Add coordinates
        processed['latitude'] = component.latitude if component.latitude is not None else ''
        processed['longitude'] = component.longitude if component.longitude is not None else ''
        
        # Add attributes
        for attr_name, attr_value in attributes.items():
            if isinstance(attr_value, dict) and 'Timeseries' in attr_value:
                processed[attr_name] = '[timeseries]'
            else:
                # Special handling for carrier attribute - don't overwrite relationship carrier
                if attr_name == 'carrier':
                    if component.carrier_id is not None:
                        self.logger.info(f"DEBUG: Skipping carrier attribute '{attr_value}' for '{component.name}' - using relationship carrier '{processed['carrier']}'")
                        continue  # Skip the carrier attribute, keep the relationship carrier
                    else:
                        self.logger.info(f"DEBUG: Using carrier attribute '{attr_value}' for '{component.name}' (no relationship carrier)")
                
                processed[attr_name] = attr_value
        
        self.logger.info(f"DEBUG: Final processed data for '{component.name}': carrier='{processed.get('carrier', 'NOT_SET')}'")
        return processed
    
    def _filter_component_columns(self, conn, component_data: Dict[str, Any], component_type: str) -> Dict[str, Any]:
        """Filter out unused columns based on component type, following DatabaseTable logic"""
        
        filtered_data = {}
        
        # Always include basic fields (name, carrier, latitude, longitude)
        # Note: bus connections are NOT basic fields - they are component-type specific
        # Note: "type" is NOT included - it's implicit based on the sheet/component type
        # Note: CONSTRAINT components don't have carrier, latitude, or longitude - they are code-based rules
        if component_type.upper() == 'CONSTRAINT':
            basic_fields = ['name']  # Constraints only have name - no physical location or carrier
        else:
            basic_fields = ['name', 'carrier', 'latitude', 'longitude']
        
        for field in basic_fields:
            if field in component_data:
                filtered_data[field] = component_data[field]
                self.logger.info(f"Added basic field '{field}' = '{component_data[field]}' for component type {component_type}")
                if field == 'carrier':
                    self.logger.info(f"DEBUG: Setting carrier field to '{component_data[field]}' from component_data")
        
        # Add bus connection columns based on component type - EXACT DatabaseTable logic
        component_type_lower = component_type.lower()
        needs_bus_connection = component_type_lower in ['generator', 'load', 'storage_unit', 'store', 'unmet_load']
        needs_two_bus_connections = component_type_lower in ['line', 'link']
        

        if needs_bus_connection:
            if 'bus' in component_data:
                filtered_data['bus'] = component_data['bus']
        elif needs_two_bus_connections:
            if 'bus0' in component_data:
                filtered_data['bus0'] = component_data['bus0']
            if 'bus1' in component_data:
                filtered_data['bus1'] = component_data['bus1']
        else:
            # Buses and other components don't get bus connection columns
            self.logger.info(f"No bus connection columns for {component_type_lower}")
        
        # Get validation rules to determine which attributes are input vs output
        try:
            
            # Add all other attributes that aren't filtered out
            for key, value in component_data.items():
                if key in filtered_data:
                    continue  # Already handled
                    
                # Filter out unused attributes following DatabaseTable logic
                should_exclude = False
                exclude_reason = ""
                
                # Note: Carrier attribute exclusion is now handled in _process_component_for_excel
                # to prevent overwriting relationship carriers
                
                # Remove location and carrier attributes for CONSTRAINT components (they don't have physical location or carriers)
                if component_type.upper() == 'CONSTRAINT' and key in ['carrier', 'latitude', 'longitude']:
                    should_exclude = True
                    exclude_reason = f"constraint exclusion - constraints don't have {key}"
                    
                # Remove 'type' and 'unit' attributes for buses (not used in this application)
                elif component_type.upper() == 'BUS' and key in ['type', 'unit']:
                    should_exclude = True
                    exclude_reason = f"bus-specific exclusion ({key})"
                    
                # Remove 'x' and 'y' coordinates for buses only - we use latitude/longitude instead
                elif component_type.upper() == 'BUS' and key in ['x', 'y']:
                    should_exclude = True
                    exclude_reason = f"bus coordinate exclusion ({key})"
                    
                # Remove sub-network and slack generator attributes for buses
                elif component_type.upper() == 'BUS' and key in ['sub_network', 'slack_generator']:
                    should_exclude = True
                    exclude_reason = f"bus network exclusion ({key})"
                
                # CRITICAL: Remove bus connection columns for components that shouldn't have them
                elif key in ['bus', 'bus0', 'bus1']:
                    if key == 'bus' and not needs_bus_connection:
                        should_exclude = True
                        exclude_reason = f"bus connection not needed for {component_type_lower}"
                    elif key in ['bus0', 'bus1'] and not needs_two_bus_connections:
                        should_exclude = True
                        exclude_reason = f"two-bus connection not needed for {component_type_lower}"
                
                
                if should_exclude:
                    self.logger.info(f"Excluded {key}: {exclude_reason}")
                else:
                    # Special handling for carrier attribute - don't overwrite relationship field
                    if key == 'carrier' and 'carrier' in filtered_data:
                        self.logger.info(f"Skipping carrier attribute '{value}' - keeping relationship carrier '{filtered_data['carrier']}'")
                    else:
                        filtered_data[key] = value
                        self.logger.info(f"Added attribute: {key} = {value}")
        
        except Exception as e:
            self.logger.warning(f"Could not load validation rules for filtering: {e}")
            # Fallback: include all attributes except the basic exclusions
            for key, value in component_data.items():
                if key in filtered_data:
                    continue
                if key == 'carrier':  # Skip carrier attribute
                    continue
                filtered_data[key] = value
        
        
        return filtered_data
    
    def _create_overview_sheet(self, writer, network_info: Dict, processed_components: Dict, scenario_info: Dict = None):
        """Create overview sheet with network metadata"""
        # Create key-value pairs as separate lists for two columns
        keys = []
        values = []
        
        # Network information
        keys.extend(['Name', 'Description', 'Time Start', 'Time End', 'Time Interval'])
        values.extend([
            network_info['name'],
            network_info.get('description', ''),
            network_info['time_start'],
            network_info['time_end'],
            network_info['time_interval']
        ])
        
        # Scenario information
        if scenario_info:
            keys.append('')
            values.append('')
            keys.extend(['Scenario Information', 'Scenario Name', 'Scenario Description', 'Is Master Scenario', 'Scenario Created'])
            values.extend([
                '',
                scenario_info.get('name', 'Unknown'),
                scenario_info.get('description', '') or 'No description',
                'Yes' if scenario_info.get('is_master', False) else 'No',
                scenario_info.get('created_at', '')
            ])
        
        # Empty row
        keys.append('')
        values.append('')
        
        # Export information
        keys.extend(['Export Information', 'Export Date', 'Export Version'])
        values.extend(['', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self._get_app_version()])
        
        # Create two-column DataFrame
        df = pd.DataFrame({
            'Property': keys,
            'Value': values
        })
        df.to_excel(writer, sheet_name='Overview', index=False)
    
    def _get_scenario_info(self, conn, scenario_id: int) -> Dict[str, Any]:
        """Get scenario information from database"""
        try:
            cursor = conn.execute("""
                SELECT id, network_id, name, description, is_master, created_at
                FROM scenarios 
                WHERE id = ?
            """, (scenario_id,))
            
            row = cursor.fetchone()
            if not row:
                self.logger.warning(f"No scenario found with ID {scenario_id}")
                return {}
            
            return {
                'id': row[0],
                'network_id': row[1],
                'name': row[2],
                'description': row[3],
                'is_master': bool(row[4]),
                'created_at': row[5]
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve scenario info: {e}")
            return {}
    
    def _create_component_sheet(self, writer, conn, component_type: str, components: List[Dict]):
        """Create a sheet for a specific component type"""
        if not components:
            return
        
        # Apply column filtering to each component
        filtered_components = []
        for component in components:
            filtered_component = self._filter_component_columns(conn, component, component_type)
            filtered_components.append(filtered_component)
        
        # Convert to DataFrame
        df = pd.DataFrame(filtered_components)
        
        # Reorder columns to put core fields first
        core_columns = ['name', 'carrier', 'bus', 'bus0', 'bus1', 'latitude', 'longitude']
        other_columns = []
        for col in df.columns:
            if col not in core_columns:
                other_columns.append(col)
        ordered_columns = []
        for col in core_columns:
            if col in df.columns:
                ordered_columns.append(col)
        ordered_columns.extend(other_columns)
        
        df = df[ordered_columns]
        
        # Write to Excel with proper pluralization
        sheet_name_mapping = {
            'BUS': 'Buses',
            'GENERATOR': 'Generators', 
            'LOAD': 'Loads',
            'LINE': 'Lines',
            'LINK': 'Links',
            'STORAGE_UNIT': 'Storage Units',
            'STORE': 'Stores',
            'CONSTRAINT': 'Constraints'
        }
        sheet_name = sheet_name_mapping.get(component_type, f"{component_type.title()}s")
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    def _create_timeseries_sheet(self, writer, component_type: str, timeseries_data: Dict, network_id: int, conn):
        """Create a timeseries sheet for a component type"""
        # Get network time periods
        time_periods = get_network_time_periods(conn, network_id)
        if not time_periods:
            self.logger.warning(f"No time periods found for network {network_id}, skipping timeseries sheet for {component_type}")
            return
        
        self.logger.info(f"Creating timeseries sheet for {component_type} with {len(time_periods)} time periods")
        self.logger.info(f"First few time periods: {[(p.formatted_time, p.timestamp, p.period_index) for p in time_periods[:3]]}")
        
        # Create DataFrame with human-readable timestamps
        timestamps = [period.formatted_time for period in time_periods]  # Use formatted_time instead of timestamp
        df_data = {'timestamp': timestamps}
        
        # Add component columns for each attribute
        for attr_name, component_data in timeseries_data.items():
            for component_name, timeseries_data_item in component_data.items():
                if isinstance(timeseries_data_item, list):
                    # Handle efficient format (list of values)
                    values = timeseries_data_item
                    
                    # Pad or truncate to match time periods
                    while len(values) < len(timestamps):
                        values.append(0)
                    values = values[:len(timestamps)]
                    df_data[f"{component_name}_{attr_name}"] = values
        
        df = pd.DataFrame(df_data)
        sheet_name = f"{component_type.title()} Timeseries"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        self.logger.info(f"Created timeseries sheet '{sheet_name}' with {len(df)} rows and {len(df.columns)} columns")
    
    def _create_carriers_sheet(self, writer, carriers: List[Dict]):
        """Create carriers sheet"""
        if not carriers:
            return
        
        df = pd.DataFrame(carriers)
        df.to_excel(writer, sheet_name='Carriers', index=False)
    
    def _create_network_config_sheet(self, writer, network_id: int, conn):
        """Create network configuration sheet"""
        try:
            config = get_network_config(conn, network_id, None)  # Master scenario
            if config:
                config_data = []
                for param_name, param_value in config.items():
                    config_data.append({
                        'Parameter': param_name,
                        'Value': str(param_value),
                        'Type': type(param_value).__name__,
                        'Description': ''
                    })
                
                if config_data:
                    df = pd.DataFrame(config_data)
                    df.to_excel(writer, sheet_name='Network Config', index=False)
        except Exception as e:
            self.logger.warning(f"Could not create network config sheet: {e}")
    
    def _calculate_export_stats(self, processed_components: Dict, timeseries_data: Dict) -> Dict[str, Any]:
        """Calculate export statistics"""
        total_components = sum(len(components) for components in processed_components.values())
        total_timeseries = sum(
            len(attr_data) 
            for comp_data in timeseries_data.values() 
            for attr_data in comp_data.values()
        )
        
        return {
            'total_components': total_components,
            'total_timeseries': total_timeseries,
            'component_types': len(processed_components),
            'components_by_type': {
                comp_type: len(components) 
                for comp_type, components in processed_components.items()
            }
        } 

    def _get_solve_results(self, conn, network_id: int, scenario_id: int) -> Optional[Dict[str, Any]]:
        """Get solve results from the database"""
        try:
            cursor = conn.execute("""
                SELECT results_json, metadata_json, solver_name, solve_status, 
                       objective_value, solve_time_seconds, solved_at
                FROM network_solve_results 
                WHERE network_id = ? AND scenario_id = ?
            """, (network_id, scenario_id))
            
            row = cursor.fetchone()
            if not row:
                self.logger.info(f"No solve results found for network {network_id}, scenario {scenario_id}")
                return None
            
            results_json_str, metadata_json_str, solver_name, solve_status, objective_value, solve_time, solved_at = row
            
            # Parse the JSON results
            if results_json_str:
                results = json.loads(results_json_str)
                # Add metadata from the table columns
                results['solver_name'] = solver_name
                results['solve_status'] = solve_status
                results['objective_value'] = objective_value
                results['solve_time_seconds'] = solve_time
                results['solved_at'] = solved_at
                
                if metadata_json_str:
                    metadata = json.loads(metadata_json_str)
                    results['metadata'] = metadata
                
                return results
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve solve results: {e}")
            return None
    
    def _get_solve_results_by_year(self, conn, network_id: int, scenario_id: int) -> Optional[Dict[int, Dict[str, Any]]]:
        """Get per-year solve results from the database"""
        try:
            cursor = conn.execute("""
                SELECT year, results_json, metadata_json
                FROM network_solve_results_by_year 
                WHERE network_id = ? AND scenario_id = ?
                ORDER BY year
            """, (network_id, scenario_id))
            
            rows = cursor.fetchall()
            if not rows:
                self.logger.info(f"No per-year solve results found for network {network_id}, scenario {scenario_id}")
                return None
            
            year_results = {}
            for row in rows:
                year, results_json_str, metadata_json_str = row
                
                if results_json_str:
                    year_data = json.loads(results_json_str)
                    
                    # Add metadata if available
                    if metadata_json_str:
                        metadata = json.loads(metadata_json_str)
                        year_data['metadata'] = metadata
                    
                    year_results[year] = year_data
            
            return year_results if year_results else None
            
        except Exception as e:
            self.logger.warning(f"Failed to retrieve per-year solve results: {e}")
            return None
    
    def _create_statistics_sheet(self, writer, network_id: int, scenario_id: int, conn):
        """Create statistics sheet with full-run solve results (no per-year data)"""
        try:
            # Get solve results
            solve_results = self._get_solve_results(conn, network_id, scenario_id)
            if not solve_results:
                self.logger.info("No solve results available, skipping statistics sheet")
                return
            
            # Prepare data for the statistics sheet
            stats_data = []
            
            # Section 1: Solve Summary
            stats_data.extend([
                ['SOLVE SUMMARY', ''],
                ['Solver Name', solve_results.get('solver_name', 'Unknown')],
                ['Solve Status', solve_results.get('solve_status', 'Unknown')],
                ['Solve Time (seconds)', solve_results.get('solve_time_seconds', 0)],
                ['Objective Value', solve_results.get('objective_value', 0)],
                ['Solved At', solve_results.get('solved_at', '')],
                ['', '']  # Empty row separator
            ])
            
            # Extract network statistics if available
            network_stats = solve_results.get('network_statistics', {})
            
            # Section 2: Core Network Statistics
            core_summary = network_stats.get('core_summary', {})
            if core_summary:
                stats_data.extend([
                    ['CORE NETWORK STATISTICS', ''],
                    ['Total Generation (MWh)', core_summary.get('total_generation_mwh', 0)],
                    ['Total Demand (MWh)', core_summary.get('total_demand_mwh', 0)],
                    ['Total Cost', core_summary.get('total_cost', 0)],
                    ['Load Factor', core_summary.get('load_factor', 0)],
                    ['Unserved Energy (MWh)', core_summary.get('unserved_energy_mwh', 0)],
                    ['', '']
                ])
            
            # Section 3: Custom Statistics
            custom_stats = network_stats.get('custom_statistics', {})
            if custom_stats:
                # Emissions by Carrier
                emissions = custom_stats.get('emissions_by_carrier', {})
                if emissions:
                    stats_data.extend([
                        ['EMISSIONS BY CARRIER (tons CO2)', '']
                    ])
                    for carrier, value in emissions.items():
                        if value > 0:  # Only show carriers with emissions
                            stats_data.append([carrier, value])
                    stats_data.extend([
                        ['Total Emissions (tons CO2)', custom_stats.get('total_emissions_tons_co2', 0)],
                        ['', '']
                    ])
                
                # Generation Dispatch by Carrier
                dispatch = custom_stats.get('dispatch_by_carrier', {})
                if dispatch:
                    stats_data.extend([
                        ['GENERATION DISPATCH BY CARRIER (MWh)', '']
                    ])
                    for carrier, value in dispatch.items():
                        if value > 0:  # Only show carriers with generation
                            stats_data.append([carrier, value])
                    stats_data.append(['', ''])
                
                # Power Capacity by Carrier (MW)
                power_capacity = custom_stats.get('power_capacity_by_carrier', {})
                if power_capacity:
                    stats_data.extend([
                        ['POWER CAPACITY BY CARRIER (MW)', '']
                    ])
                    for carrier, value in power_capacity.items():
                        if value > 0:  # Only show carriers with capacity
                            stats_data.append([carrier, value])
                    stats_data.append(['', ''])
                
                # Energy Capacity by Carrier (MWh)
                energy_capacity = custom_stats.get('energy_capacity_by_carrier', {})
                if energy_capacity:
                    stats_data.extend([
                        ['ENERGY CAPACITY BY CARRIER (MWh)', '']
                    ])
                    for carrier, value in energy_capacity.items():
                        if value > 0:  # Only show carriers with capacity
                            stats_data.append([carrier, value])
                    stats_data.append(['', ''])
                
                # Capital Costs by Carrier
                capital_costs = custom_stats.get('capital_cost_by_carrier', {})
                if capital_costs:
                    stats_data.extend([
                        ['CAPITAL COSTS BY CARRIER', '']
                    ])
                    for carrier, value in capital_costs.items():
                        if value > 0:  # Only show carriers with costs
                            stats_data.append([carrier, value])
                    stats_data.extend([
                        ['Total Capital Cost', custom_stats.get('total_capital_cost', 0)],
                        ['', '']
                    ])
                
                # Operational Costs by Carrier
                op_costs = custom_stats.get('operational_cost_by_carrier', {})
                if op_costs:
                    stats_data.extend([
                        ['OPERATIONAL COSTS BY CARRIER', '']
                    ])
                    for carrier, value in op_costs.items():
                        if value > 0:  # Only show carriers with costs
                            stats_data.append([carrier, value])
                    stats_data.extend([
                        ['Total Operational Cost', custom_stats.get('total_operational_cost', 0)],
                        ['', '']
                    ])
                
                # Total System Costs by Carrier
                total_costs = custom_stats.get('total_system_cost_by_carrier', {})
                if total_costs:
                    stats_data.extend([
                        ['TOTAL SYSTEM COSTS BY CARRIER', '']
                    ])
                    for carrier, value in total_costs.items():
                        if value > 0:  # Only show carriers with costs
                            stats_data.append([carrier, value])
                    stats_data.extend([
                        ['Total Currency Cost', custom_stats.get('total_currency_cost', 0)],
                        ['Average Price per MWh', custom_stats.get('average_price_per_mwh', 0)],
                        ['', '']
                    ])
                
                # Unmet Load Statistics
                unmet_stats = custom_stats.get('unmet_load_statistics', {})
                if unmet_stats:
                    stats_data.extend([
                        ['UNMET LOAD STATISTICS', ''],
                        ['Unmet Load (MWh)', unmet_stats.get('unmet_load_mwh', 0)],
                        ['Unmet Load Percentage', custom_stats.get('unmet_load_percentage', 0)],
                        ['Max Unmet Load Hour (MW)', custom_stats.get('max_unmet_load_hour_mw', 0)],
                        ['', '']
                    ])
            
            # Section 4: Component Storage Statistics
            storage_stats = solve_results.get('component_storage_stats', {})
            if storage_stats:
                stats_data.extend([
                    ['COMPONENT STORAGE STATISTICS', '']
                ])
                for key, value in storage_stats.items():
                    # Convert snake_case to readable format
                    readable_key = key.replace('_', ' ').title()
                    stats_data.append([readable_key, value])
                stats_data.append(['', ''])
            
            # Section 5: Runtime Information
            runtime_info = network_stats.get('runtime_info', {})
            if runtime_info:
                stats_data.extend([
                    ['RUNTIME INFORMATION', '']
                ])
                for key, value in runtime_info.items():
                    # Convert snake_case to readable format
                    readable_key = key.replace('_', ' ').title()
                    stats_data.append([readable_key, value])
                stats_data.append(['', ''])
            
            # Section 6: Solver Information
            solver_info = network_stats.get('solver_info', {})
            if solver_info:
                stats_data.extend([
                    ['SOLVER INFORMATION', '']
                ])
                for key, value in solver_info.items():
                    # Convert snake_case to readable format
                    readable_key = key.replace('_', ' ').title()
                    stats_data.append([readable_key, value])
                stats_data.append(['', ''])
            
            # Create DataFrame and write to Excel (simple 2-column format)
            if stats_data:
                df = pd.DataFrame(stats_data, columns=['Parameter', 'Value'])
                df.to_excel(writer, sheet_name='Statistics', index=False)
                self.logger.info(f"Created Statistics sheet with {len(stats_data)} rows")
            
        except Exception as e:
            self.logger.warning(f"Failed to create statistics sheet: {e}")
            # Don't fail the entire export if statistics sheet fails
    
    def _create_per_year_statistics_sheet(self, writer, network_id: int, scenario_id: int, conn):
        """Create per-year statistics sheet in tidy data format"""
        try:
            # Get per-year solve results
            year_results = self._get_solve_results_by_year(conn, network_id, scenario_id)
            if not year_results:
                self.logger.info("No per-year solve results available, skipping per-year statistics sheet")
                return
            
            # Prepare tidy data: Variable, Year, Carrier, Value, Units
            tidy_data = []
            
            # Get sorted years
            years = sorted(year_results.keys())
            
            # Define the statistics we want to include with their units
            stat_definitions = [
                ('dispatch_by_carrier', 'Generation Dispatch', 'MWh'),
                ('power_capacity_by_carrier', 'Power Capacity', 'MW'),
                ('energy_capacity_by_carrier', 'Energy Capacity', 'MWh'),
                ('capital_cost_by_carrier', 'Capital Cost', 'Currency'),
                ('operational_cost_by_carrier', 'Operational Cost', 'Currency'),
                ('total_system_cost_by_carrier', 'Total System Cost', 'Currency'),
                ('emissions_by_carrier', 'Emissions', 'tons CO2')
            ]
            
            # Process each statistic type
            for stat_key, stat_name, units in stat_definitions:
                # Collect all carriers across all years for this statistic
                all_carriers = set()
                for year in years:
                    year_data = year_results[year]
                    if 'network_statistics' in year_data and 'custom_statistics' in year_data['network_statistics']:
                        custom_stats = year_data['network_statistics']['custom_statistics']
                        if stat_key in custom_stats:
                            all_carriers.update(custom_stats[stat_key].keys())
                
                # Add data rows for each carrier and year combination
                for carrier in sorted(all_carriers):
                    for year in years:
                        year_data = year_results[year]
                        value = 0.0
                        
                        if 'network_statistics' in year_data and 'custom_statistics' in year_data['network_statistics']:
                            custom_stats = year_data['network_statistics']['custom_statistics']
                            if stat_key in custom_stats and carrier in custom_stats[stat_key]:
                                value = custom_stats[stat_key][carrier]
                        
                        # Only include rows with non-zero values to keep the data clean
                        if value > 0:
                            tidy_data.append([stat_name, year, carrier, value, units])
            
            # Add core summary statistics (these don't have carriers)
            core_stat_definitions = [
                ('total_generation_mwh', 'Total Generation', 'MWh'),
                ('total_demand_mwh', 'Total Demand', 'MWh'),
                ('total_cost', 'Total Cost', 'Currency'),
                ('load_factor', 'Load Factor', 'Ratio'),
                ('unserved_energy_mwh', 'Unserved Energy', 'MWh'),
                ('total_emissions_tons_co2', 'Total Emissions', 'tons CO2')
            ]
            
            for stat_key, stat_name, units in core_stat_definitions:
                for year in years:
                    year_data = year_results[year]
                    value = 0.0
                    
                    # Check both core_summary and custom_statistics
                    if 'network_statistics' in year_data:
                        network_stats = year_data['network_statistics']
                        
                        # Try core_summary first
                        if 'core_summary' in network_stats and stat_key in network_stats['core_summary']:
                            value = network_stats['core_summary'][stat_key]
                        # Try custom_statistics as fallback
                        elif 'custom_statistics' in network_stats and stat_key in network_stats['custom_statistics']:
                            value = network_stats['custom_statistics'][stat_key]
                    
                    # Include all core statistics (even zeros for completeness)
                    tidy_data.append([stat_name, year, 'Total', value, units])
            
            # Create DataFrame and write to Excel
            if tidy_data:
                df = pd.DataFrame(tidy_data, columns=['Variable', 'Year', 'Carrier', 'Value', 'Units'])
                df.to_excel(writer, sheet_name='Per-Year Statistics', index=False)
                self.logger.info(f"Created Per-Year Statistics sheet with {len(tidy_data)} rows")
            else:
                self.logger.info("No per-year statistics data to export")
            
        except Exception as e:
            self.logger.warning(f"Failed to create per-year statistics sheet: {e}")
            # Don't fail the entire export if per-year statistics sheet fails
    
    def _get_app_version(self) -> str:
        """Get the application version."""
        try:
            # Try to read from package.json in the project root
            import json
            import os
            from pathlib import Path
            
            # Look for package.json in parent directories
            current_dir = Path(__file__).parent
            while current_dir != current_dir.parent:
                package_json = current_dir / "package.json"
                if package_json.exists():
                    with open(package_json, "r") as f:
                        package_data = json.load(f)
                        return package_data.get("version", "1.0.0")
                current_dir = current_dir.parent
            
            # Fallback version
            return "1.0.0"
        except Exception as e:
            self.logger.warning(f"Could not get app version: {e}")
            return "1.0.0"
