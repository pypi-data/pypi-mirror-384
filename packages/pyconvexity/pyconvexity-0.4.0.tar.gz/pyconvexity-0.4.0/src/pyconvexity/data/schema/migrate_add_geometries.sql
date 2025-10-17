-- ============================================================================
-- MIGRATION: Add Component Geometries Support
-- Adds the component_geometries table to existing databases
-- This migration is safe and backwards compatible - existing functionality is unchanged
-- ============================================================================

-- Check if the table already exists before creating
CREATE TABLE IF NOT EXISTS component_geometries (
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

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_component_geometries_component 
    ON component_geometries(component_id);

CREATE INDEX IF NOT EXISTS idx_component_geometries_type 
    ON component_geometries(geometry_type);

CREATE INDEX IF NOT EXISTS idx_component_geometries_bbox 
    ON component_geometries(bbox_min_lng, bbox_min_lat, bbox_max_lng, bbox_max_lat);

-- Create trigger for automatic timestamp updates
DROP TRIGGER IF EXISTS update_component_geometries_timestamp;

CREATE TRIGGER update_component_geometries_timestamp
    BEFORE UPDATE ON component_geometries
    FOR EACH ROW
BEGIN
    UPDATE component_geometries 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update schema version
UPDATE system_metadata 
SET value = '2.5.0', 
    updated_at = CURRENT_TIMESTAMP,
    description = 'Database schema version - Added component_geometries table'
WHERE key = 'schema_version';

-- Add metadata about the migration
INSERT OR REPLACE INTO system_metadata (key, value, description) 
VALUES ('geometries_migration_applied', datetime('now'), 'Timestamp when component geometries migration was applied');

-- Verify the migration
SELECT 
    'Migration completed successfully!' as message,
    COUNT(*) as existing_geometries
FROM component_geometries;
