"""
数据模型 Schema 模块。
BaseSchema: 基础 Schema，自动剔除空值字段并包含未知字段。
DateTimeField: 支持 datetime 对象直接反序列化的时间字段。

注意：BaseSchema 在 pre_load 阶段会自动剔除 None、''、[]、{} 值的字段，
这意味着这些值不会参与校验和反序列化。如果需要保留空值，请直接使用 marshmallow.Schema。
"""
from flask_marshmallow import Schema
from marshmallow import INCLUDE, fields, pre_load, post_load
from datetime import datetime


class BaseSchema(Schema):
    """
    基础 Schema 类，所有业务 Schema 应继承此类。
    
    特性：
      - unknown=INCLUDE: 自动包含未声明的字段
      - pre_load 剔除空值: 在反序列化前自动移除值为 None、''、[]、{} 的字段
    """

    class Meta:
        unknown = INCLUDE

    @pre_load(pass_many=True)
    def remove_empty_fields(self, data, many, **kwargs):
        """
        剔除空值字段，避免空值覆盖数据库中的已有数据。
        
        Args:
            data: 输入数据（字典或字典列表）。
            many: 是否为批量模式。
            **kwargs: marshmallow 内部参数。
        
        Returns:
            dict 或 list: 清理后的数据。
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
    自定义 DateTime 字段，支持 datetime 对象直接传入而不需要先转换为字符串。
    常用于处理已从数据库读取的 datetime 值。
    """

    def _deserialize(self, value, attr, data, **kwargs):
        """
        反序列化 datetime 值。如果输入已经是 datetime 对象则直接返回。
        
        Args:
            value: 输入值（datetime 对象或字符串）。
            attr: 字段名。
            data: 整体数据。
            **kwargs: marshmallow 内部参数。
        
        Returns:
            datetime: 解析后的 datetime 对象。
        """
        if isinstance(value, datetime):
            return value
        return super()._deserialize(value, attr, data, **kwargs)
