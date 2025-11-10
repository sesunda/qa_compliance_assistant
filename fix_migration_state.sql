-- Fix migration state: Mark consolidated migration as applied
-- and add missing columns to projects table

-- Step 1: Clear old migration versions and set to 001
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('001');

-- Step 2: Add missing columns to projects table (if they don't exist)
DO $$
BEGIN
    -- Add project_type column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='projects' AND column_name='project_type') THEN
        ALTER TABLE projects ADD COLUMN project_type VARCHAR(100) DEFAULT 'compliance_assessment';
        RAISE NOTICE 'Added project_type column';
    ELSE
        RAISE NOTICE 'project_type column already exists';
    END IF;
    
    -- Add start_date column
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name='projects' AND column_name='start_date') THEN
        ALTER TABLE projects ADD COLUMN start_date DATE;
        RAISE NOTICE 'Added start_date column';
    ELSE
        RAISE NOTICE 'start_date column already exists';
    END IF;
END $$;

-- Verify the changes
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'projects' 
AND column_name IN ('project_type', 'start_date');
