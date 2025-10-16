-- Performance optimization for scheduled_tasks table
-- This migration adds necessary indexes for optimal query performance

-- 1. Unique index on scheduler_id (已经存在，但确保创建)
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_tasks_scheduler_id 
ON scheduled_tasks(scheduler_id);

-- 2. Index for ready tasks query (get_ready_tasks)
-- 这是最频繁的查询之一，需要复合索引
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_ready 
ON scheduled_tasks(next_run_time, enabled) 
WHERE enabled = true AND next_run_time IS NOT NULL;

-- 3. Index for task listing with filters (list_tasks)
-- created_at用于排序
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_created 
ON scheduled_tasks(created_at DESC);

-- 4. Index for task_name lookups (常用于查找特定任务)
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_name 
ON scheduled_tasks(task_name);

-- 5. Composite index for enabled tasks with type
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled_type 
ON scheduled_tasks(enabled, task_type) 
WHERE enabled = true;

-- 6. Index for update operations by id (primary key已自动有索引)
-- 但确保主键约束存在
-- (主键自动创建索引，无需额外操作)

-- 7. Index for task execution history queries
CREATE INDEX IF NOT EXISTS idx_task_history_task_scheduled 
ON task_execution_history(task_id, scheduled_time DESC);

-- 8. Index for history status queries
CREATE INDEX IF NOT EXISTS idx_task_history_status_created 
ON task_execution_history(status, created_at DESC);

-- 添加表注释
COMMENT ON TABLE scheduled_tasks IS 'Scheduled tasks configuration table with optimized indexes';

-- 分析表以更新统计信息
ANALYZE scheduled_tasks;
ANALYZE task_execution_history;