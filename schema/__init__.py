from marshmallow import Schema, INCLUDE


class BaseSchema(Schema):
    class Meta:
        unknown = INCLUDE
