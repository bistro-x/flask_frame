"""
响应封装模块。
提供统一的 API 响应结构：{result, code, message, data, create_time}。
Response.make_flask_response() 是标准的响应生成方法。
JsonResult 及相关函数已废弃，请使用 Response 类替代。
"""
import decimal
from datetime import date, time
from datetime import datetime as cdatetime
from http import HTTPStatus

import flask
from flask import jsonify
from flask_sqlalchemy.model import Model
from marshmallow import fields, post_dump, INCLUDE
from sqlalchemy import DateTime, Numeric, Date, Time

from flask_frame.util.db import result_to_dict

from ..annotation import deprecated
from ..schema import BaseSchema

SUCCESS_CODE = 100
ERROR_CODE = -1


class JsonResult:
    """已废弃：旧版响应封装类，请使用 Response 类替代。"""
    
    @deprecated
    def custom(code=None, msg=None, result=None):
        # 返回自定义结构的 JSON 响应
        return jsonify({"code": code, "msg": msg, "data": result})

    @deprecated
    def success(msg=None, result=False):
        """
        返回结果数据
        :param msg: 说明
        :param result: 数据
        :return:
        """
        if result:
            return jsonify(result)
        else:
            return jsonify({"message": msg}) if msg else jsonify(None)

    @deprecated
    def error(msg=None, result=None):
        # 返回错误结构的 JSON 响应
        return (
            jsonify({"code": ERROR_CODE, "message": msg, "data": result}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @deprecated
    def queryResult(result=None):
        # 查询结果转为字典并返回 JSON
        return jsonify(queryToDict(result))

    @deprecated
    def res_page(list, total):
        # 分页结果返回
        result = {"total": total, "list": queryToDict(list)}
        return jsonify(result)

    @deprecated
    def page(page):
        # 分页对象转为 JSON
        items = queryToDict(page.items)
        result = {"total": page.total, "list": items}
        return jsonify(result)


@deprecated
def queryToDict(models):
    """
    已废弃：将数据库查询结果转换为字典列表。请使用 util.db.result_to_dict 替代。
    
    Args:
        models: 查询结果（Model 对象、列表或 Row 类型）。
    
    Returns:
        dict 或 list: 转换后的字典或字典列表。
    """
    if isinstance(models, list):
        if len(models) == 0:
            return []
        if isinstance(models[0], Model):
            lst = []
            for model in models:
                gen = model_to_dict(model)
                dit = dict((g[0], g[1]) for g in gen)
                lst.append(dit)
            return lst
        else:
            res = result_to_dict(models)
            return res
    else:
        if models is None:
            return {}
        elif isinstance(models, Model):
            gen = model_to_dict(models)
            dit = dict((g[0], g[1]) for g in gen)
            return dit
        else:
            res = dict(zip(models.keys(), models))
            data_chg(res)
            return res


@deprecated
def model_to_dict(model):
    """
    已废弃：将 SQLAlchemy Model 对象转换为生成器（键值对）。
    
    Args:
        model: SQLAlchemy Model 实例。
    
    Yields:
        tuple: (列名, 值)，datetime 和 Decimal 类型已序列化。
    """
    for col in model.__table__.columns:
        if getattr(model, col.name) == None:
            value = None
        elif isinstance(col.type, DateTime):
            value = convert_datetime(getattr(model, col.name))
        elif isinstance(col.type, Numeric):
            value = float(getattr(model, col.name))
        elif isinstance(col.type, decimal.Decimal):
            value = float(getattr(model, col.name))
        else:
            value = getattr(model, col.name)
        yield (col.name, value)


@deprecated
def data_chg(value):
    for v in value:
        if isinstance(value[v], cdatetime):
            value[v] = convert_datetime(
                value[v]
            )  # 这里原理类似，修改的字典对象，不用返回即可修改
        elif isinstance(value[v], decimal.Decimal):
            value[v] = float(value[v])


@deprecated
def convert_datetime(value):
    if value:
        if isinstance(value, (cdatetime, DateTime)):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, (date, Date)):
            return value.strftime("%Y-%m-%d")
        elif isinstance(value, (Time, time)):
            return value.strftime("%H:%M:%S")
    else:
        return ""


class HttpResponseSchema(BaseSchema):
    """响应数据的 Schema 定义，用于序列化 Response 对象。"""

    data = fields.Raw()
    code = fields.Str(missing="0")
    provider_code = fields.Str()
    service_id = fields.Integer()
    message = fields.Str(missing="操作成功")
    detail = fields.Str()
    create_time = fields.DateTime()

    class Meta:
        unknown = INCLUDE

    def load_by_key(self, code=0, data=None, message=None, provider_code=None, create_time=None, **kwargs):
        """
        通过关键字参数构造响应数据。
        
        Args:
            code: 业务状态码。
            data: 响应数据。
            message: 提示信息。
            provider_code: 提供商标识。
            create_time: 创建时间。
            **kwargs: 其他扩展字段。
        
        Returns:
            dict: 加载后的数据字典。
        """
        return self.load(
            {
                code: code,
                data: data,
                message: message,
                provider_code: provider_code,
                create_time: create_time,
                **kwargs,
            }
        )

    @post_dump
    def remove_skip_values(self, data, many=None):
        return {key: value for key, value in data.items() if value is not None}


http_response_schema = HttpResponseSchema()


class Response(object):
    """
    标准 API 响应封装类。
    使用方式：Response(result=True, data={...}).make_flask_response()
    
    Attributes:
        result: 操作是否成功（True/False）。
        code: 业务状态码（成功默认 "0"）。
        message: 提示信息（成功时默认"操作成功"）。
        data: 响应数据（任意类型）。
        detail: 详细信息（通常用于错误详情）。
        http_status: HTTP 状态码（可选，失败时默认 500）。
        headers: 响应头字典（可选）。
        create_time: 响应生成时间（自动填充）。
    """

    def __init__(
        self,
        result=True,
        data=None,
        code=0,
        message=None,
        provider_code=None,
        task_id=None,
        response_time=None,
        service_id=None,
        headers=None,
        create_time=None,
        http_status=None,
        detail=None,
    ):
        """
        构造响应对象。
        
        Args:
            result: 操作是否成功。
            data: 响应数据。
            code: 业务状态码。
            message: 提示信息，为空时根据 result 自动填充。
            provider_code: 提供商业务码。
            task_id: 异步任务 ID。
            response_time: 响应耗时。
            service_id: 服务标识。
            headers: 响应头字典。
            create_time: 创建时间。
            http_status: HTTP 状态码。
            detail: 错误详情。
        """

        self.task_id = task_id  # 结果 True or False
        self.result = result  # 结果 True or False
        self.data = data  # 数据 json or string or Boolean
        self.code = code or "0"  # 统一编码 来自数据库 dict
        self.service = service_id
        self.provider_code = provider_code
        self.message = message or ("操作成功" if result else "操作失败")  # 说明信息
        self.response_time = response_time
        self.headers = headers
        self.http_status = http_status
        self.detail = detail
        self.create_time = create_time

    @deprecated
    def get_response(self):
        """
        使用上会有些问题，尽量使用 create_flask_response 来替代
        :return:
        """
        self.create_time = self.create_time or cdatetime.now()
        if self.result:
            return http_response_schema.dump(self)
        else:
            return http_response_schema.dump(self), (
                self.http_status or HTTPStatus.INTERNAL_SERVER_ERROR
            )

    def make_flask_response(self) -> flask.Response:
        """
        生成标准 Flask Response 对象。
        自动序列化 datetime 为北京时间字符串，Decimal 为 float。
        失败时 http_status 默认 500，成功时默认 200。
        
        Returns:
            flask.Response: 可直接返回给客户端的响应对象。
        """
        import json
        import pytz

        # 使用当前时间
        self.create_time = self.create_time or cdatetime.now()

        # 自定义JSON编码器处理时区问题
        class FlaskJSONEncoder(json.JSONEncoder):
            """
            自定义 JSON 编码器，用于处理 datetime、date、time 和 Decimal 对象的序列化。
            将 datetime 转换为北京时区格式，Decimal 转换为 float。
            """

            def default(self, obj):
                beijing_tz = pytz.timezone("Asia/Shanghai")

                if isinstance(obj, cdatetime):
                    # 处理 datetime 对象：转换为北京时区并格式化为字符串
                    if obj.tzinfo is None:
                        # 无时区信息，假设为UTC，转换为北京时间
                        obj = obj.replace(tzinfo=pytz.UTC).astimezone(beijing_tz)
                    else:
                        # 有时区信息，直接转换
                        obj = obj.astimezone(beijing_tz)
                    # 包含时区信息的时间格式 (例如: 2023-05-15 14:30:45+08:00)
                    return obj.strftime("%Y-%m-%d %H:%M:%S%z")
                elif isinstance(obj, date):
                    # 处理 date 对象：格式化为 YYYY-MM-DD
                    return obj.strftime("%Y-%m-%d")
                elif isinstance(obj, time):
                    # 处理 time 对象：格式化为 HH:MM:SS
                    return obj.strftime("%H:%M:%S")
                elif isinstance(obj, decimal.Decimal):
                    # 处理 Decimal 对象：转换为 float
                    return float(obj)

                return super().default(obj)

        # 使用自定义编码器序列化数据
        try:
            dumped_data = http_response_schema.dump(self)
            json_data = json.dumps(
                dumped_data, cls=FlaskJSONEncoder, ensure_ascii=False
            )
        except Exception as e:
            import logging

            logging.exception("序列化响应数据出错")
            # 返回错误信息，便于排查
            return flask.make_response(
                jsonify({"error": "响应序列化失败", "detail": str(e)}), 500
            )

        # 创建响应
        response = flask.make_response(
            json_data,
            self.http_status
            or (HTTPStatus.OK if self.result else HTTPStatus.INTERNAL_SERVER_ERROR),
        )

        # 设置正确的Content-Type
        response.headers["Content-Type"] = "application/json; charset=utf-8"

        # 定义报头
        response.headers = {**response.headers, **(self.headers or {})}

        # 返回
        return response

    @deprecated
    def mark_flask_response(self) -> flask.Response:
        return self.make_flask_response()

    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, dict):
            rv = jsonify(rv)
        return cls.make_flask_response()
