from typing import TYPE_CHECKING

from flask_marshmallow import Marshmallow

__all__ = ["ma", "init_app"]

if TYPE_CHECKING:
    ma: Marshmallow
else:
    ma = None


def init_app(flask_app):
    global ma
    ma = Marshmallow(flask_app)
