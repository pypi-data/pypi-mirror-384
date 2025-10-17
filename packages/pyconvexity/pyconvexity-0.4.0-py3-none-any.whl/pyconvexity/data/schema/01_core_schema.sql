-- ============================================================================
-- CORE ENERGY NETWORK SCHEMA
-- Essential tables for networks, components, and attributes
-- Optimized for atomic database operations
-- Version 2.1.0
-- ============================================================================

-- ============================================================================
-- NETWORKS AND TIME MANAGEMENT
-- ============================================================================

-- Networks table - represents energy system models
CREATE TABLE networks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Time axis definition (single source of truth)
    time_start DATETIME NOT NULL,
    time_end DATETIME NOT NULL,
    time_interval TEXT NOT NULL,  -- ISO 8601 duration (PT1H, PT30M, PT2H, etc.)
    
    -- Unmet load flag
    unmet_load_active BOOLEAN DEFAULT 1, -- 1 = true, 0 = false
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CONSTRAINT valid_time_range CHECK (time_end > time_start)
);

CREATE INDEX idx_networks_name ON networks(name);
CREATE INDEX idx_networks_created_at ON networks(created_at);

-- Network time periods - optimized storage using computed timestamps
-- Instead of storing 75k+ timestamp strings, we compute them from the time axis
-- This reduces storage from ~3.4MB to ~24 bytes per network
CREATE TABLE network_time_periods (
    network_id INTEGER NOT NULL,
    period_count INTEGER NOT NULL,      -- Total number of periods (e.g., 8760 for hourly year)
    start_timestamp INTEGER NOT NULL,   -- Unix timestamp of first period
    interval_seconds INTEGER NOT NULL,  -- Seconds between periods (3600 for hourly)
    
    PRIMARY KEY (network_id),
    
    CONSTRAINT fk_time_periods_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT valid_period_count CHECK (period_count > 0),
    CONSTRAINT valid_interval CHECK (interval_seconds > 0)
);

-- No additional indexes needed - primary key on network_id is sufficient
-- Timestamps are computed as: start_timestamp + (period_index * interval_seconds)

-- Network locks - prevents concurrent modifications
CREATE TABLE network_locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL UNIQUE,
    locked_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    locked_by TEXT NOT NULL,  -- Process/user identifier
    lock_reason TEXT NOT NULL,  -- 'solving', 'importing', 'editing', etc.
    
    CONSTRAINT fk_network_locks_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE
);

CREATE INDEX idx_network_locks_network ON network_locks(network_id);
CREATE INDEX idx_network_locks_reason ON network_locks(lock_reason);

-- ============================================================================
-- CARRIERS - ENERGY TYPES
-- ============================================================================

-- Carriers table - energy carriers (electricity, gas, heat, etc.)
CREATE TABLE carriers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    
    -- Carrier properties from PyPSA reference
    co2_emissions REAL DEFAULT 0.0,  -- tonnes/MWh
    color TEXT,                      -- Plotting color
    nice_name TEXT,                  -- Display name  
    max_growth REAL DEFAULT NULL,    -- MW - can be infinite
    max_relative_growth REAL DEFAULT 0.0,  -- MW
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_carriers_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT uq_carriers_network_name 
        UNIQUE (network_id, name)
);

CREATE INDEX idx_carriers_network ON carriers(network_id);
CREATE INDEX idx_carriers_name ON carriers(network_id, name);

-- ============================================================================
-- UNIFIED COMPONENT SYSTEM
-- ============================================================================

-- Components table - unified table for all network components
-- This is the single source of truth for component identity and relationships
CREATE TABLE components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    component_type TEXT NOT NULL,  -- 'BUS', 'GENERATOR', 'LOAD', 'LINE', 'LINK', 'STORAGE_UNIT', 'STORE', 'UNMET_LOAD'
    name TEXT NOT NULL,
    
    -- Geographic location (optional - not all components have physical locations)
    -- Lines and links are connections between buses and don't have their own coordinates
    latitude REAL,
    longitude REAL,
    
    -- Energy carrier reference (NULL for CONSTRAINT components)
    carrier_id INTEGER,
    
    -- Bus connections - simple column approach
    -- For single connections (GENERATOR, LOAD, STORAGE_UNIT, STORE): use bus_id
    -- For dual connections (LINE, LINK): use bus0_id and bus1_id
    -- For buses: all are NULL (buses don't connect to other buses)
    bus_id INTEGER,     -- Single bus connection
    bus0_id INTEGER,    -- First bus for lines/links
    bus1_id INTEGER,    -- Second bus for lines/links
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_components_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT fk_components_carrier 
        FOREIGN KEY (carrier_id) REFERENCES carriers(id),
    CONSTRAINT fk_components_bus 
        FOREIGN KEY (bus_id) REFERENCES components(id),
    CONSTRAINT fk_components_bus0 
        FOREIGN KEY (bus0_id) REFERENCES components(id),
    CONSTRAINT fk_components_bus1 
        FOREIGN KEY (bus1_id) REFERENCES components(id),
    CONSTRAINT uq_components_network_name 
        UNIQUE (network_id, name),
    CONSTRAINT valid_component_type 
        CHECK (component_type IN ('BUS', 'GENERATOR', 'LOAD', 'LINE', 'LINK', 'STORAGE_UNIT', 'STORE', 'UNMET_LOAD', 'CONSTRAINT')),
    -- New constraint: carrier_id must be NOT NULL for all components except CONSTRAINT
    CONSTRAINT valid_carrier_id 
        CHECK (component_type != 'CONSTRAINT' OR carrier_id IS NULL)
    -- Note: UNMET_LOAD uniqueness per bus is enforced in backend logic since SQLite doesn't support partial unique constraints
);

-- Optimized indexes for atomic operations
CREATE INDEX idx_components_network ON components(network_id);
CREATE INDEX idx_components_type ON components(component_type);
CREATE INDEX idx_components_name ON components(name);
CREATE INDEX idx_components_network_type ON components(network_id, component_type);
CREATE INDEX idx_components_carrier ON components(carrier_id);
CREATE INDEX idx_components_network_name ON components(network_id, name);  -- For fast lookups
CREATE INDEX idx_components_location ON components(latitude, longitude);   -- For spatial queries
CREATE INDEX idx_components_bus ON components(bus_id);                     -- For bus connections
CREATE INDEX idx_components_bus0 ON components(bus0_id);                   -- For line/link connections
CREATE INDEX idx_components_bus1 ON components(bus1_id);                   -- For line/link connections

-- ============================================================================
-- ATTRIBUTE VALIDATION SYSTEM
-- ============================================================================

-- Attribute validation rules table - defines what attributes are valid for each component type
-- This enforces PyPSA attribute definitions at the database level
CREATE TABLE attribute_validation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type TEXT NOT NULL,
    attribute_name TEXT NOT NULL,
    display_name TEXT,                 -- Human-readable display name
    
    -- Validation rules from PyPSA reference
    data_type TEXT NOT NULL,           -- 'float', 'boolean', 'string', 'int'
    unit TEXT,                         -- 'MW', 'per unit', 'currency/MWh', etc.
    default_value TEXT,                -- String representation of default
    allowed_storage_types TEXT NOT NULL, -- 'static', 'timeseries', 'static_or_timeseries'
    is_required BOOLEAN DEFAULT FALSE,
    is_input BOOLEAN DEFAULT TRUE,     -- TRUE for inputs, FALSE for outputs
    description TEXT,
    
    -- Validation constraints
    min_value REAL,                    -- Optional minimum value constraint
    max_value REAL,                    -- Optional maximum value constraint
    allowed_values TEXT,               -- JSON array of allowed values for string types
    
    -- Attribute grouping and storage control
    group_name TEXT DEFAULT 'other',   -- Attribute group: 'basic', 'power', 'economics', 'control', 'other'
    to_save BOOLEAN DEFAULT TRUE,      -- Whether to save this attribute in solve results
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uq_validation_rule 
        UNIQUE (component_type, attribute_name),
    CONSTRAINT valid_component_type_validation 
        CHECK (component_type IN ('BUS', 'GENERATOR', 'LOAD', 'LINE', 'LINK', 'STORAGE_UNIT', 'STORE', 'UNMET_LOAD', 'CONSTRAINT')),
    CONSTRAINT valid_data_type 
        CHECK (data_type IN ('float', 'boolean', 'string', 'int')),
    CONSTRAINT valid_allowed_storage_types 
        CHECK (allowed_storage_types IN ('static', 'timeseries', 'static_or_timeseries')),
    CONSTRAINT valid_group_name 
        CHECK (group_name IN ('basic', 'power', 'economics', 'control', 'other'))
);

-- Optimized indexes for validation lookups
CREATE INDEX idx_validation_component_type ON attribute_validation_rules(component_type);
CREATE INDEX idx_validation_attribute ON attribute_validation_rules(component_type, attribute_name);
CREATE INDEX idx_validation_input ON attribute_validation_rules(is_input);
CREATE INDEX idx_validation_required ON attribute_validation_rules(is_required);

-- ============================================================================
-- UNIFIED COMPONENT ATTRIBUTES
-- ============================================================================

-- Component attributes - unified storage for all component properties
-- This is the heart of our atomic attribute system with scenario support
CREATE TABLE component_attributes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    attribute_name TEXT NOT NULL,
    
    -- Scenario support - references scenarios table (master scenario has explicit ID)
    scenario_id INTEGER NOT NULL,
    
    -- Storage type - determines how value is stored
    storage_type TEXT NOT NULL CHECK (storage_type IN ('static', 'timeseries')),
    
    -- Unified value storage - exactly one must be non-NULL based on storage_type
    static_value TEXT,               -- JSON-encoded static value (handles all data types)
    timeseries_data BLOB,           -- Parquet format for timeseries
    
    -- Cached metadata for performance
    data_type TEXT NOT NULL,        -- Copied from validation rules for fast access
    unit TEXT,                      -- Copied from validation rules for fast access
    is_input BOOLEAN DEFAULT TRUE,  -- Copied from validation rules for fast access
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT fk_attributes_component 
        FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    CONSTRAINT fk_attributes_scenario 
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    
    -- Ensure exactly one storage type is used
    CONSTRAINT check_exactly_one_storage_type CHECK (
        (storage_type = 'static' AND static_value IS NOT NULL AND timeseries_data IS NULL) OR
        (storage_type = 'timeseries' AND static_value IS NULL AND timeseries_data IS NOT NULL)
    ),
    
    -- Ensure unique attribute per component per scenario
    CONSTRAINT uq_component_attribute_scenario 
        UNIQUE (component_id, attribute_name, scenario_id)
);

-- Highly optimized indexes for atomic operations with scenario support
CREATE INDEX idx_attributes_component ON component_attributes(component_id);
CREATE INDEX idx_attributes_name ON component_attributes(attribute_name);
CREATE INDEX idx_attributes_storage_type ON component_attributes(storage_type);
CREATE INDEX idx_attributes_component_name ON component_attributes(component_id, attribute_name);
CREATE INDEX idx_attributes_data_type ON component_attributes(data_type);
CREATE INDEX idx_attributes_is_input ON component_attributes(is_input);
CREATE INDEX idx_attributes_scenario ON component_attributes(scenario_id);

-- Composite indexes for common query patterns
CREATE INDEX idx_attributes_component_input ON component_attributes(component_id, is_input);
CREATE INDEX idx_attributes_component_storage ON component_attributes(component_id, storage_type);
CREATE INDEX idx_attributes_component_scenario ON component_attributes(component_id, scenario_id);

-- ============================================================================
-- VALIDATION TRIGGERS
-- ============================================================================

-- Trigger to validate attributes against rules on insert
CREATE TRIGGER validate_component_attribute_insert
    BEFORE INSERT ON component_attributes
    FOR EACH ROW
    WHEN NOT EXISTS (
        SELECT 1 FROM components c
        JOIN attribute_validation_rules avr ON c.component_type = avr.component_type
        WHERE c.id = NEW.component_id 
        AND avr.attribute_name = NEW.attribute_name
    )
BEGIN
    SELECT RAISE(ABORT, 'Attribute is not defined for this component type');
END;

-- Trigger to validate storage type on insert
CREATE TRIGGER validate_storage_type_insert
    BEFORE INSERT ON component_attributes
    FOR EACH ROW
    WHEN EXISTS (
        SELECT 1 FROM components c
        JOIN attribute_validation_rules avr ON c.component_type = avr.component_type
        WHERE c.id = NEW.component_id
        AND avr.attribute_name = NEW.attribute_name
        AND avr.allowed_storage_types != 'static_or_timeseries'
        AND avr.allowed_storage_types != NEW.storage_type
    )
BEGIN
    SELECT RAISE(ABORT, 'Storage type not allowed for this attribute');
END;

-- Trigger to validate attributes against rules on update
CREATE TRIGGER validate_component_attribute_update
    BEFORE UPDATE ON component_attributes
    FOR EACH ROW
    WHEN NOT EXISTS (
        SELECT 1 FROM components c
        JOIN attribute_validation_rules avr ON c.component_type = avr.component_type
        WHERE c.id = NEW.component_id 
        AND avr.attribute_name = NEW.attribute_name
    )
BEGIN
    SELECT RAISE(ABORT, 'Attribute is not defined for this component type');
END;

-- Trigger to validate storage type on update
CREATE TRIGGER validate_storage_type_update
    BEFORE UPDATE ON component_attributes
    FOR EACH ROW
    WHEN EXISTS (
        SELECT 1 FROM components c
        JOIN attribute_validation_rules avr ON c.component_type = avr.component_type
        WHERE c.id = NEW.component_id
        AND avr.attribute_name = NEW.attribute_name
        AND avr.allowed_storage_types != 'static_or_timeseries'
        AND avr.allowed_storage_types != NEW.storage_type
    )
BEGIN
    SELECT RAISE(ABORT, 'Storage type not allowed for this attribute');
END;

-- Trigger to update metadata timestamps
CREATE TRIGGER update_component_attributes_timestamp
    BEFORE UPDATE ON component_attributes
    FOR EACH ROW
BEGIN
    UPDATE component_attributes 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Trigger to update component timestamps when attributes change
CREATE TRIGGER update_component_timestamp_on_attribute_change
    AFTER INSERT ON component_attributes
    FOR EACH ROW
BEGIN
    UPDATE components 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.component_id;
END;

-- ============================================================================
-- COMPONENT GEOMETRIES - Optional GeoJSON geometries for spatial representation
-- ============================================================================

-- Component geometries - stores optional GeoJSON geometries for components
-- Enables real spatial representation (e.g., actual line routes, generator footprints)
CREATE TABLE component_geometries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL UNIQUE,
    
    -- GeoJSON geometry stored as JSON text
    -- Supports: Point, LineString, Polygon, MultiPolygon, MultiPoint, MultiLineString, GeometryCollection
    geometry TEXT NOT NULL,
    
    -- Cache the geometry type for faster queries and validation
    geometry_type TEXT NOT NULL CHECK (geometry_type IN (
        'Point', 'LineString', 'Polygon', 'MultiPolygon', 
        'MultiPoint', 'MultiLineString', 'GeometryCollection'
    )),
    
    -- Cache bounding box for spatial indexing and quick filtering
    bbox_min_lng REAL,
    bbox_min_lat REAL,
    bbox_max_lng REAL,
    bbox_max_lat REAL,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_geometry_component 
        FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE
);

-- Indexes for efficient geometry queries
CREATE INDEX idx_component_geometries_component ON component_geometries(component_id);
CREATE INDEX idx_component_geometries_type ON component_geometries(geometry_type);
CREATE INDEX idx_component_geometries_bbox ON component_geometries(
    bbox_min_lng, bbox_min_lat, bbox_max_lng, bbox_max_lat
);

-- Trigger to update timestamp on geometry changes
CREATE TRIGGER update_component_geometries_timestamp
    BEFORE UPDATE ON component_geometries
    FOR EACH ROW
BEGIN
    UPDATE component_geometries 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- ============================================================================
-- NETWORK CONFIGURATION
-- ============================================================================

-- Network configuration parameters - flexible parameter storage
-- Supports scenario-aware configuration with fallback to network defaults
CREATE TABLE network_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    scenario_id INTEGER, -- NULL for network defaults
    
    -- Parameter definition
    param_name TEXT NOT NULL,
    param_type TEXT NOT NULL,
    param_value TEXT NOT NULL,
    param_description TEXT,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_network_config_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT fk_network_config_scenario 
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    CONSTRAINT uq_network_config_param 
        UNIQUE (network_id, scenario_id, param_name),
    CONSTRAINT valid_param_type 
        CHECK (param_type IN ('boolean', 'real', 'integer', 'string', 'json'))
);

-- Indexes for performance
CREATE INDEX idx_network_config_network ON network_config(network_id);
CREATE INDEX idx_network_config_scenario ON network_config(scenario_id);
CREATE INDEX idx_network_config_param ON network_config(param_name);
CREATE INDEX idx_network_config_network_param ON network_config(network_id, param_name);
CREATE INDEX idx_network_config_network_scenario_param ON network_config(network_id, scenario_id, param_name);

-- ============================================================================
-- SYSTEM METADATA
-- ============================================================================

-- System metadata table for schema versioning and configuration
CREATE TABLE system_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_system_metadata_key ON system_metadata(key);

-- Insert initial schema version
INSERT INTO system_metadata (key, value, description) 
VALUES ('schema_version', '2.4.0', 'Database schema version - Added network_config table for flexible parameter storage');

INSERT INTO system_metadata (key, value, description) 
VALUES ('created_at', datetime('now'), 'Database creation timestamp');

INSERT INTO system_metadata (key, value, description) 
VALUES ('atomic_operations', 'enabled', 'Atomic database operations support'); 