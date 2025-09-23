# -*- coding: UTF-8 -*-
import json

import uuid
from datetime import date, datetime
from decimal import Decimal


# 自定义JSON编码器，支持datetime、date、UUID、Decimal类型的序列化
class AppEncoder(json.JSONEncoder):

    def default(self, obj):
        """
        重写default方法，处理特殊类型的序列化
        """
        if isinstance(obj, datetime):
            # 序列化datetime为字符串
            return obj.strftime("%Y-%m-%dT%H:%M:%S.%f")
        if isinstance(obj, date):
            # 序列化date为字符串
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, uuid.UUID):
            # 序列化UUID为字符串
            return str(obj)
        if isinstance(obj, Decimal):
            # 序列化Decimal为float
            return float(obj)
        # 其他类型使用默认序列化
        return json.JSONEncoder.default(self, obj)
