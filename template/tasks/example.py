"""
Celery 异步任务示例。
"""
from flask_frame.extension.celery import celery, BaseTask
from flask_frame.extension.database import db


@celery.task(base=BaseTask)
def process_file(file_path: str):
    """
    处理文件的异步任务。
    BaseTask 自动管理事务：成功 commit，失败 rollback。
    
    Args:
        file_path: 文件路径。
    
    Returns:
        str: 处理结果。
    """
    # 任务逻辑
    # 例如：解析文件、写入数据库等
    
    result = f"Processed: {file_path}"
    return result


@celery.task(base=BaseTask)
def cleanup_expired_data():
    """清理过期数据的定时任务"""
    # 执行清理逻辑
    # db.session.execute("DELETE FROM table WHERE expired_at < now()")
    
    return "Cleanup completed"