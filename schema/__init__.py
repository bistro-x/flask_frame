from flask_marshmallow import Schema
from marshmallow import INCLUDE, pre_load


class BaseSchema(Schema):
    class Meta:
        unknown = INCLUDE

    @pre_load()
    def strip_string(self, data, **kwargs):
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = value.strip() if isinstance(value, str) else value
        return data