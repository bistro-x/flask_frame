from flask_marshmallow import Schema
from marshmallow import INCLUDE, pre_load


class BaseSchema(Schema):
    class Meta:
        unknown = INCLUDE
