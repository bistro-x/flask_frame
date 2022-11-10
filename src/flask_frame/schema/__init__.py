from flask_marshmallow import Schema
from marshmallow import INCLUDE, fields
from datetime import datetime


class BaseSchema(Schema):
    class Meta:
        unknown = INCLUDE


class DateTimeField(fields.DateTime):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data, **kwargs)
