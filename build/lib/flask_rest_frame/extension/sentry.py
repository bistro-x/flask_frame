# -*- coding:utf-8 -*-
import logging
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration


def init_app(flask_app):
    if flask_app.config.get("SENTRY_DS"):

        # All of this is already happening by default!
        sentry_logging = LoggingIntegration(
            level=flask_app.config.get("LOG_LEVEL")
            or logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=flask_app.config.get("SENTRY_DS", ""),
            integrations=[sentry_logging, FlaskIntegration()],
        )
