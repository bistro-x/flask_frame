# -*- coding: utf-8 -*-
import logging
import os
import sys

from loguru import logger


def configure_celery_logging(app, intercept_handler):
    """配置 Celery 的日志拦截，将 Celery 日志重定向到 Loguru
    
    Args:
        app: Flask 应用实例，用于记录配置状态
        intercept_handler: 用于拦截日志的处理器实例
    
    Returns:
        bool: 配置成功返回True，失败返回False
    """
    try:
        # 配置 Celery 主日志记录器
        celery_logger = logging.getLogger('celery')
        celery_logger.handlers = []
        celery_logger.propagate = False
        celery_logger.addHandler(intercept_handler)
        
        # 配置 Celery 相关模块的日志记录器
        celery_related_loggers = ('celery.task', 'celery.worker', 'celery.app', 'celery.beat')
        for logger_name in celery_related_loggers:
            logger = logging.getLogger(logger_name)
            logger.handlers = []
            logger.propagate = False
            logger.addHandler(intercept_handler)
            
        app.logger.info("Celery 日志已配置使用 Loguru")
        return True
    except Exception as e:
        app.logger.debug(f"Celery 日志配置跳过: {e}")
        return False
    
def _set_logger(app, config):
    """设置日志记录器的具体配置
    
    Args:
        app: Flask应用实例
        config: 日志配置字典
    """
    # 导入项目相关模块
    from .compress import zip_logs
    from .macro import (
        k_log_path,
        k_log_name,
        k_log_enqueue,
        k_log_format,
        k_log_retention,
        k_log_rotation,
        k_log_serialize,
        k_log_level,
    )

    # 构建日志文件路径
    path = config[k_log_name]
    if config[k_log_path] is not None:
        path = os.path.join(config[k_log_path], config[k_log_name])

    # 获取日志级别并设置
    log_level = config[k_log_level] or "ERROR"
    app.logger.setLevel(log_level)

    # 移除所有现有日志处理器并添加新配置
    logger.remove()
    # 添加标准输出处理器
    logger.add(sys.stdout, format=config[k_log_format], level=log_level)

    # 添加文件日志处理器
    logger.add(
        path,
        level=log_level,
        format=config[k_log_format],
        enqueue=config[k_log_enqueue],
        serialize=config[k_log_serialize],
        rotation=config[k_log_rotation],
        retention=config[k_log_retention],
        backtrace=True,  # 启用堆栈跟踪，方便调试
        diagnose=True,   # 启用诊断信息，提供更详细的错误信息
    )

    class InterceptHandler(logging.Handler):
        """拦截标准日志库的日志并转发到Loguru
        
        将来自Python标准日志库的日志记录拦截并重定向到Loguru处理
        """
        def emit(self, record):
            """处理拦截的日志记录
            
            Args:
                record: 日志记录对象
            """
            from ..lock import Lock

            # 始终使用锁，因为这是用来替代队列模式的（enqueue会和gevent冲突）
            lock = Lock.get_file_lock("log_lock", timeout=10)
            
            try:
                # 获取锁以确保线程安全
                lock.acquire()

                # 获取对应的Loguru日志级别
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno

                # 查找日志消息的来源调用者
                frame, depth = logging.currentframe(), 2
                while frame and frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1

                # 使用Loguru记录日志，保留异常信息
                logger.opt(depth=depth, exception=record.exc_info).log(
                    level, record.getMessage()
                )
            finally:
                # 释放锁
                lock.release()

    # 获取gunicorn的错误日志记录器，与Flask应用集成
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers

    # 移除所有现有的处理程序，防止重复日志
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)
        
    # 创建拦截处理程序
    intercept_handler = InterceptHandler()
    
    # 添加自定义拦截处理程序，将Flask日志重定向到Loguru
    app.logger.addHandler(intercept_handler)
    
    # 配置Python根日志记录器使用拦截处理程序
    # force=True确保覆盖任何现有配置
    logging.basicConfig(handlers=[intercept_handler], level=log_level, force=True)

    # 配置Celery日志拦截
    configure_celery_logging(app, intercept_handler)
    
def init_app(app):
    """初始化Flask应用的Loguru日志系统
    
    配置日志系统，设置适当的处理程序、格式和轮转策略
    
    Args:
        app: 需要配置日志的Flask应用实例
    """
    # 导入项目特定模块
    from .compress import zip_logs
    from .macro import (
        k_log_path,
        k_log_name,
        k_log_enqueue,
        k_log_format,
        k_log_retention,
        k_log_rotation,
        k_log_serialize,
        k_log_level,
    )

    # 默认日志配置
    config = {"LOG_PATH": "./log", "LOG_NAME": "{time:YYYY-MM-DD}.log"}

    config.setdefault(k_log_level, "ERROR")
    config.setdefault(k_log_path, None)
    config.setdefault(k_log_name, "")
    config.setdefault(
        k_log_format,
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
        "| <level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> -"
        " <level>{message}</level>",
    )
    config.setdefault(k_log_enqueue, False)
    config.setdefault(k_log_serialize, False)
    config.setdefault(k_log_rotation, "00:00")
    config.setdefault(k_log_retention, "30 days")

    config.update(app.config)

    # 设置默认的日志路径
    _set_logger(app, config)
