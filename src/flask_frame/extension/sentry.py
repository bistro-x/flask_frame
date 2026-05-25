"""
Sentry 错误监控插件。
同时支持 SENTRY_DSN（推荐）和 SENTRY_DS（兼容旧版）两个配置键名。
会自动扫描所有 SENTRY_ 前缀的配置项作为初始化参数传入 sentry_sdk.init()。
"""
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

__all__ = ["init_app"]


def init_app(flask_app):
    """初始化 Sentry SDK，未配置 DSN 时静默跳过"""
    # 优先使用标准键名 SENTRY_DSN，兼容旧版 SENTRY_DS
    dsn = flask_app.config.get("SENTRY_DSN") or flask_app.config.get("SENTRY_DS")

    if not dsn:
        return

    _SENTRY_EXCLUDE_KEYS = ("SENTRY_DSN", "SENTRY_DS")

    other_param = {}
    for key, value in flask_app.config.items():
        if key.startswith("SENTRY_") and key not in _SENTRY_EXCLUDE_KEYS:
            other_param[key.replace("SENTRY_", "").lower()] = value

    sentry_logging = LoggingIntegration(
        level=flask_app.config.get("LOG_LEVEL") or logging.INFO,
        event_level=logging.ERROR,
    )

    sentry_sdk.init(
        dsn=dsn,
        integrations=[sentry_logging, FlaskIntegration()],
        **other_param
    )
