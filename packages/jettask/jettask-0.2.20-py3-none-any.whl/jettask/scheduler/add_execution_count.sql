-- 为scheduled_tasks表添加执行次数字段
ALTER TABLE scheduled_tasks 
ADD COLUMN IF NOT EXISTS execution_count INTEGER DEFAULT 0;

-- 添加注释
COMMENT ON COLUMN scheduled_tasks.execution_count IS '任务执行次数';

-- 为现有记录设置初始值（可选，根据历史数据估算）
UPDATE scheduled_tasks 
SET execution_count = 0 
WHERE execution_count IS NULL;