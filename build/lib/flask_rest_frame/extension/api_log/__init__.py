# -*- coding:utf-8 -*-
# flask api 的日志记录模块

flask_app = None
from extension.celery import celery


def init_app(app):
    global flask_app
    flask_app = app

    # 初始化模型
    from frame.extension.database import db, BaseModel, db_schema

    class ApiLog(db.Model, BaseModel):
        __tablename__ = "api_log"
        __table_args__ = {"extend_existing": True, "schema": db_schema}

    @app.after_request
    def after_request(response):
        from flask import request

        # 查询方法不记录
        if request.method == "GET":
            return response

        from frame.extension.permission import get_current_user
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


if celery:
    from extension.celery import BaseTask

    @celery.task(base=BaseTask, name="api_log_clean")
    def api_log_clean():
        """API日志清理"""
        from frame.extension.database import db

        api_log_retention_days = flask_app.config.get(
            "API_LOG_RETENTION_DAYS", 30
        )  # 日志保留时间
        db.session.execute(
            f"delete from z_know_info.api_log where create_time < (now() - interval '{api_log_retention_days} day');"
        )
