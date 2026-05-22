# -*- coding:utf-8 -*-
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_app(flask_app):
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
