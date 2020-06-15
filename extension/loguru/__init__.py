# -*- coding: utf-8 -*-

# sys
import logging
import os

# 3p
from loguru import logger

# project
from .compress import zip_logs
from .macro import k_log_path, k_log_name, k_log_enqueue, k_log_format, k_log_retention
from .macro import k_log_rotation, k_log_serialize



def _set_logger(app, config):
    """ Config logru
    """
    path = config[k_log_name]
    if config[k_log_path] is not None:
        path = os.path.join(config[k_log_path], config[k_log_name])

    logger.add(path, format=config[k_log_format],
               enqueue=config[k_log_enqueue], serialize=config[k_log_serialize],
               rotation=config[k_log_rotation],
               retention=config[k_log_retention])

    class InterceptHandler(logging.Handler):
        def emit(self, record):
            if hasattr(record, "levelno") and record.levelno >= 40:
                logger.exception(record.getMessage())
            else:
                logger.log(record.levelname, record.getMessage())



    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers

    for handler in list(app.logger.handlers):
        app.logger.removeHandler(handler)

    app.logger.addHandler(InterceptHandler())


def init_app(app):
    """This is used to initialize logger with your app object
    """
    config = {
        "LOG_PATH": "./log",
        "LOG_NAME": "{time:YYYY-MM-DD}.log"
    }

    config.update(app.config)

    config.setdefault(k_log_path, None)
    config.setdefault(k_log_name, "")
    config.setdefault(k_log_format, "")
    config.setdefault(k_log_enqueue, True)
    config.setdefault(k_log_serialize, False)
    config.setdefault(k_log_rotation, "12:00")
    config.setdefault(k_log_retention, "30 days")

    _set_logger(app, config)
