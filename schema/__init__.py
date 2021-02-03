from flask_marshmallow import Schema
from marshmallow import INCLUDE


class BaseSchema(Schema):
    class Meta:
        unknown = INCLUDE
