import decimal
from datetime import date, time
from datetime import datetime as cdatetime  # 有时候会返回datatime类型
from http import HTTPStatus

import flask
from flask import jsonify
from flask_sqlalchemy import Model
from marshmallow import fields, post_dump, INCLUDE
from sqlalchemy import DateTime, Numeric, Date, Time  # 有时又是DateTime

# 返回结果： 成功code=100； 失败：code=-1
from frame.annotation import deprecated
from frame.schema import BaseSchema

SUCCESS_CODE = 100
ERROR_CODE = -1


class JsonResult:
    @deprecated
    def custom(code=None, msg=None, result=None):
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
        return (
            jsonify({"code": ERROR_CODE, "message": msg, "data": result}),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    @deprecated
    def queryResult(result=None):
        return jsonify(queryToDict(result))

    @deprecated
    def res_page(list, total):
        result = {"total": total, "list": queryToDict(list)}
        return jsonify(result)

    @deprecated
    def page(page):
        items = queryToDict(page.items)
        result = {"total": page.total, "list": items}
        return jsonify(result)


@deprecated
def queryToDict(models):
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


# 当结果为result对象列表时，result有key()方法
@deprecated
def result_to_dict(results):
    res = [dict(zip(r.keys(), r)) for r in results]
    # 这里r为一个字典，对象传递直接改变字典属性
    for r in res:
        data_chg(r)
    return res


@deprecated
def model_to_dict(model):  # 这段来自于参考资源
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
            value[v] = convert_datetime(value[v])  # 这里原理类似，修改的字典对象，不用返回即可修改
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
    """错误格式"""

    data = fields.Raw()  # 数据 json or string or Boolean
    code = fields.Str(default="0")  # 统一编码 来自数据库 dict
    provider_code = fields.Str()
    service_id = fields.Integer()
    message = fields.Str(default="操作成功")  # 说明信息
    create_time = fields.DateTime(default=cdatetime.now())

    class Meta:
        unknown = INCLUDE

    def load_by_key(
        self, code=0, data=None, message=None, provider_code=None, create_time=None
    ):
        """构造函数"""
        return self.load(
            {
                code: code,
                data: data,
                message: message,
                provider_code: provider_code,
                create_time: create_time,
            }
        )

    @post_dump
    def remove_skip_values(self, data, many=None):
        return {key: value for key, value in data.items() if value is not None}


http_response_schema = HttpResponseSchema()


class Response(object):
    """返回对应"""

    def __init__(
        self,
        result=True,
        data=None,
        code=0,
        message="操作成功",
        provider_code=0,
        task_id=None,
        response_time=None,
        service_id=None,
        headers=None,
        create_time=None,
        http_status=None
    ):
        """
        构造函数
        :param result:
        :param data:
        :param code:
        :param message:
        :param service_id: 服务ID
        :param headers: 文件报头
        :param http_status: 指定返回http代码
        :param kwargs:
        """

        self.task_id = task_id  # 结果 True or False
        self.result = result  # 结果 True or False
        self.data = data  # 数据 json or string or Boolean
        self.code = code or "0"  # 统一编码 来自数据库 dict
        self.service = service_id
        self.provider_code = provider_code
        self.message = message  # 说明信息
        self.response_time = response_time
        self.headers = headers
        self.http_status = http_status
        
        if create_time:
            self.create_time = create_time

    @deprecated
    def get_response(self):
        """
        使用上会有些问题，尽量使用 create_flask_response 来替代
        :return:
        """
        if self.result:
            return http_response_schema.dump(self)
        else:
            return http_response_schema.dump(self), (self.http_status or HTTPStatus.INTERNAL_SERVER_ERROR)

    def mark_flask_response(self) -> flask.Response:
        """
        创建flask相关的返回对象
        :return:
        """
        if self.http_status == 204:
            response = flask.make_response('', 204) 
        else:
            response = flask.make_response(
                jsonify(http_response_schema.dump(self)),
                self.http_status or (HTTPStatus.OK if self.result else HTTPStatus.INTERNAL_SERVER_ERROR),
            )

        # 定义报头
        response.headers = {**response.headers, **(self.headers or {})}

        # 返回
        return response

    @classmethod
    def force_type(self, rv, environ=None):
        if isinstance(rv, dict):
            rv = jsonify(rv)
        return self.mark_flask_response()