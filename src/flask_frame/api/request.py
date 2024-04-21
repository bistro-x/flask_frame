# 当结果为result对象列表时，result有key()方法
from flask import request
import requests
from flask_frame.api.response import Response


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


def proxy(server_url, response_standard=True):
    """代理请求到另一个服务

    Args:
        server_url (string):  请求地址

    Returns:
        _type_: 响应
    """

    # 调用远程服务
    other_param = {}
    if request.is_json and request.data:
        other_param["json"] = request.get_json()
    elif request.data:
        other_param["data"] = request.data

    response = proxy_request(
        server_url,
        request.path,
        request.method,
        request.headers,
        request.args,
        **other_param,
    )

    if not response_standard:
        return (response.text, response.status_code)

    # 标准化
    if (
        "content-type" in response.headers
        and "json" in response.headers["content-type"]
    ):
        response_json = response.json()
    else:
        response_json = {}

    if response.headers.get("Transfer-Encoding"):
        response.headers.pop("Transfer-Encoding")

    return Response(
        result=response.ok,
        code=response_json.get("code") if not response.ok else 0,
        message=response_json.get("message") if not response.ok else None,
        detail=response_json.get("details") if not response.ok else None,
        data=response_json if response.ok else None,
        http_status=response.status_code,
        headers=response.headers,
    ).mark_flask_response()


def proxy_request(
    server_url=None, path="", method="GET", headers=None, params=None, **kwargs
):
    """创建代理请求

    Args:
        server_url (_type_, optional): _description_. Defaults to None.
        path (str, optional): _description_. Defaults to "".
        method (str, optional): _description_. Defaults to "GET".
        headers (_type_, optional): _description_. Defaults to None.
        params (_type_, optional): _description_. Defaults to None.

    Returns:
        Response: 响应
    """

    # 本地代理
    send_headers = {}
    if headers:
        send_headers = (
            {h[0]: h[1] for h in headers} if not isinstance(headers, dict) else headers
        )
        send_headers["Authorization"] = None

    return requests.request(
        method=method,
        url=server_url + path,
        params=params,
        headers=send_headers,
        timeout=30,  # Add a timeout argument (e.g., 10 seconds)
        **kwargs,
    )
