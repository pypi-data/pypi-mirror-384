-- Migration to add index for scheduler_id field
-- This index is critical for performance as we heavily rely on scheduler_id for lookups

-- Create unique index on scheduler_id for fast lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_tasks_scheduler_id 
ON scheduled_tasks(scheduler_id);

-- Also add a comment to clarify the importance
COMMENT ON INDEX idx_scheduled_tasks_scheduler_id IS 
'Unique index on scheduler_id for fast task lookups and deduplication';