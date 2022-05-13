# 当结果为result对象列表时，result有key()方法
from flask import request


def get_request_param():
    """获取请求发送的所有参数

    Returns:
        json: 请求传入的所有参数
    """

    json_data = request.get_json(silent=True)

    if isinstance(json_data, list):
        return {
            **(request.form or {}),
            **request.files,
            **(request.args or {}),
        }, json_data
    else:
        return {
            **(json_data or {}),
            **(request.form or {}),
            **request.files,
            **(request.args or {}),
        }, None
