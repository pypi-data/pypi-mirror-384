"""
Global Energy Monitor (GEM) data integration for PyConvexity.

This module provides functions to load power plant data from GEM's Global Integrated Power dataset
and integrate it with PyConvexity models.
"""

import sqlite3
import pandas as pd
import yaml
import country_converter as coco
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from pyconvexity.core.types import CreateComponentRequest, StaticValue
from pyconvexity.models.components import create_component
from pyconvexity.models.attributes import set_static_attribute
from pyconvexity.data.loaders.cache import DataCache

logger = logging.getLogger(__name__)

# Default path to GEM data - can be overridden
DEFAULT_GEM_DATA_PATH = None

def _get_gem_data_path() -> Path:
    """Get the path to GEM data file."""
    global DEFAULT_GEM_DATA_PATH
    
    if DEFAULT_GEM_DATA_PATH:
        return Path(DEFAULT_GEM_DATA_PATH)
    
    # Try to find the examples data
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "examples" / "data" / "raw" / "global-energy-monitor" / "Global-Integrated-Power-August-2025.xlsx",
        Path("data/raw/global-energy-monitor/Global-Integrated-Power-August-2025.xlsx"),
        Path("../examples/data/raw/global-energy-monitor/Global-Integrated-Power-August-2025.xlsx"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return path
    
    raise FileNotFoundError(
        "GEM data file not found. Please set the path using set_gem_data_path() or "
        "ensure the file exists at one of the expected locations."
    )

def set_gem_data_path(path: str):
    """Set the path to the GEM data file."""
    global DEFAULT_GEM_DATA_PATH
    DEFAULT_GEM_DATA_PATH = path

def _load_gem_mapping() -> Dict[str, Any]:
    """Load the GEM to carriers mapping configuration."""
    # Try to find the mapping file
    possible_paths = [
        Path(__file__).parent.parent.parent.parent.parent / "examples" / "schema" / "gem_mapping.yaml",
        Path("schema/gem_mapping.yaml"),
        Path("../examples/schema/gem_mapping.yaml"),
    ]
    
    for mapping_file in possible_paths:
        if mapping_file.exists():
            with open(mapping_file, 'r') as f:
                return yaml.safe_load(f)
    
    # Fallback to embedded mapping if file not found
    logger.warning("GEM mapping file not found, using embedded mapping")
    return _get_embedded_gem_mapping()

def _get_embedded_gem_mapping() -> Dict[str, Any]:
    """Embedded GEM mapping as fallback."""
    return {
        'technology_mapping': {
            # Nuclear
            "pressurized water reactor": ["nuclear", "nuclear", "pressurized-water-reactor"],
            "boiling water reactor": ["nuclear", "nuclear", "boiling-water-reactor"],
            "small modular reactor": ["nuclear", "nuclear", "small-modular-reactor"],
            
            # Thermal coal
            "subcritical": ["thermal", "coal", "subcritical"],
            "supercritical": ["thermal", "coal", "supercritical"],
            "ultra-supercritical": ["thermal", "coal", "supercritical"],
            
            # Thermal gas
            "combined cycle": ["thermal", "gas", "combined-cycle"],
            "gas turbine": ["thermal", "gas", "gas-turbine"],
            
            # Renewables
            "PV": ["renewables", "solar", "photovoltaic"],
            "Solar Thermal": ["renewables", "solar", "thermal"],
            "Onshore": ["renewables", "wind", "onshore"],
            "Offshore hard mount": ["renewables", "wind", "offshore"],
            "Offshore floating": ["renewables", "wind", "offshore"],
            "run-of-river": ["renewables", "hydro", "run-of-river"],
            "pumped storage": ["storage", "pumped-hydro", "unspecified"],
            
            # Storage
            "battery": ["storage", "battery", "lithium-ion"],
            
            # Bioenergy
            "biomass": ["bioenergy", "biomass", "unspecified"],
            "biogas": ["bioenergy", "biogas", "unspecified"],
        },
        'type_fallback': {
            "nuclear": ["nuclear", "nuclear", "unspecified"],
            "coal": ["thermal", "coal", "unspecified"],
            "oil/gas": ["thermal", "gas", "unspecified"],
            "wind": ["renewables", "wind", "unspecified"],
            "solar": ["renewables", "solar", "unspecified"],
            "geothermal": ["renewables", "geothermal", "unspecified"],
            "hydropower": ["renewables", "hydro", "unspecified"],
            "bioenergy": ["bioenergy", "biomass", "unspecified"],
        },
        'default_mapping': ["unknown", "unspecified", "unspecified"]
    }

def _map_technology_to_carriers(technology: str, gem_type: str, mapping_config: Dict[str, Any]) -> tuple:
    """
    Map GEM technology to carriers schema.
    
    Args:
        technology: GEM Technology field value
        gem_type: GEM Type field value
        mapping_config: Loaded mapping configuration
    
    Returns:
        tuple: (category, carrier, type)
    """
    # Clean the technology string
    if pd.isna(technology):
        technology = "unknown"
    else:
        technology = str(technology).strip()
    
    # Try to map using technology mapping
    tech_mapping = mapping_config['technology_mapping']
    if technology in tech_mapping:
        mapped = tech_mapping[technology]
        if len(mapped) == 2:
            return mapped[0], mapped[1], "unspecified"
        elif len(mapped) == 3:
            return mapped[0], mapped[1], mapped[2]
    
    # Fallback to type mapping
    type_fallback = mapping_config['type_fallback']
    if pd.notna(gem_type) and str(gem_type).strip() in type_fallback:
        mapped = type_fallback[str(gem_type).strip()]
        if len(mapped) == 2:
            return mapped[0], mapped[1], "unspecified"
        elif len(mapped) == 3:
            return mapped[0], mapped[1], mapped[2]
    
    # Default mapping
    default = mapping_config['default_mapping']
    return default[0], default[1], default[2]

def get_generators_from_gem(
    country: str,
    gem_data_path: Optional[str] = None,
    technology_types: Optional[List[str]] = None,
    min_capacity_mw: float = 0.0,
    status_filter: Optional[List[str]] = None,
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Load generator data from GEM for a specific country.
    
    Args:
        country: ISO 3-letter country code (e.g., "USA", "DEU", "CHN")
        gem_data_path: Optional path to GEM Excel file (overrides default)
        technology_types: Optional list of technology types to filter by
        min_capacity_mw: Minimum capacity in MW (default: 0.0)
        status_filter: Optional list of status values (default: ["operating", "construction"])
        use_cache: Whether to use cached data (default: True)
        
    Returns:
        pandas.DataFrame: Generator data with columns:
            - plant_name: Name of the power plant
            - country_iso_3: ISO 3-letter country code
            - category: Energy category (nuclear, thermal, renewables, etc.)
            - carrier: Energy carrier (coal, gas, solar, wind, etc.)
            - type: Technology type (subcritical, combined-cycle, photovoltaic, etc.)
            - capacity_mw: Capacity in megawatts
            - start_year: Year the plant started operation
            - latitude: Latitude coordinate
            - longitude: Longitude coordinate
            
    Raises:
        FileNotFoundError: If GEM data file cannot be found
        ValueError: If country code is invalid
    """
    if gem_data_path:
        set_gem_data_path(gem_data_path)
    
    # Validate country code
    country = country.upper()
    if len(country) != 3:
        raise ValueError(f"Country code must be 3 letters, got: {country}")
    
    # Set default status filter
    if status_filter is None:
        status_filter = ["operating", "construction"]
    
    # Create cache key
    cache_filters = {
        'country': country,
        'technology_types': technology_types,
        'min_capacity_mw': min_capacity_mw,
        'status_filter': status_filter
    }
    
    # Try to get cached data
    cache = DataCache()
    if use_cache:
        cached_data = cache.get_cached_data('gem_generators', cache_filters)
        if cached_data is not None:
            return cached_data
    
    # Load and process data
    logger.info(f"Loading GEM data for country: {country}")
    
    gem_file = _get_gem_data_path()
    df = pd.read_excel(gem_file, sheet_name='Power facilities')
    
    # Apply status filter
    df = df[df['Status'].isin(status_filter)]
    
    # Filter out captive industry use
    df = df[~df['Captive Industry Use'].isin(['power', 'heat', 'both'])]
    
    # Convert country names to ISO codes
    country_codes_3 = coco.convert(
        names=df['Country/area'], 
        to='ISO3', 
        not_found='pass'
    )
    df['country_iso_3'] = country_codes_3
    
    # Filter by country
    df = df[df['country_iso_3'] == country]
    
    if len(df) == 0:
        logger.warning(f"No generators found for country: {country}")
        return pd.DataFrame()
    
    # Rename columns
    df = df.rename(columns={
        'Plant / Project name': 'plant_name',
        'Capacity (MW)': 'capacity_mw',
        'Start year': 'start_year',
        'Latitude': 'latitude',
        'Longitude': 'longitude'
    })
    
    # Clean start_year column - convert non-numeric values to NaN
    df['start_year'] = pd.to_numeric(df['start_year'], errors='coerce')
    
    # Load mapping configuration and apply technology mapping
    mapping_config = _load_gem_mapping()
    
    df['category'] = None
    df['carrier'] = None
    df['type'] = None
    
    for idx, row in df.iterrows():
        category, carrier, tech_type = _map_technology_to_carriers(
            row['Technology'], row['Type'], mapping_config
        )
        df.at[idx, 'category'] = category
        df.at[idx, 'carrier'] = carrier
        df.at[idx, 'type'] = tech_type
    
    # Apply filters
    if technology_types:
        df = df[df['carrier'].isin(technology_types)]
    
    if min_capacity_mw > 0:
        df = df[df['capacity_mw'] >= min_capacity_mw]
    
    # Aggregate plants by key attributes
    df = (
        df.groupby(['country_iso_3', 'category', 'carrier', 'type', 'plant_name'])
        .agg({
            'capacity_mw': 'sum',
            'start_year': 'first',
            'latitude': 'first',
            'longitude': 'first',
        })
        .reset_index()
    )
    
    # Select final columns
    result_df = df[[
        'plant_name',
        'country_iso_3',
        'category',
        'carrier',
        'type',
        'capacity_mw',
        'start_year',
        'latitude',
        'longitude',
    ]]
    
    # Cache the result
    if use_cache:
        cache.cache_data('gem_generators', result_df, cache_filters)
    
    logger.info(f"Loaded {len(result_df)} generators for {country}")
    return result_df

def add_gem_generators_to_network(
    conn: sqlite3.Connection,
    network_id: int,
    generators_df: pd.DataFrame,
    bus_mapping: Optional[Dict[str, int]] = None,
    carrier_mapping: Optional[Dict[str, int]] = None
) -> List[int]:
    """
    Add GEM generators to a PyConvexity network.
    
    Args:
        conn: Database connection
        network_id: ID of the network to add generators to
        generators_df: DataFrame from get_generators_from_gem()
        bus_mapping: Optional mapping from region/location to bus IDs
        carrier_mapping: Optional mapping from carrier names to carrier IDs
        
    Returns:
        List of created generator component IDs
        
    Raises:
        ValueError: If required data is missing
    """
    if generators_df.empty:
        logger.warning("No generators to add")
        return []
    
    created_ids = []
    name_counter = {}  # Track duplicate names
    
    for _, gen in generators_df.iterrows():
        # Determine bus_id (simplified - could be enhanced with spatial mapping)
        bus_id = None
        if bus_mapping:
            # Try different possible column names for bus assignment
            for col_name in ['region', 'nearest_bus', 'bus', 'bus_name']:
                if col_name in gen and pd.notna(gen[col_name]):
                    bus_id = bus_mapping.get(gen[col_name])
                    if bus_id:
                        break
        
        # Determine carrier_id
        carrier_id = None
        if carrier_mapping:
            carrier_id = carrier_mapping.get(gen['carrier'])
        
        # Make generator name unique
        base_name = gen['plant_name']
        if base_name in name_counter:
            name_counter[base_name] += 1
            unique_name = f"{base_name}_{name_counter[base_name]}"
        else:
            name_counter[base_name] = 0
            unique_name = base_name
        
        # Create generator component
        component_id = create_component(
            conn=conn,
            network_id=network_id,
            component_type="GENERATOR",
            name=unique_name,
            latitude=gen['latitude'] if pd.notna(gen['latitude']) else None,
            longitude=gen['longitude'] if pd.notna(gen['longitude']) else None,
            carrier_id=carrier_id,
            bus_id=bus_id
        )
        
        # Set generator attributes
        set_static_attribute(conn, component_id, "p_nom", StaticValue(float(gen['capacity_mw'])))
        
        # Set marginal costs based on technology
        marginal_cost = 0.0  # Default for renewables (wind, solar, hydro)
        if gen['carrier'] == 'gas':
            marginal_cost = 50.0  # €/MWh for gas
        elif gen['carrier'] == 'coal':
            marginal_cost = 35.0  # €/MWh for coal
        elif gen['carrier'] == 'biomass':
            marginal_cost = 45.0  # €/MWh for biomass
        elif gen['carrier'] == 'nuclear':
            marginal_cost = 15.0  # €/MWh for nuclear
        # Wind, solar, hydro, pumped-hydro remain at 0.0
        
        set_static_attribute(conn, component_id, "marginal_cost", StaticValue(marginal_cost))
        
        if pd.notna(gen['start_year']):
            try:
                set_static_attribute(conn, component_id, "build_year", StaticValue(int(gen['start_year'])))
            except:
                pass  # Skip if build_year attribute doesn't exist
        
        # Technology metadata would be stored here if the database had a metadata table
        # For now, the Ireland demo will use the original generator dataframe for technology info
        
        created_ids.append(component_id)
        
        logger.debug(f"Created generator {component_id}: {gen['plant_name']} ({gen['capacity_mw']} MW)")
    
    logger.info(f"Added {len(created_ids)} generators to network {network_id}")
    return created_ids
