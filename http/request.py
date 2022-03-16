# 当结果为result对象列表时，result有key()方法
from flask import request

def get_request_param():
    """获取请求发送的所有参数

    Returns:
        json: 请求传入的所有参数
    """
    return {**(request.args or {}),**(request.form or {}), **(request.json or {}), **request.files}