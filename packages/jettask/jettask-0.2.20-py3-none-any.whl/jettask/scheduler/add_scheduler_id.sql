-- Migration to add scheduler_id column to scheduled_tasks table
-- This allows unique identification and deduplication of tasks

-- Add the scheduler_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'scheduled_tasks' 
        AND column_name = 'scheduler_id'
    ) THEN
        ALTER TABLE scheduled_tasks 
        ADD COLUMN scheduler_id VARCHAR(255) UNIQUE;
        
        -- Add comment
        COMMENT ON COLUMN scheduled_tasks.scheduler_id IS 
        'Unique identifier for the task, used for deduplication';
    END IF;
END $$;

-- Create index for scheduler_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_scheduler_id 
ON scheduled_tasks(scheduler_id) 
WHERE scheduler_id IS NOT NULL;