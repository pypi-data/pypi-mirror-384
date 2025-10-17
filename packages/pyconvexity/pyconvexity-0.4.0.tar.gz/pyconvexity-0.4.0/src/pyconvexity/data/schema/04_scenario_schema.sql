-- ============================================================================
-- SCENARIO-AWARE ATTRIBUTES AND CONSTRAINTS SCHEMA
-- Support for multiple scenarios within networks and Python constraint execution
-- Version 1.0.0
-- ============================================================================

-- ============================================================================
-- SCENARIOS TABLE
-- ============================================================================

-- Scenarios table - represents different modeling scenarios within a network
-- The "Main" scenario is the master scenario (explicit, not implicit)
-- "Master" refers to the fact that this is the main reference scenario
CREATE TABLE scenarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    network_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    is_master BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_scenarios_network 
        FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    CONSTRAINT uq_scenarios_network_name 
        UNIQUE (network_id, name)
);

-- Index for efficient scenario lookups
CREATE INDEX idx_scenarios_network ON scenarios(network_id);
CREATE INDEX idx_scenarios_master ON scenarios(is_master);

-- ============================================================================
-- SCENARIO MANAGEMENT TRIGGERS
-- ============================================================================

-- Ensure exactly one master scenario per network
CREATE TRIGGER ensure_single_master_scenario
    BEFORE INSERT ON scenarios
    FOR EACH ROW
    WHEN NEW.is_master = TRUE
BEGIN
    UPDATE scenarios 
    SET is_master = FALSE 
    WHERE network_id = NEW.network_id AND is_master = TRUE;
END;

-- Ensure exactly one master scenario per network on update
CREATE TRIGGER ensure_single_master_scenario_update
    BEFORE UPDATE ON scenarios
    FOR EACH ROW
    WHEN NEW.is_master = TRUE AND OLD.is_master = FALSE
BEGIN
    UPDATE scenarios 
    SET is_master = FALSE 
    WHERE network_id = NEW.network_id AND is_master = TRUE AND id != NEW.id;
END;

-- Prevent deletion of master scenario
CREATE TRIGGER prevent_master_scenario_deletion
    BEFORE DELETE ON scenarios
    FOR EACH ROW
    WHEN OLD.is_master = TRUE
BEGIN
    SELECT RAISE(ABORT, 'Cannot delete master scenario');
END;

-- ============================================================================
-- SCENARIO UTILITY FUNCTIONS
-- ============================================================================

-- Create a view for easy attribute resolution with scenario inheritance
CREATE VIEW component_attributes_with_scenario AS
SELECT 
    ca.component_id,
    ca.attribute_name,
    ca.storage_type,
    ca.static_value,
    ca.timeseries_data,
    ca.data_type,
    ca.unit,
    ca.is_input,
    COALESCE(ca.scenario_id, 0) as scenario_id,
    CASE 
        WHEN ca.scenario_id IS NULL THEN 'Main'
        ELSE s.name
    END as scenario_name,
    ca.created_at,
    ca.updated_at
FROM component_attributes ca
LEFT JOIN scenarios s ON ca.scenario_id = s.id;

-- ============================================================================
-- AUTOMATIC MASTER SCENARIO CREATION
-- ============================================================================

-- Trigger to automatically create "Main" scenario (the master scenario) when a network is created
-- This ensures every network has exactly one master scenario that serves as the main reference
CREATE TRIGGER create_master_scenario_for_network
    AFTER INSERT ON networks
    FOR EACH ROW
BEGIN
    INSERT INTO scenarios (network_id, name, description, is_master)
    VALUES (NEW.id, 'Main', 'Main scenario (default)', TRUE);
END;

-- ============================================================================
-- COMPONENT VALIDATION FOR CONSTRAINT
-- ============================================================================

-- Note: CONSTRAINT components can have NULL carrier_id - this is now enforced
-- by the CHECK constraint in the components table schema

-- ============================================================================
-- INITIALIZATION
-- ============================================================================

-- This schema extends the existing core schema with scenario support
-- "Main" scenarios (master scenarios) are automatically created for existing networks
INSERT INTO scenarios (network_id, name, description, is_master)
SELECT id, 'Main', 'Main scenario (default)', TRUE
FROM networks
WHERE id NOT IN (SELECT network_id FROM scenarios WHERE is_master = TRUE); 