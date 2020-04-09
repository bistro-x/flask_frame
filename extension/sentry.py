# -*- coding:utf-8 -*-

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration


def init_app(flask_app):
    if flask_app.config.get("SENTRY_DS"):
        sentry_sdk.init(
            dsn=flask_app.config.get("SENTRY_DS", ""),
            integrations=[FlaskIntegration()]
        )
