ma = None
from flask_marshmallow import Marshmallow


def init_app(flask_app):
    global ma
    ma = Marshmallow(flask_app)
