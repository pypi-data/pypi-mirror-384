-- 定时任务表
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id BIGSERIAL PRIMARY KEY,               -- 自增主键（任务唯一标识）
    scheduler_id VARCHAR(255) NOT NULL UNIQUE, -- 任务的唯一标识符（必填，用于去重）
    task_name VARCHAR(255) NOT NULL,        -- 要执行的函数名（对应@app.task注册的任务名）
    task_type VARCHAR(50) NOT NULL,         -- 任务类型: cron, interval, once
    
    -- 任务执行相关
    queue_name VARCHAR(100) NOT NULL,       -- 目标队列名
    task_args JSONB DEFAULT '[]',           -- 任务参数
    task_kwargs JSONB DEFAULT '{}',         -- 任务关键字参数
    
    -- 调度相关
    cron_expression VARCHAR(100),           -- cron表达式 (task_type=cron时使用)
    interval_seconds NUMERIC(10,2),         -- 间隔秒数 (task_type=interval时使用，支持小数)
    next_run_time TIMESTAMP WITH TIME ZONE, -- 下次执行时间
    last_run_time TIMESTAMP WITH TIME ZONE, -- 上次执行时间
    
    -- 状态和控制
    enabled BOOLEAN DEFAULT true,           -- 是否启用
    max_retries INTEGER DEFAULT 3,          -- 最大重试次数
    retry_delay INTEGER DEFAULT 60,         -- 重试延迟(秒)
    timeout INTEGER DEFAULT 300,            -- 任务超时时间(秒)
    priority INTEGER DEFAULT NULL,          -- 任务优先级 (1=最高, 数字越大优先级越低，NULL=默认最低)
    
    -- 元数据
    description TEXT,                       -- 任务描述
    tags JSONB DEFAULT '[]',                -- 标签
    metadata JSONB DEFAULT '{}',            -- 额外元数据
    
    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run_time) WHERE enabled = true;
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_task_type ON scheduled_tasks(task_type);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_queue ON scheduled_tasks(queue_name);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_enabled ON scheduled_tasks(enabled);
CREATE UNIQUE INDEX IF NOT EXISTS idx_scheduled_tasks_scheduler_id ON scheduled_tasks(scheduler_id);

-- 任务执行历史表
CREATE TABLE IF NOT EXISTS task_execution_history (
    id BIGSERIAL PRIMARY KEY,
    task_id BIGINT NOT NULL,                -- 关联的任务ID（外键到 scheduled_tasks.id）
    event_id VARCHAR(255) NOT NULL,         -- 执行事件ID
    
    -- 执行信息
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,  -- 计划执行时间
    started_at TIMESTAMP WITH TIME ZONE,               -- 实际开始时间
    finished_at TIMESTAMP WITH TIME ZONE,              -- 完成时间
    
    -- 执行结果
    status VARCHAR(50) NOT NULL,            -- pending, running, success, failed, timeout
    result JSONB,                           -- 执行结果
    error_message TEXT,                     -- 错误信息
    retry_count INTEGER DEFAULT 0,          -- 重试次数
    
    -- 性能指标
    duration_ms INTEGER,                    -- 执行耗时(毫秒)
    worker_id VARCHAR(100),                 -- 执行的worker ID
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_execution_history(task_id);
CREATE INDEX IF NOT EXISTS idx_task_history_event_id ON task_execution_history(event_id);
CREATE INDEX IF NOT EXISTS idx_task_history_status ON task_execution_history(status);
CREATE INDEX IF NOT EXISTS idx_task_history_scheduled ON task_execution_history(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_task_history_created ON task_execution_history(created_at);

-- 更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_scheduled_tasks_updated_at BEFORE UPDATE
    ON scheduled_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();