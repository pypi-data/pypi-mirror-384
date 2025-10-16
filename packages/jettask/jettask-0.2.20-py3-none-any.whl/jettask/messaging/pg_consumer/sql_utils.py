"""SQL 文件处理工具"""
import re
from typing import List
import logging

logger = logging.getLogger(__name__)


def split_sql_statements(sql_content: str) -> List[str]:
    """
    智能分割 SQL 语句，正确处理 PL/pgSQL 函数定义
    
    Args:
        sql_content: SQL 文件内容
        
    Returns:
        分割后的 SQL 语句列表
    """
    statements = []
    current_statement = []
    in_function = False
    in_string = False
    in_dollar_quote = False
    dollar_quote_tag = None
    
    lines = sql_content.split('\n')
    
    for line in lines:
        # 跳过纯注释行
        stripped = line.strip()
        if stripped.startswith('--') and not current_statement:
            continue
            
        # 检测函数开始
        if not in_function and not in_string and not in_dollar_quote:
            # 检查是否是函数定义的开始
            if re.match(r'^\s*CREATE\s+(OR\s+REPLACE\s+)?FUNCTION', line, re.IGNORECASE):
                in_function = True
                logger.debug(f"进入函数定义: {line[:50]}")
        
        # 处理美元引号（$$）
        if not in_string:
            # 查找美元引号
            dollar_matches = re.findall(r'\$([^$]*)\$', line)
            for match in dollar_matches:
                if not in_dollar_quote:
                    # 开始美元引号
                    in_dollar_quote = True
                    dollar_quote_tag = match
                    logger.debug(f"进入美元引号: ${match}$")
                elif dollar_quote_tag == match:
                    # 结束美元引号
                    in_dollar_quote = False
                    dollar_quote_tag = None
                    logger.debug(f"退出美元引号: ${match}$")
        
        # 处理普通字符串（单引号）
        if not in_dollar_quote:
            # 简单的单引号检测（不处理转义）
            quote_count = line.count("'") - line.count("\\'")
            if quote_count % 2 == 1:
                in_string = not in_string
        
        current_statement.append(line)
        
        # 检查语句是否结束
        if stripped.endswith(';') and not in_string and not in_dollar_quote:
            # 对于函数，需要特殊处理
            if in_function:
                # 检查是否是函数结束（以 language 'xxx' 或 $$ language 结尾）
                if re.search(r"(language\s+['\"]?\w+['\"]?\s*;?\s*$|\$\$\s*language\s+['\"]?\w+['\"]?\s*;?\s*$)", 
                           stripped, re.IGNORECASE):
                    in_function = False
                    logger.debug(f"函数定义结束: {line[:50]}")
                    # 完整的函数定义
                    full_statement = '\n'.join(current_statement)
                    if full_statement.strip():
                        statements.append(full_statement)
                    current_statement = []
                # else: 仍在函数内部，继续累积
            else:
                # 普通语句结束
                full_statement = '\n'.join(current_statement)
                if full_statement.strip():
                    statements.append(full_statement)
                current_statement = []
    
    # 处理最后可能未完成的语句
    if current_statement:
        full_statement = '\n'.join(current_statement)
        if full_statement.strip():
            statements.append(full_statement)
    
    logger.info(f"SQL 文件分割完成，共 {len(statements)} 个语句")
    
    # 清理语句
    cleaned_statements = []
    for stmt in statements:
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            # 移除尾部多余的分号（保留一个）
            while stmt.endswith(';;'):
                stmt = stmt[:-1]
            cleaned_statements.append(stmt)
    
    return cleaned_statements


def execute_sql_file(connection, file_path: str):
    """
    执行 SQL 文件（同步版本）
    
    Args:
        connection: 数据库连接
        file_path: SQL 文件路径
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = split_sql_statements(sql_content)
    
    cursor = connection.cursor()
    try:
        for i, stmt in enumerate(statements, 1):
            try:
                logger.debug(f"执行第 {i}/{len(statements)} 个语句")
                cursor.execute(stmt)
            except Exception as e:
                if 'already exists' not in str(e):
                    logger.warning(f"语句 {i} 执行失败: {e}")
                    logger.debug(f"失败的语句: {stmt[:100]}...")
        connection.commit()
        logger.info(f"SQL 文件执行完成: {file_path}")
    except Exception as e:
        connection.rollback()
        logger.error(f"SQL 文件执行失败: {e}")
        raise
    finally:
        cursor.close()


async def execute_sql_file_async(async_session, file_path: str):
    """
    执行 SQL 文件（异步版本）
    
    Args:
        async_session: 异步数据库会话
        file_path: SQL 文件路径
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    statements = split_sql_statements(sql_content)
    
    # 为每个语句创建单独的事务，避免一个失败影响其他语句
    for i, stmt in enumerate(statements, 1):
        try:
            logger.debug(f"异步执行第 {i}/{len(statements)} 个语句")
            await async_session.execute(stmt)
            await async_session.commit()  # 立即提交每个成功的语句
        except Exception as e:
            # 静默处理一些预期的错误
            error_str = str(e)
            if any(x in error_str for x in [
                'already exists',
                'InFailedSqlTransaction',
                'DeadlockDetected',
                'duplicate key',
                'already exists'
            ]):
                logger.debug(f"语句 {i} 跳过（预期错误）: {type(e).__name__}")
            else:
                logger.warning(f"语句 {i} 执行失败: {e}")
                logger.debug(f"失败的语句: {stmt[:100]}...")
            
            # 始终尝试回滚失败的事务
            try:
                await async_session.rollback()
            except:
                pass
    
    logger.info(f"SQL 文件异步执行完成: {file_path}")