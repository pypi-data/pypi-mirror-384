-- 数据迁移脚本
-- 从旧的单表结构迁移到新的双表结构

BEGIN;

-- 1. 先备份原表（如果存在）
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        -- 如果tasks表已存在，重命名为备份表
        IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks_backup') THEN
            ALTER TABLE tasks RENAME TO tasks_backup;
        ELSE
            -- 如果备份表已存在，创建带时间戳的备份
            EXECUTE format('ALTER TABLE tasks RENAME TO tasks_backup_%s', 
                          to_char(now(), 'YYYYMMDD_HH24MISS'));
        END IF;
    END IF;
END $$;

-- 2. 执行创建新表的SQL（引用create_new_tables.sql的内容）
-- 注意：在实际使用时，应该先运行create_new_tables.sql

-- 3. 如果有旧数据，进行数据迁移
DO $$
BEGIN
    -- 检查是否有备份表
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks_backup') THEN
        -- 迁移任务基础信息到新的tasks表
        INSERT INTO tasks (
            stream_id,
            queue,
            task_name,
            task_type,
            payload,
            priority,
            created_at,
            scheduled_at,
            status,
            source,
            metadata
        )
        SELECT 
            COALESCE(task_id, 'unknown-' || id::text) as stream_id,  -- 使用task_id作为stream_id
            COALESCE(queue_name, 'default') as queue,
            COALESCE(task_name, 'unknown') as task_name,
            task_type,
            COALESCE(task_data, '{}'::jsonb) as payload,
            COALESCE(priority, 0) as priority,
            created_at,
            trigger_time as scheduled_at,
            CASE 
                WHEN status IN ('pending', 'running', 'completed', 'failed') THEN status
                WHEN status = 'success' THEN 'completed'
                ELSE 'pending'
            END as status,
            'migration' as source,
            jsonb_build_object(
                'migrated_at', now(),
                'original_id', id,
                'original_status', status
            ) as metadata
        FROM tasks_backup
        ON CONFLICT (stream_id) DO NOTHING;  -- 避免重复

        -- 迁移执行记录到task_runs表
        -- 由于旧表是单表结构，我们为每个任务创建一条运行记录
        INSERT INTO task_runs (
            task_id,
            stream_id,
            consumer_group,
            consumer_name,
            worker_id,
            status,
            start_time,
            end_time,
            retry_count,
            error_message,
            result
        )
        SELECT 
            t.id as task_id,
            t.stream_id,
            'default_group' as consumer_group,  -- 默认消费者组
            tb.consumer as consumer_name,
            tb.consumer as worker_id,
            CASE 
                WHEN tb.status = 'success' THEN 'success'
                WHEN tb.status IN ('failed', 'error') THEN 'failed'
                WHEN tb.status = 'running' THEN 'running'
                WHEN tb.status = 'timeout' THEN 'timeout'
                ELSE 'pending'
            END as status,
            tb.started_at as start_time,
            tb.completed_at as end_time,
            COALESCE(tb.retry_count, 0) as retry_count,
            tb.error as error_message,
            tb.result
        FROM tasks_backup tb
        JOIN tasks t ON t.stream_id = COALESCE(tb.task_id, 'unknown-' || tb.id::text)
        WHERE tb.status IS NOT NULL;

        RAISE NOTICE 'Data migration completed successfully';
    ELSE
        RAISE NOTICE 'No backup table found, skipping data migration';
    END IF;
END $$;

-- 4. 创建兼容性视图（可选）
-- 如果有代码依赖旧的表结构，可以创建视图提供兼容性
CREATE OR REPLACE VIEW tasks_legacy AS
SELECT 
    t.id,
    t.stream_id as task_id,
    t.queue as queue_name,
    t.task_name,
    t.task_type,
    t.payload as task_data,
    t.priority,
    tr.consumer_name as consumer,
    tr.status,
    tr.start_time as started_at,
    tr.end_time as completed_at,
    tr.retry_count,
    tr.error_message as error,
    tr.result,
    t.created_at,
    tr.updated_at,
    t.scheduled_at as trigger_time
FROM tasks t
LEFT JOIN task_runs tr ON t.id = tr.task_id 
    AND tr.consumer_group = 'default_group';  -- 兼容旧代码，只显示默认组

-- 5. 更新序列（如果需要）
DO $$
DECLARE
    max_id BIGINT;
BEGIN
    -- 获取最大ID
    SELECT COALESCE(MAX(id), 0) INTO max_id FROM tasks;
    -- 更新序列
    IF max_id > 0 THEN
        EXECUTE format('ALTER SEQUENCE tasks_id_seq RESTART WITH %s', max_id + 1);
    END IF;
    
    SELECT COALESCE(MAX(id), 0) INTO max_id FROM task_runs;
    IF max_id > 0 THEN
        EXECUTE format('ALTER SEQUENCE task_runs_id_seq RESTART WITH %s', max_id + 1);
    END IF;
END $$;

COMMIT;

-- 6. 验证迁移结果
SELECT 
    'Tasks Table' as table_name,
    COUNT(*) as row_count
FROM tasks
UNION ALL
SELECT 
    'Task Runs Table' as table_name,
    COUNT(*) as row_count
FROM task_runs
UNION ALL
SELECT 
    'Original Backup Table' as table_name,
    COUNT(*) as row_count
FROM tasks_backup
WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks_backup');

-- 显示迁移统计
SELECT 
    'Migration Summary' as info,
    jsonb_build_object(
        'total_tasks', (SELECT COUNT(*) FROM tasks),
        'total_runs', (SELECT COUNT(*) FROM task_runs),
        'unique_consumer_groups', (SELECT COUNT(DISTINCT consumer_group) FROM task_runs),
        'migration_time', now()
    ) as details;