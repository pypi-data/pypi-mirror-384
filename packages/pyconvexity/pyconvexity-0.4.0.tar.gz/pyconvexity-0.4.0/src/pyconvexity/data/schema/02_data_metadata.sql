-- ============================================================================
-- DATA STORAGE AND METADATA SCHEMA (OPTIMIZED)
-- Essential tables for data storage and solve results only
-- Removed unused audit logging and analysis caching for efficiency
-- Version 2.2.0 - Optimized
-- ============================================================================

-- ============================================================================
-- GENERIC DATA STORAGE
-- ============================================================================

-- Generic data store for arbitrary network-level data
-- Supports storing configuration, results, statistics, scripts, etc.
CREATE TABLE network_data_store (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    category TEXT NOT NULL,          -- 'config', 'results', 'statistics', 'scripts', etc.
    name TEXT NOT NULL,              -- Specific name within category
    data_format TEXT DEFAULT 'json', -- 'json', 'parquet', 'csv', 'binary', 'text'
    data BLOB NOT NULL,              -- Serialized data
    metadata TEXT,                   -- JSON metadata about the data
    checksum TEXT,                   -- Data integrity hash
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CONSTRAINT fk_datastore_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT uq_datastore_network_category_name 
        UNIQUE (network_id, category, name),
    CONSTRAINT valid_data_format 
        CHECK (data_format IN ('json', 'parquet', 'csv', 'binary', 'text', 'yaml', 'toml'))
);

-- Minimal indexes for data retrieval
CREATE INDEX idx_datastore_network ON network_data_store(network_id);
CREATE INDEX idx_datastore_category ON network_data_store(network_id, category);

-- ============================================================================
-- DOCUMENTATION AND NOTES
-- ============================================================================

-- Network-level notes and documentation
CREATE TABLE network_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    tags TEXT,                       -- JSON array of tags
    note_type TEXT DEFAULT 'note',   -- 'note', 'todo', 'warning', 'info'
    priority INTEGER DEFAULT 0,     -- 0=normal, 1=high, -1=low
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CONSTRAINT fk_notes_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT valid_note_type 
        CHECK (note_type IN ('note', 'todo', 'warning', 'info', 'doc'))
);

-- Minimal indexes for notes
CREATE INDEX idx_notes_network ON network_notes(network_id);

-- Component-specific notes and documentation
CREATE TABLE component_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    tags TEXT,                       -- JSON array of tags
    note_type TEXT DEFAULT 'note',   -- 'note', 'todo', 'warning', 'info'
    priority INTEGER DEFAULT 0,     -- 0=normal, 1=high, -1=low
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    CONSTRAINT fk_component_notes_component 
        FOREIGN KEY (component_id) REFERENCES components(id) ON DELETE CASCADE,
    CONSTRAINT valid_component_note_type 
        CHECK (note_type IN ('note', 'todo', 'warning', 'info', 'doc'))
);

-- Minimal indexes for component notes
CREATE INDEX idx_component_notes_component ON component_notes(component_id);

-- ============================================================================
-- SOLVE RESULTS AND STATISTICS
-- ============================================================================

-- Network solve results - stores solver outputs and statistics
-- This is where PyPSA solve results are stored after successful solves
CREATE TABLE network_solve_results (
    network_id INTEGER NOT NULL,
    scenario_id INTEGER NOT NULL,  -- References scenarios table (master scenario has explicit ID)
    
    -- Solve metadata
    solved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    solver_name TEXT NOT NULL,          -- 'highs', 'gurobi', 'cplex', etc.
    solve_type TEXT NOT NULL,           -- 'pypsa_optimization', 'monte_carlo', 'sensitivity', etc.
    solve_status TEXT NOT NULL,         -- 'optimal', 'infeasible', 'unbounded', etc.
    objective_value REAL,               -- Objective function value
    solve_time_seconds REAL,            -- Time taken to solve
    
    -- Everything else stored as JSON for maximum flexibility
    results_json TEXT NOT NULL,         -- All results, statistics, whatever the solver produces
    metadata_json TEXT,                 -- Solver settings, input parameters, build info
    
    PRIMARY KEY (network_id, scenario_id),
    
    FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

-- Minimal indexes for performance
CREATE INDEX idx_solve_results_network ON network_solve_results(network_id);
CREATE INDEX idx_solve_results_scenario ON network_solve_results(scenario_id);

-- ============================================================================
-- YEAR-BASED SOLVE RESULTS
-- ============================================================================

-- Year-based solve results - stores solver outputs and statistics by year
-- This enables capacity expansion analysis and year-over-year comparisons
CREATE TABLE network_solve_results_by_year (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    scenario_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    
    -- Year-specific statistics (same structure as main results but year-specific)
    results_json TEXT NOT NULL,         -- All results, statistics for this year only
    metadata_json TEXT,                 -- Solver settings, input parameters for this year
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_solve_results_year_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT fk_solve_results_year_scenario 
        FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE,
    CONSTRAINT uq_solve_results_year_unique 
        UNIQUE (network_id, scenario_id, year),
    CONSTRAINT valid_year CHECK (year >= 1900 AND year <= 2100)
);

-- Minimal indexes for performance
CREATE INDEX idx_solve_results_year_network ON network_solve_results_by_year(network_id);
CREATE INDEX idx_solve_results_year_scenario ON network_solve_results_by_year(scenario_id);

-- Optional: Registry of solve type schemas for frontend introspection
CREATE TABLE solve_type_schemas (
    solve_type TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    description TEXT,
    json_schema TEXT,                   -- JSON Schema describing the expected structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- UTILITY VIEWS (SIMPLIFIED)
-- ============================================================================

-- View for recent network activity (simplified without audit/cache tables)
CREATE VIEW network_activity_summary AS
SELECT 
    n.id as network_id,
    n.name as network_name,
    COUNT(DISTINCT c.id) as components_count,
    COUNT(DISTINCT ca.id) as attributes_count,
    COUNT(DISTINCT nn.id) as notes_count,
    COUNT(DISTINCT nds.id) as data_store_entries_count,
    MAX(c.updated_at) as last_component_update,
    MAX(ca.updated_at) as last_attribute_update,
    MAX(nn.updated_at) as last_note_update,
    MAX(nds.updated_at) as last_data_update
FROM networks n
LEFT JOIN components c ON n.id = c.network_id
LEFT JOIN component_attributes ca ON c.id = ca.component_id
LEFT JOIN network_notes nn ON n.id = nn.network_id
LEFT JOIN network_data_store nds ON n.id = nds.network_id
GROUP BY n.id, n.name;

-- ============================================================================
-- CONNECTIVITY VIEWS - Human-readable bus connections
-- ============================================================================

-- View for components with single bus connections (generators, loads, etc.)
CREATE VIEW components_with_bus AS
SELECT 
    c.*,
    b.name as bus_name
FROM components c
LEFT JOIN components b ON c.bus_id = b.id AND b.component_type = 'BUS'
WHERE c.component_type IN ('GENERATOR', 'LOAD', 'STORAGE_UNIT', 'STORE');

-- View for components with dual bus connections (lines, links)
CREATE VIEW components_with_buses AS
SELECT 
    c.*,
    b0.name as bus0_name,
    b1.name as bus1_name
FROM components c
LEFT JOIN components b0 ON c.bus0_id = b0.id AND b0.component_type = 'BUS'
LEFT JOIN components b1 ON c.bus1_id = b1.id AND b1.component_type = 'BUS'
WHERE c.component_type IN ('LINE', 'LINK');

-- Unified view for all components with resolved bus connections
CREATE VIEW components_with_connectivity AS
SELECT 
    c.*,
    CASE 
        WHEN c.component_type = 'BUS' THEN NULL
        WHEN c.component_type IN ('GENERATOR', 'LOAD', 'STORAGE_UNIT', 'STORE') THEN 
            (SELECT b.name FROM components b WHERE b.id = c.bus_id AND b.component_type = 'BUS')
        ELSE NULL
    END as bus_name,
    CASE 
        WHEN c.component_type IN ('LINE', 'LINK') THEN 
            (SELECT b.name FROM components b WHERE b.id = c.bus0_id AND b.component_type = 'BUS')
        ELSE NULL
    END as bus0_name,
    CASE 
        WHEN c.component_type IN ('LINE', 'LINK') THEN 
            (SELECT b.name FROM components b WHERE b.id = c.bus1_id AND b.component_type = 'BUS')
        ELSE NULL
    END as bus1_name
FROM components c;

-- ============================================================================
-- DEFAULT CARRIERS SETUP
-- ============================================================================

-- Note: Default carriers will be created automatically when a network is created
-- This is handled in the application code to ensure proper network_id assignment
-- The default carriers are:
-- - AC (default for electrical buses and components)
-- - DC (for DC electrical systems)  
-- - heat (for heating systems)
-- - gas (for gas systems)
-- - electricity (generic electrical carrier)

-- These carriers follow PyPSA conventions and ensure all components can have
-- appropriate carrier assignments without requiring manual setup