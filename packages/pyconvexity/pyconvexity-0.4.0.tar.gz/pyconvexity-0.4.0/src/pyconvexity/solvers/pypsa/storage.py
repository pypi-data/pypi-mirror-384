"""
Result storage functionality for PyPSA solver integration.

Handles storing solve results back to the database with proper validation and error handling.
"""

import logging
import uuid
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Callable

from pyconvexity.core.types import StaticValue
from pyconvexity.models import (
    list_components_by_type, set_static_attribute, set_timeseries_attribute
)
from pyconvexity.validation import get_validation_rule

logger = logging.getLogger(__name__)


class ResultStorage:
    """
    Handles storing PyPSA solve results back to the database.
    
    This class manages the complex process of extracting results from PyPSA networks
    and storing them back to the database with proper validation and error handling.
    """
    
    def store_results(
        self,
        conn,
        network_id: int,
        network: 'pypsa.Network',
        solve_result: Dict[str, Any],
        scenario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Store complete solve results back to database.
        
        Args:
            conn: Database connection
            network_id: ID of the network
            network: Solved PyPSA Network object
            solve_result: Solve result metadata
            scenario_id: Optional scenario ID
            
        Returns:
            Dictionary with storage statistics
        """
        run_id = solve_result.get('run_id', str(uuid.uuid4()))
        
        try:
            # Store component results
            component_stats = self._store_component_results(
                conn, network_id, network, scenario_id
            )
            
            # Calculate network statistics first
            network_stats = self._calculate_network_statistics(
                conn, network_id, network, solve_result
            )
            
            # Store solve summary with network statistics
            self._store_solve_summary(
                conn, network_id, solve_result, scenario_id, network_stats
            )
            
            # Store year-based statistics if available
            year_stats_stored = 0
            if solve_result.get('year_statistics'):
                year_stats_stored = self._store_year_based_statistics(
                    conn, network_id, network, solve_result['year_statistics'], scenario_id
                )
            
            return {
                "component_stats": component_stats,
                "network_stats": network_stats,
                "year_stats_stored": year_stats_stored,
                "run_id": run_id,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to store solve results: {e}", exc_info=True)
            return {
                "component_stats": {},
                "network_stats": {},
                "run_id": run_id,
                "success": False,
                "error": str(e)
            }
    
    def _store_component_results(
        self,
        conn,
        network_id: int,
        network: 'pypsa.Network',
        scenario_id: Optional[int]
    ) -> Dict[str, int]:
        """Store results for all component types."""
        results_stats = {
            "stored_bus_results": 0,
            "stored_generator_results": 0,
            "stored_unmet_load_results": 0,
            "stored_load_results": 0,
            "stored_line_results": 0,
            "stored_link_results": 0,
            "stored_storage_unit_results": 0,
            "stored_store_results": 0,
            "skipped_attributes": 0,
            "errors": 0
        }
        
        try:
            # Store bus results
            if hasattr(network, 'buses_t') and network.buses_t:
                results_stats["stored_bus_results"] = self._store_component_type_results(
                    conn, network_id, 'BUS', network.buses, network.buses_t, scenario_id
                )
            
            # Store generator results (includes regular generators)
            if hasattr(network, 'generators_t') and network.generators_t:
                results_stats["stored_generator_results"] = self._store_component_type_results(
                    conn, network_id, 'GENERATOR', network.generators, network.generators_t, scenario_id
                )
                
                # Store UNMET_LOAD results (these are also stored as generators in PyPSA)
                results_stats["stored_unmet_load_results"] = self._store_component_type_results(
                    conn, network_id, 'UNMET_LOAD', network.generators, network.generators_t, scenario_id
                )
            
            # Store load results
            if hasattr(network, 'loads_t') and network.loads_t:
                results_stats["stored_load_results"] = self._store_component_type_results(
                    conn, network_id, 'LOAD', network.loads, network.loads_t, scenario_id
                )
            
            # Store line results
            if hasattr(network, 'lines_t') and network.lines_t:
                results_stats["stored_line_results"] = self._store_component_type_results(
                    conn, network_id, 'LINE', network.lines, network.lines_t, scenario_id
                )
            
            # Store link results
            if hasattr(network, 'links_t') and network.links_t:
                results_stats["stored_link_results"] = self._store_component_type_results(
                    conn, network_id, 'LINK', network.links, network.links_t, scenario_id
                )
            
            # Store storage unit results
            if hasattr(network, 'storage_units_t') and network.storage_units_t:
                results_stats["stored_storage_unit_results"] = self._store_component_type_results(
                    conn, network_id, 'STORAGE_UNIT', network.storage_units, network.storage_units_t, scenario_id
                )
            
            # Store store results
            if hasattr(network, 'stores_t') and network.stores_t:
                results_stats["stored_store_results"] = self._store_component_type_results(
                    conn, network_id, 'STORE', network.stores, network.stores_t, scenario_id
                )
            
            return results_stats
            
        except Exception as e:
            logger.error(f"Error storing solve results: {e}", exc_info=True)
            results_stats["errors"] += 1
            return results_stats
    
    def _store_component_type_results(
        self,
        conn,
        network_id: int,
        component_type: str,
        static_df: pd.DataFrame,
        timeseries_dict: Dict[str, pd.DataFrame],
        scenario_id: Optional[int]
    ) -> int:
        """Store results for a specific component type - only store OUTPUT attributes."""
        stored_count = 0
        
        try:
            # Get component name to ID mapping
            components = list_components_by_type(conn, network_id, component_type)
            name_to_id = {comp.name: comp.id for comp in components}
            
            # Store timeseries results - ONLY OUTPUT ATTRIBUTES (is_input=FALSE)
            for attr_name, timeseries_df in timeseries_dict.items():
                if timeseries_df.empty:
                    continue
                
                # Check if this attribute is an output attribute (not an input)
                try:
                    rule = get_validation_rule(conn, component_type, attr_name)
                    if rule.is_input:
                        # Skip input attributes to preserve original input data
                        continue
                except Exception:
                    # If no validation rule found, skip to be safe
                    continue
                
                for component_name in timeseries_df.columns:
                    if component_name not in name_to_id:
                        continue
                    
                    component_id = name_to_id[component_name]
                    component_series = timeseries_df[component_name]
                    
                    # Skip if all values are NaN
                    if component_series.isna().all():
                        continue
                    
                    # Convert to efficient values array
                    values = []
                    for value in component_series.values:
                        if pd.isna(value):
                            values.append(0.0)  # Fill NaN with 0.0
                        else:
                            values.append(float(value))
                    
                    if not values:
                        continue
                    
                    # Store using efficient format
                    try:
                        set_timeseries_attribute(conn, component_id, attr_name, values, scenario_id)
                        stored_count += 1
                    except Exception as e:
                        # Handle validation errors gracefully
                        if ("No validation rule found" in str(e) or 
                            "does not allow" in str(e) or
                            "ValidationError" in str(type(e).__name__)):
                            continue
                        else:
                            logger.warning(f"Error storing timeseries {attr_name} for {component_type} '{component_name}': {e}")
                            continue
            
            # Store static optimization results - ONLY OUTPUT ATTRIBUTES (is_input=FALSE)
            if not static_df.empty:
                for attr_name in static_df.columns:
                    # Check if this attribute is an output attribute (not an input)
                    try:
                        rule = get_validation_rule(conn, component_type, attr_name)
                        if rule.is_input:
                            # Skip input attributes to preserve original input data
                            continue
                    except Exception:
                        # If no validation rule found, skip to be safe
                        continue
                    
                    for component_name, value in static_df[attr_name].items():
                        if component_name not in name_to_id or pd.isna(value):
                            continue
                        
                        component_id = name_to_id[component_name]
                        
                        try:
                            # Convert value to StaticValue
                            if isinstance(value, (int, np.integer)):
                                static_value = StaticValue(int(value))
                            elif isinstance(value, (float, np.floating)):
                                if np.isfinite(value):
                                    static_value = StaticValue(float(value))
                                else:
                                    continue  # Skip infinite/NaN values
                            elif isinstance(value, bool):
                                static_value = StaticValue(bool(value))
                            else:
                                static_value = StaticValue(str(value))
                            
                            # Store using atomic utility
                            set_static_attribute(conn, component_id, attr_name, static_value, scenario_id)
                            stored_count += 1
                            
                        except Exception as e:
                            # Handle validation errors gracefully
                            if ("No validation rule found" in str(e) or 
                                "does not allow" in str(e) or
                                "ValidationError" in str(type(e).__name__)):
                                continue
                            else:
                                logger.warning(f"Error storing static {attr_name} for {component_type} '{component_name}': {e}")
                                continue
            
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing results for {component_type}: {e}", exc_info=True)
            return stored_count
    
    def _store_solve_summary(
        self,
        conn,
        network_id: int,
        solve_result: Dict[str, Any],
        scenario_id: Optional[int],
        network_stats: Optional[Dict[str, Any]] = None
    ):
        """Store solve summary to network_solve_results table."""
        try:
            # Prepare solve summary data
            solver_name = solve_result.get('solver_name', 'unknown')
            solve_status = solve_result.get('status', 'unknown')
            objective_value = solve_result.get('objective_value')
            solve_time = solve_result.get('solve_time', 0.0)
            
            # Use master scenario if no scenario specified
            if scenario_id is None:
                from pyconvexity.models import get_master_scenario_id
                scenario_id = get_master_scenario_id(conn, network_id)
            
            # Create enhanced solve result with network statistics for serialization
            enhanced_solve_result = {
                **solve_result,
                "network_statistics": network_stats or {}
            }
            
            # Store solve results summary
            conn.execute("""
                INSERT OR REPLACE INTO network_solve_results (
                    network_id, scenario_id, solver_name, solve_type, solve_status,
                    objective_value, solve_time_seconds, results_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                network_id,
                scenario_id,
                solver_name,
                'pypsa_optimization',
                solve_status,
                objective_value,
                solve_time,
                self._serialize_results_json(enhanced_solve_result),
                self._serialize_metadata_json(enhanced_solve_result)
            ))
            
            logger.info(f"Stored solve summary for network {network_id}, scenario {scenario_id}")
            
        except Exception as e:
            logger.error(f"Failed to store solve summary: {e}", exc_info=True)
    
    def _calculate_network_statistics(
        self,
        conn,
        network_id: int,
        network: 'pypsa.Network',
        solve_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate network statistics - focusing only on capacity for now."""
        try:
            # Calculate carrier-specific statistics
            carrier_stats = self._calculate_carrier_statistics(conn, network_id, network)
            
            # Calculate basic network statistics
            total_cost = solve_result.get('objective_value', 0.0)
            total_generation_mwh = sum(carrier_stats.get("dispatch_by_carrier", {}).values())
            total_emissions_tonnes = sum(carrier_stats.get("emissions_by_carrier", {}).values())
            total_capital_cost = sum(carrier_stats.get("capital_cost_by_carrier", {}).values())
            total_operational_cost = sum(carrier_stats.get("operational_cost_by_carrier", {}).values())
            total_system_cost = sum(carrier_stats.get("total_system_cost_by_carrier", {}).values())
            
            # Calculate unmet load statistics
            unmet_load_mwh = carrier_stats.get("dispatch_by_carrier", {}).get("Unmet Load", 0.0)
            total_demand_mwh = self._calculate_total_demand(network)
            unmet_load_percentage = (unmet_load_mwh / (total_demand_mwh + 1e-6)) * 100 if total_demand_mwh > 0 else 0.0
            
            # Create nested structure expected by frontend
            network_statistics = {
                "core_summary": {
                    "total_generation_mwh": total_generation_mwh,
                    "total_demand_mwh": total_demand_mwh,
                    "total_cost": total_cost,
                    "load_factor": (total_demand_mwh / (total_generation_mwh + 1e-6)) if total_generation_mwh > 0 else 0.0,
                    "unserved_energy_mwh": unmet_load_mwh
                },
                "custom_statistics": {
                    # Include carrier-specific statistics (capacity, dispatch, emissions, costs)
                    **carrier_stats,
                    "total_capital_cost": total_capital_cost,
                    "total_operational_cost": total_operational_cost,
                    "total_currency_cost": total_system_cost,  # Use calculated system cost instead of PyPSA objective
                    "total_emissions_tons_co2": total_emissions_tonnes,
                    "average_price_per_mwh": (total_system_cost / (total_generation_mwh + 1e-6)) if total_generation_mwh > 0 else 0.0,
                    "unmet_load_percentage": unmet_load_percentage,
                    "max_unmet_load_hour_mw": 0.0       # TODO: Calculate max hourly unmet load later
                },
                "runtime_info": {
                    "component_count": (
                        len(network.buses) + len(network.generators) + len(network.loads) + 
                        len(network.lines) + len(network.links)
                    ) if hasattr(network, 'buses') else 0,
                    "bus_count": len(network.buses) if hasattr(network, 'buses') else 0,
                    "generator_count": len(network.generators) if hasattr(network, 'generators') else 0,
                    "load_count": len(network.loads) if hasattr(network, 'loads') else 0,
                    "snapshot_count": len(network.snapshots) if hasattr(network, 'snapshots') else 0
                }
            }
            
            logger.info(f"Calculated network statistics: core_summary={network_statistics['core_summary']}")
            return network_statistics
            
        except Exception as e:
            logger.error(f"Failed to calculate network statistics: {e}", exc_info=True)
            # Return empty structure matching expected format
            return {
                "core_summary": {
                    "total_generation_mwh": 0.0,
                    "total_demand_mwh": 0.0,
                    "total_cost": solve_result.get('objective_value', 0.0),
                    "load_factor": 0.0,
                    "unserved_energy_mwh": 0.0
                },
                "custom_statistics": {
                    "dispatch_by_carrier": {},
                    "power_capacity_by_carrier": {},
                    "energy_capacity_by_carrier": {},
                    "emissions_by_carrier": {},
                    "capital_cost_by_carrier": {},
                    "operational_cost_by_carrier": {},
                    "total_system_cost_by_carrier": {},
                    "total_capital_cost": 0.0,
                    "total_operational_cost": 0.0,
                    "total_currency_cost": 0.0,
                    "total_emissions_tons_co2": 0.0,
                    "average_price_per_mwh": 0.0,
                    "unmet_load_percentage": 0.0,
                    "max_unmet_load_hour_mw": 0.0
                },
                "runtime_info": {
                    "component_count": 0,
                    "bus_count": 0,
                    "generator_count": 0,
                    "load_count": 0,
                    "snapshot_count": 0
                },
                "error": str(e)
            }
    
    def _calculate_carrier_statistics(self, conn, network_id: int, network: 'pypsa.Network') -> Dict[str, Any]:
        """
        Calculate carrier-specific statistics directly from the network.
        This is the primary calculation - per-year stats will be calculated separately.
        """
        try:
            # Calculate all-year statistics directly from the network
            # Extract years from network snapshots
            if hasattr(network.snapshots, 'levels'):
                # Multi-period optimization - get years from period level
                period_values = network.snapshots.get_level_values(0)
                years = sorted(period_values.unique())
            elif hasattr(network.snapshots, 'year'):
                years = sorted(network.snapshots.year.unique())
            elif hasattr(network, '_available_years'):
                years = network._available_years
            else:
                years = [2020]  # Fallback
            
            logger.info(f"Calculating all-year carrier statistics for years: {years}")
            
            # Calculate per-year statistics first
            all_year_stats = {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},
                "energy_capacity_by_carrier": {},
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
            
            # Initialize all carriers with zero values
            cursor = conn.execute("""
                SELECT DISTINCT name FROM carriers WHERE network_id = ?
            """, (network_id,))
            all_carriers = [row[0] for row in cursor.fetchall()]
            
            # Initialize all carriers with zero values (including special "Unmet Load" carrier)
            all_carriers_with_unmet = all_carriers + ['Unmet Load']
            for carrier in all_carriers_with_unmet:
                all_year_stats["dispatch_by_carrier"][carrier] = 0.0
                all_year_stats["power_capacity_by_carrier"][carrier] = 0.0
                all_year_stats["energy_capacity_by_carrier"][carrier] = 0.0
                all_year_stats["emissions_by_carrier"][carrier] = 0.0
                all_year_stats["capital_cost_by_carrier"][carrier] = 0.0
                all_year_stats["operational_cost_by_carrier"][carrier] = 0.0
                all_year_stats["total_system_cost_by_carrier"][carrier] = 0.0
            
            # Calculate statistics for each year and sum them up
            for year in years:
                year_stats = self._calculate_year_carrier_statistics(conn, network_id, network, year)
                
                # Sum up all the statistics (including "Unmet Load")
                for carrier in all_carriers_with_unmet:
                    # Sum dispatch, emissions, and costs across years
                    all_year_stats["dispatch_by_carrier"][carrier] += year_stats["dispatch_by_carrier"].get(carrier, 0.0)
                    all_year_stats["emissions_by_carrier"][carrier] += year_stats["emissions_by_carrier"].get(carrier, 0.0)
                    all_year_stats["capital_cost_by_carrier"][carrier] += year_stats["capital_cost_by_carrier"].get(carrier, 0.0)
                    all_year_stats["operational_cost_by_carrier"][carrier] += year_stats["operational_cost_by_carrier"].get(carrier, 0.0)
                    all_year_stats["total_system_cost_by_carrier"][carrier] += year_stats["total_system_cost_by_carrier"].get(carrier, 0.0)
                    
                    # For capacity: use the last year (final capacity state)
                    if year == years[-1]:
                        all_year_stats["power_capacity_by_carrier"][carrier] = year_stats["power_capacity_by_carrier"].get(carrier, 0.0)
                        all_year_stats["energy_capacity_by_carrier"][carrier] = year_stats["energy_capacity_by_carrier"].get(carrier, 0.0)
            
            logger.info(f"Calculated all-year carrier statistics:")
            logger.info(f"  Total dispatch: {sum(all_year_stats['dispatch_by_carrier'].values()):.2f} MWh")
            logger.info(f"  Total emissions: {sum(all_year_stats['emissions_by_carrier'].values()):.2f} tonnes CO2")
            logger.info(f"  Total capital cost: {sum(all_year_stats['capital_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Total operational cost: {sum(all_year_stats['operational_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Final power capacity: {sum(all_year_stats['power_capacity_by_carrier'].values()):.2f} MW")
            
            return all_year_stats
            
        except Exception as e:
            logger.error(f"Failed to calculate carrier statistics: {e}", exc_info=True)
            return {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},
                "energy_capacity_by_carrier": {},
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
    
    def _store_year_based_statistics(
        self,
        conn,
        network_id: int,
        network: 'pypsa.Network',
        year_statistics: Dict[int, Dict[str, Any]],
        scenario_id: Optional[int]
    ) -> int:
        """Store year-based statistics to database"""
        try:
            import json
            stored_count = 0
            
            # Use master scenario if no scenario specified
            if scenario_id is None:
                from pyconvexity.models import get_master_scenario_id
                scenario_id = get_master_scenario_id(conn, network_id)
            
            # Check if network_solve_results_by_year table exists, create if not
            conn.execute("""
                CREATE TABLE IF NOT EXISTS network_solve_results_by_year (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network_id INTEGER NOT NULL,
                    scenario_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    results_json TEXT,
                    metadata_json TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (network_id) REFERENCES networks(id),
                    FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                    UNIQUE(network_id, scenario_id, year)
                )
            """)
            
            for year, stats in year_statistics.items():
                try:
                    # Calculate proper year-specific carrier statistics
                    year_carrier_stats = self._calculate_year_carrier_statistics(conn, network_id, network, year)
                    
                    # Merge year-specific carrier stats into the statistics
                    if "custom_statistics" in stats:
                        stats["custom_statistics"].update(year_carrier_stats)
                    else:
                        stats["custom_statistics"] = year_carrier_stats
                    
                    # Wrap the year statistics in the same structure as overall results for consistency
                    year_result_wrapper = {
                        "success": True,
                        "year": year,
                        "network_statistics": stats
                    }
                    
                    metadata = {
                        "year": year,
                        "network_id": network_id,
                        "scenario_id": scenario_id
                    }
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO network_solve_results_by_year 
                        (network_id, scenario_id, year, results_json, metadata_json)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        network_id,
                        scenario_id,
                        year,
                        json.dumps(year_result_wrapper, default=self._json_serializer),
                        json.dumps(metadata, default=self._json_serializer)
                    ))
                    
                    stored_count += 1
                    logger.info(f"Stored year-based statistics for year {year}")
                    
                except Exception as e:
                    logger.error(f"Failed to store statistics for year {year}: {e}")
                    continue
            
            logger.info(f"Successfully stored year-based statistics for {stored_count} years")
            return stored_count
            
        except Exception as e:
            logger.error(f"Failed to store year-based statistics: {e}", exc_info=True)
            return 0
    
    def _calculate_year_carrier_statistics(self, conn, network_id: int, network: 'pypsa.Network', year: int) -> Dict[str, Any]:
        """
        Calculate carrier-specific statistics for a specific year.
        For now, only calculate capacity statistics.
        """
        try:
            # Initialize carrier statistics
            carrier_stats = {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},  # MW - Generators + Storage Units (power) + Lines + Links
                "energy_capacity_by_carrier": {},  # MWh - Stores + Storage Units (energy)
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
            
            # Get all carriers from database
            cursor = conn.execute("""
                SELECT DISTINCT name FROM carriers WHERE network_id = ?
            """, (network_id,))
            all_carriers = [row[0] for row in cursor.fetchall()]
            
            # Initialize all carriers with zero values (including special "Unmet Load" carrier)
            all_carriers_with_unmet = all_carriers + ['Unmet Load']
            for carrier in all_carriers_with_unmet:
                carrier_stats["dispatch_by_carrier"][carrier] = 0.0
                carrier_stats["power_capacity_by_carrier"][carrier] = 0.0
                carrier_stats["energy_capacity_by_carrier"][carrier] = 0.0
                carrier_stats["emissions_by_carrier"][carrier] = 0.0
                carrier_stats["capital_cost_by_carrier"][carrier] = 0.0
                carrier_stats["operational_cost_by_carrier"][carrier] = 0.0
                carrier_stats["total_system_cost_by_carrier"][carrier] = 0.0
            
            # Calculate dispatch (generation) by carrier for this specific year
            
            # 1. GENERATORS - Generation dispatch (including UNMET_LOAD)
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                # Get generator-carrier mapping (include both GENERATOR and UNMET_LOAD)
                cursor = conn.execute("""
                SELECT c.name as component_name, 
                       CASE 
                           WHEN c.component_type = 'UNMET_LOAD' THEN 'Unmet Load'
                           ELSE carr.name 
                       END as carrier_name
                FROM components c
                JOIN carriers carr ON c.carrier_id = carr.id
                WHERE c.network_id = ? AND c.component_type IN ('GENERATOR', 'UNMET_LOAD')
            """, (network_id,))
                generator_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter generation data for this specific year
                year_generation = self._filter_timeseries_by_year(network.generators_t.p, network.snapshots, year)
                if year_generation is not None and not year_generation.empty:
                    for gen_name in year_generation.columns:
                        if gen_name in generator_carriers:
                            carrier_name = generator_carriers[gen_name]
                            
                            # Calculate generation for this year (ALWAYS apply snapshot weightings to convert MW to MWh)
                            year_weightings = self._get_year_weightings(network, year)
                            if year_weightings is not None:
                                generation_mwh = float((year_generation[gen_name].values * year_weightings).sum())
                            else:
                                # Fallback: simple sum (will be incorrect for non-1H models)
                                generation_mwh = float(year_generation[gen_name].sum())
                                logger.warning(f"Could not apply snapshot weightings for {gen_name} in year {year} - energy may be incorrect")
                            
                            if carrier_name in carrier_stats["dispatch_by_carrier"]:
                                carrier_stats["dispatch_by_carrier"][carrier_name] += generation_mwh
            
            # 2. STORAGE_UNITS - Discharge only (positive values)
            if hasattr(network, 'storage_units_t') and hasattr(network.storage_units_t, 'p'):
                # Get storage unit-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORAGE_UNIT'
                """, (network_id,))
                storage_unit_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter storage unit data for this specific year
                year_storage = self._filter_timeseries_by_year(network.storage_units_t.p, network.snapshots, year)
                if year_storage is not None and not year_storage.empty:
                    for su_name in year_storage.columns:
                        if su_name in storage_unit_carriers:
                            carrier_name = storage_unit_carriers[su_name]
                            
                            # Calculate discharge for this year (positive values only, ALWAYS apply snapshot weightings)
                            year_weightings = self._get_year_weightings(network, year)
                            if year_weightings is not None:
                                discharge_mwh = float((year_storage[su_name].clip(lower=0).values * year_weightings).sum())
                            else:
                                # Fallback: simple sum (will be incorrect for non-1H models)
                                discharge_mwh = float(year_storage[su_name].clip(lower=0).sum())
                                logger.warning(f"Could not apply snapshot weightings for storage unit {su_name} in year {year} - energy may be incorrect")
                            
                            if carrier_name in carrier_stats["dispatch_by_carrier"]:
                                carrier_stats["dispatch_by_carrier"][carrier_name] += discharge_mwh
            
            # 3. STORES - Discharge only (positive values)
            if hasattr(network, 'stores_t') and hasattr(network.stores_t, 'p'):
                # Get store-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORE'
                """, (network_id,))
                store_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter store data for this specific year
                year_stores = self._filter_timeseries_by_year(network.stores_t.p, network.snapshots, year)
                if year_stores is not None and not year_stores.empty:
                    for store_name in year_stores.columns:
                        if store_name in store_carriers:
                            carrier_name = store_carriers[store_name]
                            
                            # Calculate discharge for this year (positive values only, ALWAYS apply snapshot weightings)
                            year_weightings = self._get_year_weightings(network, year)
                            if year_weightings is not None:
                                discharge_mwh = float((year_stores[store_name].clip(lower=0).values * year_weightings).sum())
                            else:
                                # Fallback: simple sum (will be incorrect for non-1H models)
                                discharge_mwh = float(year_stores[store_name].clip(lower=0).sum())
                                logger.warning(f"Could not apply snapshot weightings for store {store_name} in year {year} - energy may be incorrect")
                            
                            if carrier_name in carrier_stats["dispatch_by_carrier"]:
                                carrier_stats["dispatch_by_carrier"][carrier_name] += discharge_mwh
            
            # Calculate emissions by carrier for this specific year
            # Get emission factors for all carriers
            cursor = conn.execute("""
                SELECT name, co2_emissions FROM carriers WHERE network_id = ?
            """, (network_id,))
            emission_factors = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Calculate emissions: dispatch (MWh) × emission factor (tonnes CO2/MWh) = tonnes CO2
            for carrier_name, dispatch_mwh in carrier_stats["dispatch_by_carrier"].items():
                # Handle None values safely
                if dispatch_mwh is None:
                    dispatch_mwh = 0.0
                
                emission_factor = emission_factors.get(carrier_name, 0.0)  # Default to 0 if no emission factor
                if emission_factor is None:
                    emission_factor = 0.0
                
                emissions_tonnes = dispatch_mwh * emission_factor
                
                if carrier_name in carrier_stats["emissions_by_carrier"]:
                    carrier_stats["emissions_by_carrier"][carrier_name] += emissions_tonnes
            
            # Calculate capital costs by carrier for this specific year
            # Capital costs are annualized and counted every year the component is active
            
            # Helper function to check if component is active in this year
            def is_component_active(build_year, lifetime, current_year):
                """Check if component is active in the current year based on build_year and lifetime"""
                if pd.isna(build_year):
                    return True  # No build year constraint
                
                build_year = int(build_year)
                if build_year > current_year:
                    return False  # Not built yet
                
                if pd.isna(lifetime) or lifetime == float('inf'):
                    return True  # Infinite lifetime
                
                lifetime = int(lifetime)
                end_year = build_year + lifetime - 1
                return current_year <= end_year
            
            # 1. GENERATORS - Capital costs (including UNMET_LOAD)
            if hasattr(network, 'generators') and not network.generators.empty:
                # Get generator info: carrier, capital_cost, build_year, lifetime (include UNMET_LOAD)
                cursor = conn.execute("""
                    SELECT c.name as component_name, 
                           CASE 
                               WHEN c.component_type = 'UNMET_LOAD' THEN 'Unmet Load'
                               ELSE carr.name 
                           END as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type IN ('GENERATOR', 'UNMET_LOAD')
                """, (network_id,))
                generator_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for gen_name in network.generators.index:
                    if gen_name in generator_carriers:
                        carrier_name = generator_carriers[gen_name]
                        
                        # Get build year and lifetime
                        build_year = network.generators.loc[gen_name, 'build_year'] if 'build_year' in network.generators.columns else None
                        lifetime = network.generators.loc[gen_name, 'lifetime'] if 'lifetime' in network.generators.columns else None
                        
                        # Check if component is active in this year
                        if is_component_active(build_year, lifetime, year):
                            # Get capacity and capital cost
                            if 'p_nom_opt' in network.generators.columns:
                                capacity_mw = float(network.generators.loc[gen_name, 'p_nom_opt'])
                            else:
                                capacity_mw = float(network.generators.loc[gen_name, 'p_nom']) if 'p_nom' in network.generators.columns else 0.0
                            
                            capital_cost_per_mw = float(network.generators.loc[gen_name, 'capital_cost']) if 'capital_cost' in network.generators.columns else 0.0
                            
                            # Calculate annualized capital cost for this year
                            annual_capital_cost = capacity_mw * capital_cost_per_mw
                            
                            if carrier_name in carrier_stats["capital_cost_by_carrier"]:
                                carrier_stats["capital_cost_by_carrier"][carrier_name] += annual_capital_cost
            
            # 2. STORAGE_UNITS - Capital costs
            if hasattr(network, 'storage_units') and not network.storage_units.empty:
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORAGE_UNIT'
                """, (network_id,))
                storage_unit_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for su_name in network.storage_units.index:
                    if su_name in storage_unit_carriers:
                        carrier_name = storage_unit_carriers[su_name]
                        
                        # Get build year and lifetime
                        build_year = network.storage_units.loc[su_name, 'build_year'] if 'build_year' in network.storage_units.columns else None
                        lifetime = network.storage_units.loc[su_name, 'lifetime'] if 'lifetime' in network.storage_units.columns else None
                        
                        # Check if component is active in this year
                        if is_component_active(build_year, lifetime, year):
                            # Get power capacity and capital cost (per MW)
                            if 'p_nom_opt' in network.storage_units.columns:
                                capacity_mw = float(network.storage_units.loc[su_name, 'p_nom_opt'])
                            else:
                                capacity_mw = float(network.storage_units.loc[su_name, 'p_nom']) if 'p_nom' in network.storage_units.columns else 0.0
                            
                            capital_cost_per_mw = float(network.storage_units.loc[su_name, 'capital_cost']) if 'capital_cost' in network.storage_units.columns else 0.0
                            
                            # Calculate annualized capital cost for this year
                            annual_capital_cost = capacity_mw * capital_cost_per_mw
                            
                            if carrier_name in carrier_stats["capital_cost_by_carrier"]:
                                carrier_stats["capital_cost_by_carrier"][carrier_name] += annual_capital_cost
            
            # 3. STORES - Capital costs (per MWh)
            if hasattr(network, 'stores') and not network.stores.empty:
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORE'
                """, (network_id,))
                store_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for store_name in network.stores.index:
                    if store_name in store_carriers:
                        carrier_name = store_carriers[store_name]
                        
                        # Get build year and lifetime
                        build_year = network.stores.loc[store_name, 'build_year'] if 'build_year' in network.stores.columns else None
                        lifetime = network.stores.loc[store_name, 'lifetime'] if 'lifetime' in network.stores.columns else None
                        
                        # Check if component is active in this year
                        if is_component_active(build_year, lifetime, year):
                            # Get energy capacity and capital cost (per MWh)
                            if 'e_nom_opt' in network.stores.columns:
                                capacity_mwh = float(network.stores.loc[store_name, 'e_nom_opt'])
                            else:
                                capacity_mwh = float(network.stores.loc[store_name, 'e_nom']) if 'e_nom' in network.stores.columns else 0.0
                            
                            capital_cost_per_mwh = float(network.stores.loc[store_name, 'capital_cost']) if 'capital_cost' in network.stores.columns else 0.0
                            
                            # Calculate annualized capital cost for this year
                            annual_capital_cost = capacity_mwh * capital_cost_per_mwh
                            
                            if carrier_name in carrier_stats["capital_cost_by_carrier"]:
                                carrier_stats["capital_cost_by_carrier"][carrier_name] += annual_capital_cost
            
            # 4. LINES - Capital costs (per MVA)
            if hasattr(network, 'lines') and not network.lines.empty:
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'LINE'
                """, (network_id,))
                line_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for line_name in network.lines.index:
                    if line_name in line_carriers:
                        carrier_name = line_carriers[line_name]
                        
                        # Get build year and lifetime
                        build_year = network.lines.loc[line_name, 'build_year'] if 'build_year' in network.lines.columns else None
                        lifetime = network.lines.loc[line_name, 'lifetime'] if 'lifetime' in network.lines.columns else None
                        
                        # Check if component is active in this year
                        if is_component_active(build_year, lifetime, year):
                            # Get apparent power capacity and capital cost (per MVA)
                            if 's_nom_opt' in network.lines.columns:
                                capacity_mva = float(network.lines.loc[line_name, 's_nom_opt'])
                            else:
                                capacity_mva = float(network.lines.loc[line_name, 's_nom']) if 's_nom' in network.lines.columns else 0.0
                            
                            capital_cost_per_mva = float(network.lines.loc[line_name, 'capital_cost']) if 'capital_cost' in network.lines.columns else 0.0
                            
                            # Calculate annualized capital cost for this year
                            annual_capital_cost = capacity_mva * capital_cost_per_mva
            
                            if carrier_name in carrier_stats["capital_cost_by_carrier"]:
                                carrier_stats["capital_cost_by_carrier"][carrier_name] += annual_capital_cost
            
            # 5. LINKS - Capital costs (per MW)
            if hasattr(network, 'links') and not network.links.empty:
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'LINK'
                """, (network_id,))
                link_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for link_name in network.links.index:
                    if link_name in link_carriers:
                        carrier_name = link_carriers[link_name]
                        
                        # Get build year and lifetime
                        build_year = network.links.loc[link_name, 'build_year'] if 'build_year' in network.links.columns else None
                        lifetime = network.links.loc[link_name, 'lifetime'] if 'lifetime' in network.links.columns else None
                        
                        # Check if component is active in this year
                        if is_component_active(build_year, lifetime, year):
                            # Get power capacity and capital cost (per MW)
                            if 'p_nom_opt' in network.links.columns:
                                capacity_mw = float(network.links.loc[link_name, 'p_nom_opt'])
                            else:
                                capacity_mw = float(network.links.loc[link_name, 'p_nom']) if 'p_nom' in network.links.columns else 0.0
                            
                            capital_cost_per_mw = float(network.links.loc[link_name, 'capital_cost']) if 'capital_cost' in network.links.columns else 0.0
                            
                            # Calculate annualized capital cost for this year
                            annual_capital_cost = capacity_mw * capital_cost_per_mw
                            
                            if carrier_name in carrier_stats["capital_cost_by_carrier"]:
                                carrier_stats["capital_cost_by_carrier"][carrier_name] += annual_capital_cost
            
            # Calculate operational costs by carrier for this specific year
            # Operational costs = dispatch (MWh) × marginal_cost (currency/MWh)
            # Only for components that are active in this year
            
            # 1. GENERATORS - Operational costs (including UNMET_LOAD)
            if hasattr(network, 'generators_t') and hasattr(network.generators_t, 'p'):
                # Get generator info: carrier, marginal_cost, build_year, lifetime (include UNMET_LOAD)
                cursor = conn.execute("""
                    SELECT c.name as component_name, 
                           CASE 
                               WHEN c.component_type = 'UNMET_LOAD' THEN 'Unmet Load'
                               ELSE carr.name 
                           END as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type IN ('GENERATOR', 'UNMET_LOAD')
                """, (network_id,))
                generator_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter generation data for this specific year
                year_generation = self._filter_timeseries_by_year(network.generators_t.p, network.snapshots, year)
                if year_generation is not None and not year_generation.empty:
                    for gen_name in year_generation.columns:
                        if gen_name in generator_carriers:
                            carrier_name = generator_carriers[gen_name]
                            
                            # Get build year and lifetime
                            build_year = network.generators.loc[gen_name, 'build_year'] if 'build_year' in network.generators.columns else None
                            lifetime = network.generators.loc[gen_name, 'lifetime'] if 'lifetime' in network.generators.columns else None
                            
                            # Check if component is active in this year
                            if is_component_active(build_year, lifetime, year):
                                # Calculate generation for this year (already calculated above, but need to recalculate for operational costs)
                                year_weightings = self._get_year_weightings(network, year)
                                if year_weightings is not None:
                                    generation_mwh = float((year_generation[gen_name].values * year_weightings).sum())
                                else:
                                    generation_mwh = float(year_generation[gen_name].sum())
                                
                                # Get marginal cost
                                marginal_cost = float(network.generators.loc[gen_name, 'marginal_cost']) if 'marginal_cost' in network.generators.columns else 0.0
                                
                                # Calculate operational cost for this year
                                operational_cost = generation_mwh * marginal_cost
                                
                                if carrier_name in carrier_stats["operational_cost_by_carrier"]:
                                    carrier_stats["operational_cost_by_carrier"][carrier_name] += operational_cost
            
            # 2. STORAGE_UNITS - Operational costs (discharge only)
            if hasattr(network, 'storage_units_t') and hasattr(network.storage_units_t, 'p'):
                # Get storage unit info: carrier, marginal_cost, build_year, lifetime
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORAGE_UNIT'
                """, (network_id,))
                storage_unit_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter storage unit data for this specific year
                year_storage = self._filter_timeseries_by_year(network.storage_units_t.p, network.snapshots, year)
                if year_storage is not None and not year_storage.empty:
                    for su_name in year_storage.columns:
                        if su_name in storage_unit_carriers:
                            carrier_name = storage_unit_carriers[su_name]
                            
                            # Get build year and lifetime
                            build_year = network.storage_units.loc[su_name, 'build_year'] if 'build_year' in network.storage_units.columns else None
                            lifetime = network.storage_units.loc[su_name, 'lifetime'] if 'lifetime' in network.storage_units.columns else None
                            
                            # Check if component is active in this year
                            if is_component_active(build_year, lifetime, year):
                                # Calculate discharge for this year (positive values only)
                                year_weightings = self._get_year_weightings(network, year)
                                if year_weightings is not None:
                                    discharge_mwh = float((year_storage[su_name].clip(lower=0).values * year_weightings).sum())
                                else:
                                    discharge_mwh = float(year_storage[su_name].clip(lower=0).sum())
                                
                                # Get marginal cost
                                marginal_cost = float(network.storage_units.loc[su_name, 'marginal_cost']) if 'marginal_cost' in network.storage_units.columns else 0.0
                                
                                # Calculate operational cost for this year
                                operational_cost = discharge_mwh * marginal_cost
                                
                                if carrier_name in carrier_stats["operational_cost_by_carrier"]:
                                    carrier_stats["operational_cost_by_carrier"][carrier_name] += operational_cost
            
            # 3. STORES - Operational costs (discharge only)
            if hasattr(network, 'stores_t') and hasattr(network.stores_t, 'p'):
                # Get store info: carrier, marginal_cost, build_year, lifetime
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORE'
                """, (network_id,))
                store_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Filter store data for this specific year
                year_stores = self._filter_timeseries_by_year(network.stores_t.p, network.snapshots, year)
                if year_stores is not None and not year_stores.empty:
                    for store_name in year_stores.columns:
                        if store_name in store_carriers:
                            carrier_name = store_carriers[store_name]
                            
                            # Get build year and lifetime
                            build_year = network.stores.loc[store_name, 'build_year'] if 'build_year' in network.stores.columns else None
                            lifetime = network.stores.loc[store_name, 'lifetime'] if 'lifetime' in network.stores.columns else None
                            
                            # Check if component is active in this year
                            if is_component_active(build_year, lifetime, year):
                                # Calculate discharge for this year (positive values only)
                                year_weightings = self._get_year_weightings(network, year)
                                if year_weightings is not None:
                                    discharge_mwh = float((year_stores[store_name].clip(lower=0).values * year_weightings).sum())
                                else:
                                    discharge_mwh = float(year_stores[store_name].clip(lower=0).sum())
                                
                                # Get marginal cost
                                marginal_cost = float(network.stores.loc[store_name, 'marginal_cost']) if 'marginal_cost' in network.stores.columns else 0.0
                                
                                # Calculate operational cost for this year
                                operational_cost = discharge_mwh * marginal_cost
                            
                            if carrier_name in carrier_stats["operational_cost_by_carrier"]:
                                carrier_stats["operational_cost_by_carrier"][carrier_name] += operational_cost
                        
            # Calculate total system costs by carrier for this specific year
            # Total system cost = capital cost + operational cost
            for carrier_name in carrier_stats["capital_cost_by_carrier"]:
                capital_cost = carrier_stats["capital_cost_by_carrier"][carrier_name]
                operational_cost = carrier_stats["operational_cost_by_carrier"][carrier_name]
                total_system_cost = capital_cost + operational_cost
                
                if carrier_name in carrier_stats["total_system_cost_by_carrier"]:
                    carrier_stats["total_system_cost_by_carrier"][carrier_name] = total_system_cost
            
            # Calculate capacity by carrier for this specific year
            
            # 4. GENERATORS - Power capacity (MW) (including UNMET_LOAD)
            if hasattr(network, 'generators') and not network.generators.empty:
                # Get generator-carrier mapping (include UNMET_LOAD)
                cursor = conn.execute("""
                    SELECT c.name as component_name, 
                           CASE 
                               WHEN c.component_type = 'UNMET_LOAD' THEN 'Unmet Load'
                               ELSE carr.name 
                           END as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type IN ('GENERATOR', 'UNMET_LOAD')
                """, (network_id,))
                generator_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for gen_name in network.generators.index:
                    if gen_name in generator_carriers:
                        carrier_name = generator_carriers[gen_name]
                        
                        # Check if this generator is available in this year (build_year <= year)
                        is_available = True
                        if 'build_year' in network.generators.columns:
                            build_year = network.generators.loc[gen_name, 'build_year']
                            if pd.notna(build_year) and int(build_year) > year:
                                is_available = False
                        
                        if is_available:
                            # Use p_nom_opt if available, otherwise p_nom
                            if 'p_nom_opt' in network.generators.columns:
                                capacity_mw = float(network.generators.loc[gen_name, 'p_nom_opt'])
                            else:
                                capacity_mw = float(network.generators.loc[gen_name, 'p_nom']) if 'p_nom' in network.generators.columns else 0.0
                            
                            if carrier_name in carrier_stats["power_capacity_by_carrier"]:
                                carrier_stats["power_capacity_by_carrier"][carrier_name] += capacity_mw
                                
            # 2. STORAGE_UNITS - Power capacity (MW) + Energy capacity (MWh)
            if hasattr(network, 'storage_units') and not network.storage_units.empty:
                # Get storage unit-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORAGE_UNIT'
                """, (network_id,))
                storage_unit_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for su_name in network.storage_units.index:
                    if su_name in storage_unit_carriers:
                        carrier_name = storage_unit_carriers[su_name]
                        
                        # Check if this storage unit is available in this year
                        is_available = True
                        if 'build_year' in network.storage_units.columns:
                            build_year = network.storage_units.loc[su_name, 'build_year']
                            if pd.notna(build_year) and int(build_year) > year:
                                is_available = False
                        
                        if is_available:
                            # Power capacity (MW)
                            if 'p_nom_opt' in network.storage_units.columns:
                                p_nom_opt = float(network.storage_units.loc[su_name, 'p_nom_opt'])
                            else:
                                p_nom_opt = float(network.storage_units.loc[su_name, 'p_nom']) if 'p_nom' in network.storage_units.columns else 0.0
                            
                            if carrier_name in carrier_stats["power_capacity_by_carrier"]:
                                carrier_stats["power_capacity_by_carrier"][carrier_name] += p_nom_opt
                            
                            # Energy capacity (MWh) using max_hours
                            max_hours = 1.0  # Default
                            if 'max_hours' in network.storage_units.columns:
                                max_hours = float(network.storage_units.loc[su_name, 'max_hours'])
                            energy_capacity_mwh = p_nom_opt * max_hours
                            
                            if carrier_name in carrier_stats["energy_capacity_by_carrier"]:
                                carrier_stats["energy_capacity_by_carrier"][carrier_name] += energy_capacity_mwh
            
            # 3. STORES - Energy capacity (MWh) only
            if hasattr(network, 'stores') and not network.stores.empty:
                # Get store-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'STORE'
                """, (network_id,))
                store_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for store_name in network.stores.index:
                    if store_name in store_carriers:
                        carrier_name = store_carriers[store_name]
                        
                        # Check if this store is available in this year
                        is_available = True
                        if 'build_year' in network.stores.columns:
                            build_year = network.stores.loc[store_name, 'build_year']
                            if pd.notna(build_year) and int(build_year) > year:
                                is_available = False
                        
                        if is_available:
                            # Energy capacity (MWh)
                            if 'e_nom_opt' in network.stores.columns:
                                capacity_mwh = float(network.stores.loc[store_name, 'e_nom_opt'])
                            else:
                                capacity_mwh = float(network.stores.loc[store_name, 'e_nom']) if 'e_nom' in network.stores.columns else 0.0
                            
                            if carrier_name in carrier_stats["energy_capacity_by_carrier"]:
                                carrier_stats["energy_capacity_by_carrier"][carrier_name] += capacity_mwh
                                
            # 4. LINES - Apparent power capacity (MVA -> MW)
            if hasattr(network, 'lines') and not network.lines.empty:
                # Get line-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'LINE'
                """, (network_id,))
                line_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for line_name in network.lines.index:
                    if line_name in line_carriers:
                        carrier_name = line_carriers[line_name]
                        
                        # Check if this line is available in this year
                        is_available = True
                        if 'build_year' in network.lines.columns:
                            build_year = network.lines.loc[line_name, 'build_year']
                            if pd.notna(build_year) and int(build_year) > year:
                                is_available = False
                        
                        if is_available:
                            # Apparent power capacity (MVA -> MW, assume power factor = 1)
                            if 's_nom_opt' in network.lines.columns:
                                capacity_mva = float(network.lines.loc[line_name, 's_nom_opt'])
                            else:
                                capacity_mva = float(network.lines.loc[line_name, 's_nom']) if 's_nom' in network.lines.columns else 0.0
                            
                            capacity_mw = capacity_mva  # Convert MVA to MW
                            
                            if carrier_name in carrier_stats["power_capacity_by_carrier"]:
                                carrier_stats["power_capacity_by_carrier"][carrier_name] += capacity_mw
            
            # 5. LINKS - Power capacity (MW)
            if hasattr(network, 'links') and not network.links.empty:
                # Get link-carrier mapping
                cursor = conn.execute("""
                    SELECT c.name as component_name, carr.name as carrier_name
                    FROM components c
                    JOIN carriers carr ON c.carrier_id = carr.id
                    WHERE c.network_id = ? AND c.component_type = 'LINK'
                """, (network_id,))
                link_carriers = {row[0]: row[1] for row in cursor.fetchall()}
                
                for link_name in network.links.index:
                    if link_name in link_carriers:
                        carrier_name = link_carriers[link_name]
                        
                        # Check if this link is available in this year
                        is_available = True
                        if 'build_year' in network.links.columns:
                            build_year = network.links.loc[link_name, 'build_year']
                            if pd.notna(build_year) and int(build_year) > year:
                                is_available = False
                        
                        if is_available:
                            # Power capacity (MW)
                            if 'p_nom_opt' in network.links.columns:
                                capacity_mw = float(network.links.loc[link_name, 'p_nom_opt'])
                            else:
                                capacity_mw = float(network.links.loc[link_name, 'p_nom']) if 'p_nom' in network.links.columns else 0.0
                            
                            if carrier_name in carrier_stats["power_capacity_by_carrier"]:
                                carrier_stats["power_capacity_by_carrier"][carrier_name] += capacity_mw
            
            logger.info(f"Calculated year {year} carrier statistics:")
            logger.info(f"  Dispatch: {sum(carrier_stats['dispatch_by_carrier'].values()):.2f} MWh")
            logger.info(f"  Emissions: {sum(carrier_stats['emissions_by_carrier'].values()):.2f} tonnes CO2")
            logger.info(f"  Capital cost: {sum(carrier_stats['capital_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Operational cost: {sum(carrier_stats['operational_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Total system cost: {sum(carrier_stats['total_system_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Power capacity: {sum(carrier_stats['power_capacity_by_carrier'].values()):.2f} MW")
            logger.info(f"  Energy capacity: {sum(carrier_stats['energy_capacity_by_carrier'].values()):.2f} MWh")
            
            return carrier_stats
            
        except Exception as e:
            logger.error(f"Failed to calculate year {year} carrier statistics: {e}", exc_info=True)
            return {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},
                "energy_capacity_by_carrier": {},
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
    
    def _sum_year_based_carrier_statistics(self, conn, network_id: int) -> Dict[str, Any]:
        """
        Sum up per-year carrier statistics for accurate multi-year totals.
        For capacity: take the LAST YEAR (final capacity) instead of maximum.
        """
        try:
            import json
            
            # Initialize totals
            totals = {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},
                "energy_capacity_by_carrier": {},
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
            
            # Get all carriers from database
            cursor = conn.execute("""
                SELECT DISTINCT name FROM carriers WHERE network_id = ?
            """, (network_id,))
            all_carriers = [row[0] for row in cursor.fetchall()]
            
            # Initialize all carriers with zero values (including special "Unmet Load" carrier)
            all_carriers_with_unmet = all_carriers + ['Unmet Load']
            for carrier in all_carriers_with_unmet:
                totals["dispatch_by_carrier"][carrier] = 0.0
                totals["power_capacity_by_carrier"][carrier] = 0.0
                totals["energy_capacity_by_carrier"][carrier] = 0.0
                totals["emissions_by_carrier"][carrier] = 0.0
                totals["capital_cost_by_carrier"][carrier] = 0.0
                totals["operational_cost_by_carrier"][carrier] = 0.0
                totals["total_system_cost_by_carrier"][carrier] = 0.0
            
            # Get all year-based results, ordered by year
            cursor = conn.execute("""
                SELECT year, results_json FROM network_solve_results_by_year 
                WHERE network_id = ?
                ORDER BY year
            """, (network_id,))
            
            year_results = cursor.fetchall()
            logger.info(f"Found {len(year_results)} year-based results to sum for network {network_id}")
            
            if not year_results:
                logger.warning(f"No year-based results found for network {network_id}")
                return totals
            
            # For capacity: use the LAST YEAR only (final capacity state)
            last_year, last_results_json = year_results[-1]
            
            try:
                results = json.loads(last_results_json)
                network_stats = results.get('network_statistics', {})
                custom_stats = network_stats.get('custom_statistics', {})
                
                # Use last year's capacity as the all-year capacity
                power_capacity_by_carrier = custom_stats.get('power_capacity_by_carrier', {})
                for carrier, value in power_capacity_by_carrier.items():
                    if carrier in totals["power_capacity_by_carrier"]:
                        totals["power_capacity_by_carrier"][carrier] = float(value or 0)
                
                energy_capacity_by_carrier = custom_stats.get('energy_capacity_by_carrier', {})
                for carrier, value in energy_capacity_by_carrier.items():
                    if carrier in totals["energy_capacity_by_carrier"]:
                        totals["energy_capacity_by_carrier"][carrier] = float(value or 0)
                
                logger.info(f"Used last year ({last_year}) capacity as all-year capacity")
                
            except Exception as e:
                logger.error(f"Failed to process last year ({last_year}) results: {e}")
            
            # For other stats (dispatch, emissions, costs): sum across all years
            for year, results_json in year_results:
                try:
                    results = json.loads(results_json)
                    network_stats = results.get('network_statistics', {})
                    custom_stats = network_stats.get('custom_statistics', {})
                    
                    # Sum dispatch (energy values - sum across years)
                    dispatch_by_carrier = custom_stats.get('dispatch_by_carrier', {})
                    for carrier, value in dispatch_by_carrier.items():
                        if carrier in totals["dispatch_by_carrier"]:
                            totals["dispatch_by_carrier"][carrier] += float(value or 0)
                    
                    # Sum emissions (cumulative across years)
                    emissions_by_carrier = custom_stats.get('emissions_by_carrier', {})
                    for carrier, value in emissions_by_carrier.items():
                        if carrier in totals["emissions_by_carrier"]:
                            totals["emissions_by_carrier"][carrier] += float(value or 0)
                    
                    # Sum capital costs (cumulative across years)
                    capital_cost_by_carrier = custom_stats.get('capital_cost_by_carrier', {})
                    for carrier, value in capital_cost_by_carrier.items():
                        if carrier in totals["capital_cost_by_carrier"]:
                            totals["capital_cost_by_carrier"][carrier] += float(value or 0)
                    
                    # Sum operational costs (cumulative across years)
                    operational_cost_by_carrier = custom_stats.get('operational_cost_by_carrier', {})
                    for carrier, value in operational_cost_by_carrier.items():
                        if carrier in totals["operational_cost_by_carrier"]:
                            totals["operational_cost_by_carrier"][carrier] += float(value or 0)
                    
                    # Sum total system costs (cumulative across years)
                    total_system_cost_by_carrier = custom_stats.get('total_system_cost_by_carrier', {})
                    for carrier, value in total_system_cost_by_carrier.items():
                        if carrier in totals["total_system_cost_by_carrier"]:
                            totals["total_system_cost_by_carrier"][carrier] += float(value or 0)
                    
                except Exception as e:
                    logger.error(f"Failed to process year {year} results: {e}")
                    continue
            
            logger.info(f"Summed carrier statistics across {len(year_results)} years:")
            logger.info(f"  Final power capacity: {sum(totals['power_capacity_by_carrier'].values()):.2f} MW")
            logger.info(f"  Final energy capacity: {sum(totals['energy_capacity_by_carrier'].values()):.2f} MWh")
            logger.info(f"  Total dispatch: {sum(totals['dispatch_by_carrier'].values()):.2f} MWh")
            logger.info(f"  Total emissions: {sum(totals['emissions_by_carrier'].values()):.2f} tonnes CO2")
            logger.info(f"  Total capital cost: {sum(totals['capital_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Total operational cost: {sum(totals['operational_cost_by_carrier'].values()):.2f} USD")
            logger.info(f"  Total system cost: {sum(totals['total_system_cost_by_carrier'].values()):.2f} USD")
            
            return totals
            
        except Exception as e:
            logger.error(f"Failed to sum year-based carrier statistics: {e}", exc_info=True)
            # Return empty structure on error
            return {
                "dispatch_by_carrier": {},
                "power_capacity_by_carrier": {},
                "energy_capacity_by_carrier": {},
                "emissions_by_carrier": {},
                "capital_cost_by_carrier": {},
                "operational_cost_by_carrier": {},
                "total_system_cost_by_carrier": {}
            }
    
    def _serialize_results_json(self, solve_result: Dict[str, Any]) -> str:
        """Serialize solve results to JSON string."""
        import json
        try:
            # Create a clean results dictionary
            results = {
                "success": solve_result.get("success", False),
                "status": solve_result.get("status", "unknown"),
                "solve_time": solve_result.get("solve_time", 0.0),
                "objective_value": solve_result.get("objective_value"),
                "solver_name": solve_result.get("solver_name", "unknown"),
                "run_id": solve_result.get("run_id"),
                "network_statistics": solve_result.get("network_statistics", {}),
                "pypsa_result": solve_result.get("pypsa_result", {})
            }
            return json.dumps(results, default=self._json_serializer)
        except Exception as e:
            logger.warning(f"Failed to serialize results JSON: {e}")
            return json.dumps({"error": "serialization_failed"})
    
    def _serialize_metadata_json(self, solve_result: Dict[str, Any]) -> str:
        """Serialize solve metadata to JSON string."""
        import json
        try:
            metadata = {
                "solver_name": solve_result.get("solver_name", "unknown"),
                "run_id": solve_result.get("run_id"),
                "multi_period": solve_result.get("multi_period", False),
                "years": solve_result.get("years", []),
                "network_name": solve_result.get("network_name"),
                "num_snapshots": solve_result.get("num_snapshots", 0)
            }
            return json.dumps(metadata, default=self._json_serializer)
        except Exception as e:
            logger.warning(f"Failed to serialize metadata JSON: {e}")
            return json.dumps({"error": "serialization_failed"})
    
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
    
    def _calculate_total_demand(self, network: 'pypsa.Network') -> float:
        """Calculate total demand from loads in the network"""
        try:
            total_demand = 0.0
            
            # Calculate demand from loads
            if hasattr(network, 'loads_t') and hasattr(network.loads_t, 'p'):
                # Apply snapshot weightings to convert MW to MWh
                weightings = network.snapshot_weightings
                if isinstance(weightings, pd.DataFrame):
                    if 'objective' in weightings.columns:
                        weighting_values = weightings['objective'].values
                    else:
                        weighting_values = weightings.iloc[:, 0].values
                else:
                    weighting_values = weightings.values
                
                total_demand = float((network.loads_t.p.values * weighting_values[:, None]).sum())
            
            return total_demand
            
        except Exception as e:
            logger.error(f"Failed to calculate total demand: {e}")
            return 0.0
    
    def _json_serializer(self, obj):
        """Convert numpy/pandas types to JSON serializable types"""
        import numpy as np
        import pandas as pd
        
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict()
        elif hasattr(obj, 'item'):  # Handle numpy scalars
            return obj.item()
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")