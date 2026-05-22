# -*- coding:utf-8 -*-
"""
API 请求日志插件。
通过 after_request 钩子记录非 GET 请求的调用信息。
提供 Celery 定时任务 api_log_clean 清理过期日志。
"""
flask_app = None


def init_app(app):
    """
    初始化 API 日志记录，注册 after_request 钩子。
    
    Args:
        app: Flask 应用实例，需配置 DB_SCHEMA 和 API_LOG_RETENTION_DAYS。
    """
    global flask_app
    flask_app = app

    # 初始化模型
    from ..database import db, BaseModel, db_schema

    @app.after_request
    def after_request(response):
        from flask import request
        from .model import ApiLog

        # 查询方法不记录
        if request.method == "GET":
            return response

        from ..permission import get_current_user
        from sqlalchemy.sql import null

        # 创建
        user = get_current_user()

        api_log = ApiLog()
        api_log.user_id = user.get("id", null()) if user else null()
        api_log.client_id = user.get("client_id", null()) if user else null()

        api_log.remote_addr = request.remote_addr
        api_log.method = request.method
        api_log.path = request.path
        api_log.headers = dict(request.headers)
        api_log.args = dict(request.args)
        api_log.status = response.status_code
        db.session.merge(api_log)
        db.session.commit()

        return response

    _register_celery_task()


def _register_celery_task():
    """
    注册 API 日志清理定时任务（需 Celery 插件）。
    若 Celery 未启用则静默跳过。
    """
    try:
        from ..celery import celery
    except ImportError:
        return

    if not celery:
        return

    @celery.task(name="api_log_clean")
    def api_log_clean():
        """API日志清理"""
        from ..database import db
        from sqlalchemy import text

        api_log_retention_days = flask_app.config.get("API_LOG_RETENTION_DAYS", 30)
        schema = flask_app.config.get("DB_SCHEMA")

        db.session.execute(
            text(
                f"DELETE FROM {schema}.api_log "
                "WHERE create_time < now() - :days * interval '1 day'"
            ),
            {"days": api_log_retention_days},
        )
