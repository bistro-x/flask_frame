# -*- coding: utf-8 -*-
import logging
import os

from loguru import logger


def _set_logger(app, config):
    # project
    from .compress import zip_logs
    from .macro import (
        k_log_path, k_log_name, k_log_enqueue, k_log_format,
        k_log_retention, k_log_rotation, k_log_serialize, k_log_level
    )

    path = config[k_log_name]
    if config[k_log_path] is not None:
        path = os.path.join(config[k_log_path], config[k_log_name])

    app.logger.setLevel(config[k_log_level] or "ERROR")

    logger.add(path,
               format=config[k_log_format],
               enqueue=config[k_log_enqueue],
               serialize=config[k_log_serialize],
               rotation=config[k_log_rotation],
               retention=config[k_log_retention])

    class InterceptHandler(logging.Handler):

        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers

    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)

    app.logger.addHandler(InterceptHandler())


def init_app(app):
    # project
    from .compress import zip_logs
    from .macro import (
        k_log_path, k_log_name, k_log_enqueue, k_log_format,
        k_log_retention, k_log_rotation, k_log_serialize
    )

    config = {
        "LOG_PATH": "./log",
        "LOG_NAME": "{time:YYYY-MM-DD}.log"
    }

    config.update(app.config)

    config.setdefault(k_log_path, None)
    config.setdefault(k_log_name, "")
    config.setdefault(k_log_format, "{time} {level} {message}")
    config.setdefault(k_log_enqueue, True)
    config.setdefault(k_log_serialize, False)
    config.setdefault(k_log_rotation, "12:00")
    config.setdefault(k_log_retention, "30 days")

    _set_logger(app, config)
