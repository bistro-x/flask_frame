"""
请求参数提取和代理转发模块。
get_request_param(): 统一合并 JSON、form、files、URL 参数。
proxy(): 代理请求到远程服务，支持 PostgREST 风格的 schema 前缀。
"""
from flask import request
import requests

from .response import Response


def get_request_param():
    """
    提取当前请求的所有参数，合并为一个字典。
    
    支持的参数来源（按优先级合并）：
      - JSON body（如果存在且不是列表）
      - form data
      - files
      - URL query 参数
    
    特殊处理：当 JSON body 是列表时（批量请求场景），返回 (参数字典, 列表) 元组。
    
    Returns:
        tuple: (合并后的参数字典, JSON 列表或 None)。
            当请求体是 JSON 列表时，第二个元素为该列表，否则为 None。
    """
    json_data = request.get_json(silent=True)

    if isinstance(json_data, list):
        # 如果请求体是列表，返回所有表单、文件和 URL 参数
        return {
            **(request.form or {}),
            **request.files,
            **(request.args or {}),
        }, json_data
    else:
        # 否则合并所有参数
        return {
            **(json_data or {}),
            **(request.form or {}),
            **request.files,
            **(request.args or {}),
        }, None


def proxy(server_url, response_standard=True, includ_schema_prefix=False):
    """
    代理当前请求到远程服务（如 PostgREST）。
    
    Args:
        server_url: 目标服务基础 URL，如 "http://postgrest:3000"。
        response_standard: 是否使用 Response 标准封装。True 返回 Flask Response，
            False 返回 (text, status_code) 元组用于透传。
        includ_schema_prefix: 是否从 URL 提取 schema 前缀（第一个路径段）。
            提取后会从转发路径中去掉，并设置 Accept-Profile 或 Content-Profile 头。
    
    Returns:
        flask.Response 或 tuple: 根据 response_standard 返回不同格式。
    """

    # 调用远程服务
    other_param = {}
    if request.is_json and request.data:
        other_param["json"] = request.get_json()
    elif request.data:
        other_param["data"] = request.data

    # 构建要发送的 headers（基于 incoming request）
    # 将 request.headers 转为普通 dict，便于修改和传递给 proxy_request
    send_headers = {k: v for k, v in request.headers.items()}

    # 计算要转发的 path（默认使用原始 request.path）
    proxied_path = request.path or ""

    # 若要求包含 schema/profile 前缀，则从 request.path 中提取 schema（第一个 path 段）
    # 并将其放入 Accept-Profile / Content-Profile，同时将 proxied_path 去掉该前缀
    if includ_schema_prefix or "/" in (request.path or "").lstrip("/"):
        # 规范化并分割路径；例如 "/schema/items/1" -> schema="schema", remaining="/items/1"
        raw_path = (request.path or "").lstrip("/")
        if raw_path:
            parts = raw_path.split("/", 1)
            schema = parts[0] if parts[0] else None
            
            if schema and len(parts) > 1:
                remaining = "/" + parts[1] if len(parts) > 1 else "/"
                method = (request.method or "GET").upper()
                if method in ("GET", "HEAD"):
                    # 对于查询类请求，使用 Accept-Profile 指定 schema/tenant
                    send_headers["Accept-Profile"] = schema
                else:
                    # 对于写入类请求，使用 Content-Profile 指定 schema/tenant
                    send_headers["Content-Profile"] = schema
                # 更新要转发的 path（去掉 schema 前缀）
                proxied_path = remaining
        else:
            # 无路径可提取时保持原样
            proxied_path = request.path or "/"

    response = proxy_request(
        server_url,
        proxied_path,
        request.method,
        send_headers,
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

    # 删除 preference-applied 和 content-length 报头（不区分大小写）
    for key in list(response.headers.keys()):
        if key.lower() in ("content-length"):
            response.headers.pop(key)

    return Response(
        result=response.ok,
        code=response_json.get("code") if not response.ok else 0,
        message=response_json.get("message") if not response.ok else None,
        detail=response_json.get("details") if not response.ok else None,
        data=response_json if response.ok else None,
        http_status=response.status_code,
        headers=response.headers,
    ).make_flask_response()


def proxy_request(server_url=None, path="", method="GET", headers=None, params=None, **kwargs):
    """
    发送代理请求到指定服务。自动移除 Authorization 头以避免泄露凭据。
    
    Args:
        server_url: 目标服务基础 URL。
        path: 要转发的路径，如 /items。
        method: HTTP 方法。
        headers: 请求头（dict 或可迭代键值对），会被拷贝后修改。
        params: URL 查询参数字典。
        **kwargs: 直接传给 requests.request 的参数（如 json, data, files）。
    
    Returns:
        requests.Response: 原始响应对象。
    """
    # 本地代理
    send_headers = {}
    if headers:
        # 确保使用 headers 的拷贝，且兼容 headers 是 list/tuple 或 dict 的情况
        send_headers = (
            dict(headers)
            if isinstance(headers, dict)
            else {h[0]: h[1] for h in headers}
        )
        # 删除 Authorization，避免将 None 作为字符串发送
        send_headers.pop("Authorization", None)

    return requests.request(
        method=method,
        url=server_url + path,
        params=params,
        headers=send_headers,
        timeout=30,  # Add a timeout argument (e.g., 10 seconds)
        **kwargs,
    )
