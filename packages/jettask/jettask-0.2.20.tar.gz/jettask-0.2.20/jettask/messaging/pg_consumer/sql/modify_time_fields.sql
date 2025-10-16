-- 修改task_runs表的时间字段，改为存储秒数而不是毫秒
-- 1. 重命名字段并修改类型
-- 2. 将已有的毫秒数据转换为秒

DO $$ 
BEGIN
    -- 处理duration_ms字段
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'task_runs' AND column_name = 'duration_ms'
    ) THEN
        -- 如果duration字段不存在，创建它
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'task_runs' AND column_name = 'duration'
        ) THEN
            ALTER TABLE task_runs ADD COLUMN duration DOUBLE PRECISION;
        END IF;
        
        -- 将毫秒转换为秒
        UPDATE task_runs 
        SET duration = duration_ms / 1000.0 
        WHERE duration_ms IS NOT NULL AND duration IS NULL;
        
        -- 删除旧字段
        ALTER TABLE task_runs DROP COLUMN IF EXISTS duration_ms;
    END IF;
    
    -- 处理execution_time_ms字段
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'task_runs' AND column_name = 'execution_time_ms'
    ) THEN
        -- 如果execution_time字段不存在，创建它
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'task_runs' AND column_name = 'execution_time'
        ) THEN
            ALTER TABLE task_runs ADD COLUMN execution_time DOUBLE PRECISION;
        END IF;
        
        -- 将毫秒转换为秒
        UPDATE task_runs 
        SET execution_time = execution_time_ms / 1000.0 
        WHERE execution_time_ms IS NOT NULL AND execution_time IS NULL;
        
        -- 删除旧字段
        ALTER TABLE task_runs DROP COLUMN IF EXISTS execution_time_ms;
    END IF;
    
    -- 如果字段已经是正确的格式，确保它们存在
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'task_runs' AND column_name = 'duration'
    ) THEN
        ALTER TABLE task_runs ADD COLUMN duration DOUBLE PRECISION;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'task_runs' AND column_name = 'execution_time'
    ) THEN
        ALTER TABLE task_runs ADD COLUMN execution_time DOUBLE PRECISION;
    END IF;
END $$;

-- 添加注释
COMMENT ON COLUMN task_runs.duration IS '总耗时（秒），从任务创建到执行完成的时间';
COMMENT ON COLUMN task_runs.execution_time IS '实际执行时间（秒），从任务开始执行到执行完成的时间';