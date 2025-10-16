-- 添加priority字段到scheduled_tasks表
-- 用于支持定时任务的优先级设置

-- 检查是否已经存在priority字段，避免重复添加
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'scheduled_tasks' 
        AND column_name = 'priority'
    ) THEN
        ALTER TABLE scheduled_tasks 
        ADD COLUMN priority INTEGER DEFAULT NULL;
        
        -- 添加注释
        COMMENT ON COLUMN scheduled_tasks.priority IS '任务优先级 (1=最高, 数字越大优先级越低，NULL=默认最低)';
        
        -- 创建索引以提高查询性能
        CREATE INDEX idx_scheduled_tasks_priority ON scheduled_tasks(priority);
        
        RAISE NOTICE 'Added priority column to scheduled_tasks table';
    ELSE
        RAISE NOTICE 'Priority column already exists in scheduled_tasks table';
    END IF;
END $$;