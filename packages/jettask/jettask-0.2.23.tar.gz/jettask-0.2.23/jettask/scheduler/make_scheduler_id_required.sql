-- Migration to make scheduler_id NOT NULL
-- First, update any NULL scheduler_id values with generated ones

-- Update NULL scheduler_id values with generated unique IDs
UPDATE scheduled_tasks 
SET scheduler_id = CONCAT(task_name, '_', task_type, '_', id)
WHERE scheduler_id IS NULL;

-- Now make the column NOT NULL
ALTER TABLE scheduled_tasks 
ALTER COLUMN scheduler_id SET NOT NULL;

-- Ensure the UNIQUE constraint exists
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM pg_constraint 
        WHERE conname = 'scheduled_tasks_scheduler_id_key'
    ) THEN
        ALTER TABLE scheduled_tasks 
        ADD CONSTRAINT scheduled_tasks_scheduler_id_key UNIQUE (scheduler_id);
    END IF;
END $$;

-- Update the comment
COMMENT ON COLUMN scheduled_tasks.scheduler_id IS 
'Unique identifier for the task (required, used for deduplication)';