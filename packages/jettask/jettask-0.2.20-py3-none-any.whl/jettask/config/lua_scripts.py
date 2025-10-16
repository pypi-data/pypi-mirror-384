"""
Redis Lua 脚本定义

集中管理所有的 Redis Lua 脚本，用于原子操作和性能优化
"""

# Lua脚本：批量处理延迟任务
# 用于批量添加延迟任务到Redis Stream和ZSET
LUA_SCRIPT_DELAYED_TASKS = """
local prefix = ARGV[1]
local current_time = tonumber(ARGV[2])
local results = {}

-- 从ARGV[3]开始，每5个参数为一组任务信息
-- [stream_key, stream_data, execute_at, delay_seconds, queue]
for i = 3, #ARGV, 5 do
    local stream_key = ARGV[i]
    local stream_data = ARGV[i+1]
    local execute_at = tonumber(ARGV[i+2])
    local delay_seconds = tonumber(ARGV[i+3])
    local queue = ARGV[i+4]

    -- 使用Hash存储所有队列的offset
    local offsets_hash = prefix .. ':QUEUE_OFFSETS'
    -- 使用HINCRBY原子递增offset
    local offset = redis.call('HINCRBY', offsets_hash, queue, 1)

    -- 1. 添加消息到Stream（包含offset字段）
    local stream_id = redis.call('XADD', stream_key, '*',
        'data', stream_data,
        'offset', offset)

    -- 2. 添加到延迟队列ZSET
    local delayed_queue_key = prefix .. ':DELAYED_QUEUE:' .. queue
    redis.call('ZADD', delayed_queue_key, execute_at, stream_id)

    -- 3. 保存 stream_key 到共享Hash（所有延迟任务共享一个Hash）
    local stream_key_hash = prefix .. ':TASK:STREAM_KEY'
    redis.call('HSET', stream_key_hash, stream_id, stream_key)

    -- 保存stream_id到结果
    table.insert(results, stream_id)
end

return results
"""

# Lua脚本：批量处理普通任务
# 用于批量添加普通任务到Redis Stream
LUA_SCRIPT_NORMAL_TASKS = """
local prefix = ARGV[1]
local current_time = ARGV[2]
local results = {}

-- 从ARGV[3]开始，每2个参数为一组任务信息
-- [stream_key, stream_data]
for i = 3, #ARGV, 2 do
    local stream_key = ARGV[i]
    local stream_data = ARGV[i+1]

    -- 从stream_key中提取队列名（格式: prefix:STREAM:queue_name）
    local queue_name = string.match(stream_key, prefix .. ':STREAM:(.*)')

    -- 获取并递增offset
    local offset_key = prefix .. ':STREAM:' .. queue_name .. ':next_offset'
    local offset = redis.call('INCR', offset_key)

    -- 1. 添加消息到Stream（包含offset字段）
    local stream_id = redis.call('XADD', stream_key, '*',
        'data', stream_data,
        'offset', offset)

    -- 2. 设置任务状态Hash（只存储status）
    local task_key = prefix .. ':TASK:' .. stream_id
    redis.call('HSET', task_key, 'status', 'pending')

    -- 3. 设置过期时间（1小时）
    redis.call('EXPIRE', task_key, 3600)

    -- 保存stream_id到结果
    table.insert(results, stream_id)
end

return results
"""

# Lua脚本：原子获取并删除结果
# 用于获取任务结果后立即删除，避免多次读取
LUA_SCRIPT_GET_AND_DELETE = """
local key = KEYS[1]
local value = redis.call('GET', key)
if value then
    redis.call('DEL', key)
end
return value
"""

# Lua脚本：批量发送任务（简化版，已被LUA_SCRIPT_NORMAL_TASKS替代）
# 保留用于兼容性
LUA_SCRIPT_BATCH_SEND = """
local stream_key = KEYS[1]
local task_name = ARGV[1]
local count = 0

for i = 2, #ARGV do
    redis.call('XADD', stream_key, '*', 'task_name', task_name, 'message', ARGV[i])
    count = count + 1
end

return count
"""

# Lua脚本：发送延迟任务（_send_delayed_tasks方法专用）
# 用于异步发送单个队列的延迟任务
LUA_SCRIPT_SEND_DELAYED_TASKS = """
local prefix = ARGV[1]
local results = {}

-- 从ARGV[2]开始，每3个参数为一组任务信息
-- [stream_key, stream_data, execute_at]
-- 延迟队列key直接从stream_key推导，保持队列名一致（包括优先级）
for i = 2, #ARGV, 3 do
    local stream_key = ARGV[i]
    local stream_data = ARGV[i+1]
    local execute_at = tonumber(ARGV[i+2])

    -- 使用Hash存储所有队列的offset
    local offsets_hash = prefix .. ':QUEUE_OFFSETS'

    -- 从stream_key中提取完整队列名（包含优先级）
    local full_queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

    -- 使用HINCRBY原子递增offset
    local current_offset = redis.call('HINCRBY', offsets_hash, full_queue_name, 1)

    -- 1. 添加消息到Stream（包含offset字段）
    local stream_id = redis.call('XADD', stream_key, '*',
        'data', stream_data,
        'offset', current_offset)

    -- 2. 添加到延迟队列ZSET（延迟队列名和Stream名完全对应）
    local delayed_queue_key = prefix .. ':DELAYED_QUEUE:' .. full_queue_name
    redis.call('ZADD', delayed_queue_key, execute_at, stream_id)

    -- 保存stream_id到结果
    table.insert(results, stream_id)
end

return results
"""

__all__ = [
    'LUA_SCRIPT_DELAYED_TASKS',
    'LUA_SCRIPT_NORMAL_TASKS',
    'LUA_SCRIPT_GET_AND_DELETE',
    'LUA_SCRIPT_BATCH_SEND',
    'LUA_SCRIPT_SEND_DELAYED_TASKS',
]
