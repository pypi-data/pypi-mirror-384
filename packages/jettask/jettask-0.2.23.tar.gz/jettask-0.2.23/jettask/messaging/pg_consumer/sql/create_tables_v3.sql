-- 优化后的任务表结构设计 V3
-- 根据实际需求调整字段

-- 1. 任务基础信息表 (tasks)
-- 存储任务的元数据，一个任务只有一条记录
CREATE TABLE IF NOT EXISTS tasks (
    id BIGSERIAL PRIMARY KEY,                     -- 内部主键
    stream_id TEXT UNIQUE NOT NULL,               -- Redis Stream的message id (例如: 1757039473571-0)
    queue TEXT NOT NULL,                          -- 队列名称
    namespace TEXT DEFAULT 'default',             -- 命名空间
    scheduled_task_id TEXT,                       -- 调度任务ID（如果是调度任务产生的）
    payload JSONB NOT NULL,                       -- 任务参数（完整的event_data）
    priority INT DEFAULT 0,                       -- 任务优先级
    source TEXT,                                  -- 任务来源（例如：api/scheduler/manual）
    metadata JSONB DEFAULT '{}'::jsonb,           -- 额外的元数据
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 任务创建时间
);

-- 为stream_id创建唯一索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_tasks_stream_id ON tasks(stream_id);

-- 为queue创建索引，方便查询
CREATE INDEX IF NOT EXISTS idx_tasks_queue ON tasks(queue);

-- 为namespace创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_namespace ON tasks(namespace);

-- 为scheduled_task_id创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_scheduled_task_id ON tasks(scheduled_task_id);

-- 为created_at创建索引
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- 为namespace和queue创建复合索引
CREATE INDEX IF NOT EXISTS idx_tasks_namespace_queue ON tasks(namespace, queue);

-- 为namespace和scheduled_task_id创建复合索引
CREATE INDEX IF NOT EXISTS idx_tasks_namespace_scheduled ON tasks(namespace, scheduled_task_id) WHERE scheduled_task_id IS NOT NULL;

-- 2. 任务运行记录表 (task_runs)
-- 记录每个消费者组对任务的执行情况
CREATE TABLE IF NOT EXISTS task_runs (
    id BIGSERIAL PRIMARY KEY,                     -- 内部主键
    task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,  -- 关联任务ID
    stream_id TEXT NOT NULL,                      -- 冗余存储stream_id方便查询
    task_name TEXT NOT NULL,                      -- 任务名称（执行的具体任务函数）
    consumer_group TEXT NOT NULL,                 -- 消费者组名称
    consumer_name TEXT,                           -- 具体的消费者实例名
    worker_id TEXT,                               -- Worker ID
    status TEXT NOT NULL DEFAULT 'pending',       -- 执行状态（pending/running/success/failed/retrying/timeout/skipped）
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,  -- 记录创建时间
    start_time TIMESTAMPTZ,                       -- 开始执行时间
    end_time TIMESTAMPTZ,                         -- 结束时间
    duration_ms BIGINT,                           -- 执行耗时（毫秒）
    retry_count INT DEFAULT 0,                    -- 重试次数
    max_retries INT DEFAULT 3,                    -- 最大重试次数
    error_message TEXT,                           -- 错误信息
    error_details JSONB,                          -- 详细错误信息（包含堆栈等）
    result JSONB,                                 -- 执行结果
    logs TEXT[],                                  -- 执行日志
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP  -- 最后更新时间
);

-- 为task_id创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_task_id ON task_runs(task_id);

-- 为stream_id创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_stream_id ON task_runs(stream_id);

-- 为task_name创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_task_name ON task_runs(task_name);

-- 为consumer_group创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_consumer_group ON task_runs(consumer_group);

-- 为status创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status);

-- 为created_at创建索引
CREATE INDEX IF NOT EXISTS idx_task_runs_created_at ON task_runs(created_at);

-- 创建复合索引优化查询
CREATE INDEX IF NOT EXISTS idx_task_runs_task_group ON task_runs(task_id, consumer_group);
CREATE INDEX IF NOT EXISTS idx_task_runs_group_status ON task_runs(consumer_group, status);
CREATE INDEX IF NOT EXISTS idx_task_runs_stream_group ON task_runs(stream_id, consumer_group);

-- 为了保证同一个任务在同一个消费者组中只有一条运行记录，创建唯一约束
CREATE UNIQUE INDEX IF NOT EXISTS idx_task_runs_unique_task_group ON task_runs(task_id, consumer_group);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为task_runs表创建触发器
DROP TRIGGER IF EXISTS update_task_runs_updated_at ON task_runs;
CREATE TRIGGER update_task_runs_updated_at 
    BEFORE UPDATE ON task_runs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 3. 创建视图方便查询
-- 任务执行概览视图
CREATE OR REPLACE VIEW task_execution_overview AS
SELECT 
    t.id,
    t.stream_id,
    t.queue,
    t.namespace,
    t.scheduled_task_id,
    t.created_at,
    COUNT(DISTINCT tr.consumer_group) as consumer_group_count,
    COUNT(tr.id) as total_runs,
    COUNT(CASE WHEN tr.status = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN tr.status = 'running' THEN 1 END) as running_count,
    AVG(tr.duration_ms) as avg_duration_ms,
    MAX(tr.end_time) as last_execution_time
FROM tasks t
LEFT JOIN task_runs tr ON t.id = tr.task_id
GROUP BY t.id;

-- 消费者组执行统计视图
CREATE OR REPLACE VIEW consumer_group_stats AS
SELECT 
    tr.consumer_group,
    tr.task_name,
    t.queue,
    t.namespace,
    COUNT(DISTINCT tr.task_id) as total_tasks,
    COUNT(CASE WHEN tr.status = 'success' THEN 1 END) as success_count,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_count,
    COUNT(CASE WHEN tr.status = 'running' THEN 1 END) as running_count,
    AVG(tr.duration_ms) as avg_duration_ms,
    SUM(tr.retry_count) as total_retries,
    MAX(tr.end_time) as last_activity
FROM task_runs tr
JOIN tasks t ON tr.task_id = t.id
GROUP BY tr.consumer_group, tr.task_name, t.queue, t.namespace;

-- 按命名空间的任务统计视图
CREATE OR REPLACE VIEW namespace_task_stats AS
SELECT 
    t.namespace,
    t.queue,
    COUNT(DISTINCT t.id) as total_tasks,
    COUNT(DISTINCT t.scheduled_task_id) as scheduled_tasks,
    COUNT(DISTINCT tr.task_name) as unique_task_names,
    COUNT(DISTINCT tr.consumer_group) as consumer_groups,
    COUNT(tr.id) as total_runs,
    COUNT(CASE WHEN tr.status = 'success' THEN 1 END) as success_runs,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_runs,
    AVG(tr.duration_ms) as avg_duration_ms,
    MIN(t.created_at) as first_task_at,
    MAX(t.created_at) as last_task_at
FROM tasks t
LEFT JOIN task_runs tr ON t.id = tr.task_id
GROUP BY t.namespace, t.queue;

-- 添加注释
COMMENT ON TABLE tasks IS '任务基础信息表，存储任务的元数据';
COMMENT ON TABLE task_runs IS '任务运行记录表，记录每个消费者组对任务的执行情况';
COMMENT ON COLUMN tasks.stream_id IS 'Redis Stream的消息ID，确保幂等性';
COMMENT ON COLUMN tasks.namespace IS '命名空间，用于多租户隔离';
COMMENT ON COLUMN tasks.scheduled_task_id IS '调度任务ID，标识该任务是否由调度器产生';
COMMENT ON COLUMN tasks.payload IS '任务参数，存储完整的event_data';
COMMENT ON COLUMN task_runs.task_name IS '具体执行的任务函数名称';
COMMENT ON COLUMN task_runs.consumer_group IS '消费者组名称，格式如：jettask:QUEUE:queue_name:task_name';
COMMENT ON COLUMN task_runs.created_at IS '记录创建时间，标记任务何时被消费者接收';
COMMENT ON COLUMN task_runs.start_time IS '实际开始执行时间，可能与created_at不同';
COMMENT ON COLUMN task_runs.duration_ms IS '执行耗时（毫秒），由应用层计算';