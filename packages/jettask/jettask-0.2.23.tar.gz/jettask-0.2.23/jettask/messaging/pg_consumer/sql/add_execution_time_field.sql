-- 添加execution_time_ms字段到task_runs表
-- execution_time_ms: 实际执行时间（毫秒），从任务开始执行到执行完成的时间
-- duration_ms: 总耗时（毫秒），从任务创建到执行完成的时间

-- 检查字段是否存在，如果不存在则添加
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'task_runs' 
        AND column_name = 'execution_time_ms'
    ) THEN
        ALTER TABLE task_runs 
        ADD COLUMN execution_time_ms BIGINT;
        
        COMMENT ON COLUMN task_runs.execution_time_ms IS '实际执行时间（毫秒），从任务开始执行到执行完成的时间';
        
        -- 为已有数据计算execution_time_ms（如果有start_time和end_time）
        UPDATE task_runs 
        SET execution_time_ms = EXTRACT(EPOCH FROM (end_time - start_time)) * 1000
        WHERE start_time IS NOT NULL 
        AND end_time IS NOT NULL
        AND execution_time_ms IS NULL;
    END IF;
END $$;

-- 确保duration_ms字段的注释正确
COMMENT ON COLUMN task_runs.duration_ms IS '总耗时（毫秒），从任务创建到执行完成的时间';