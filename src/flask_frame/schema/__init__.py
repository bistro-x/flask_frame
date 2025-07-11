from flask_marshmallow import Schema
from marshmallow import INCLUDE, fields, pre_load, post_load
from datetime import datetime


class BaseSchema(Schema):
    """
    基础Schema，支持未知字段自动包含，并在反序列化前剔除值为空的字段。
    """
    class Meta:
        unknown = INCLUDE

    @pre_load(pass_many=True)
    def remove_empty_fields(self, data, many, **kwargs):
        """
        剔除值为 None、''、[]、{} 的字段（在校验前处理）
        """
        def clean(d):
            if isinstance(d, dict):
                return {k: v for k, v in d.items() if v not in (None, '', [], {})}
            return d

        if many and isinstance(data, list):
            return [clean(item) for item in data]
        return clean(data)


class DateTimeField(fields.DateTime):
    """
    支持 datetime 类型直接反序列化的自定义时间字段
    """
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data, **kwargs)


# flask_marshmallow（或 marshmallow）不会自动剔除值为 None、''、[]、{} 的参数。
# 它只会忽略未声明的字段（unknown=INCLUDE），但不会过滤字段值为空的情况。
# 如需自动剔除空值字段，需自定义 post_load 或在视图层手动过滤。
# 你当前的 post_load(remove_empty_fields) 实现就是为此目的。
