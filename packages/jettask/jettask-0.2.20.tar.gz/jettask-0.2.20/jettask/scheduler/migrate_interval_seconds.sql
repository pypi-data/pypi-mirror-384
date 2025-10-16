-- Migration to change interval_seconds from INTEGER to NUMERIC
-- This allows storing decimal values like 0.1 seconds

-- Alter the column type
ALTER TABLE scheduled_tasks 
ALTER COLUMN interval_seconds TYPE NUMERIC(10,2);

-- Add a comment to document the change
COMMENT ON COLUMN scheduled_tasks.interval_seconds IS 'Interval in seconds for interval-type tasks (supports decimal values)';