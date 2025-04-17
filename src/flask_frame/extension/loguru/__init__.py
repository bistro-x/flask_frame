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
            
        app.logger.info("Celery logging configured with Loguru")
        return True
    except Exception as e:
        app.logger.debug(f"Celery logging configuration skipped: {e}")
        return False
    
def _set_logger(app, config):
    # project
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

    path = config[k_log_name]
    if config[k_log_path] is not None:
        path = os.path.join(config[k_log_path], config[k_log_name])

    app.logger.setLevel(config[k_log_level] or "ERROR")

    logger.remove()
    logger.add(sys.stdout, format=config[k_log_format])

    logger.add(
        path,
        level=(config[k_log_level] or "ERROR"),
        format=config[k_log_format],
        enqueue=True,  # 确保设置为 True
        serialize=config[k_log_serialize],
        rotation=config[k_log_rotation],
        retention=config[k_log_retention],
        backtrace=True,  # 启用堆栈跟踪
        diagnose=True,   # 启用诊断信息
    )

    class InterceptHandler(logging.Handler):
        def emit(self, record):
            try:
                # 尝试获取对应的 Loguru 日志级别名称
                level = logger.level(record.levelname).name
            except ValueError:
                # 如果找不到对应的名称，则使用原始的数字级别
                level = record.levelno

            # 查找日志消息的原始调用位置
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            # 使用正确的调用深度和异常信息记录日志，保留原始调用者信息
            logger.opt(depth=depth, exception=record.exc_info).log(
                level, record.getMessage()
            )


    # 获取 gunicorn 的错误日志记录器，用于与 Flask 应用集成
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers

    # 移除所有现有的处理程序，防止重复日志
    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)
    # 创建拦截处理程序
    intercept_handler = InterceptHandler()
    
    # 添加自定义拦截处理程序，将 Flask 日志重定向到 Loguru
    app.logger.addHandler(intercept_handler)
    
    # 配置 Python 根日志记录器使用我们的拦截处理程序
    # 捕获所有模块的日志，level=0 表示捕获所有级别
    # force=True 确保覆盖任何现有配置
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 配置 Celery 日志拦截
    configure_celery_logging(app, intercept_handler)
    
def init_app(app):
    """初始化 Flask 应用的 Loguru 日志系统
    
    配置日志系统，设置适当的处理程序、格式和轮转策略
    
    Args:
        app: 需要配置日志的 Flask 应用实例
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
