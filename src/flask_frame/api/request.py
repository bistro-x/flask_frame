# 当结果为result对象列表时，result有key()方法
from flask import request
import requests

from .response import Response


def get_request_param():
    """
    获取请求发送的所有参数，支持 JSON、表单、文件和 URL 参数。

    参数说明：
      无（从 flask.request 中读取当前请求）

    返回值：
      tuple: (params_dict, json_list_or_none)
        - params_dict (dict): 合并后的参数，优先包含 JSON(body) 内容（若存在且非列表），然后合并 form、files、query params。
        - json_list_or_none (list|None): 当请求体本身是一个 JSON 列表时返回该列表（用于批量场景），否则返回 None。

    说明：
      - 当请求体是一个 JSON 列表时，函数把 JSON 列表作为第二返回值，并把表单/文件/URL 参数作为第一个返回值。
      - 当请求体是普通 JSON 对象或无 JSON 时，返回合并后的参数字典，第二个返回值为 None。
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
    """代理请求到另一个服务

    参数说明：
      server_url (str): 目标服务的基础 URL（例如 "http://localhost:3000"），在转发时会与 path 拼接。
      response_standard (bool): 是否使用本服务的标准响应封装。
          - True: 返回统一的 Response.make_flask_response()（包含 code/message/data 等结构）。
          - False: 直接返回目标服务的原始 (text, status_code) 元组，便于简单透传。
      includ_schema_prefix (bool): 是否从请求路径中提取 schema 前缀并注入对应的 Profile 报头。
          - True: 从请求路径的第一个段提取 schema（例如 /schema/items -> schema）。
              * GET/HEAD 请求会把该 schema 放入 Accept-Profile。
              * 其他方法会把该 schema 放入 Content-Profile。
            同时转发时会把路径中的 schema 前缀去掉（/schema/items -> /items）。
          - False: 不做 schema 前缀提取或自动注入。

    返回值：
      Flask Response 或 tuple:
        - 若 response_standard=True：返回 Response.make_flask_response()（Flask Response 对象）。
        - 若 response_standard=False：返回 (response.text, response.status_code)。

    说明（中文）：
      - 函数会基于 incoming request 构建要转发的 headers（并可在 includ_schema_prefix 模式下注入 Accept-Profile/Content-Profile），
        将请求 body（json/data）与 query params 一并转发到目标服务。
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
    if includ_schema_prefix:
        # 规范化并分割路径；例如 "/schema/items/1" -> schema="schema", remaining="/items/1"
        raw_path = (request.path or "").lstrip("/")
        if raw_path:
            parts = raw_path.split("/", 1)
            schema = parts[0] if parts[0] else None
            remaining = "/" + parts[1] if len(parts) > 1 else "/"
            if schema:
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


def proxy_request(
    server_url=None, path="", method="GET", headers=None, params=None, **kwargs
):
    """创建代理请求

    参数说明：
      server_url (str): 目标服务基础 URL（例如 "http://localhost:3000"），不应为 None。
      path (str): 要转发的路径，建议以 '/' 开头（例如 '/items'）。
      method (str): HTTP 方法名称（'GET','POST' 等）。
      headers (dict 或 可迭代): 要发送的 HTTP 报头；若为非 dict（例如 headers 列表），函数会转换为 dict。
      params (dict): URL query 参数（可选）。
      **kwargs: 其他会直接传给 requests.request 的参数（例如 json, data, files 等）。

    返回值：
      requests.Response: requests 库返回的响应对象，调用方会根据需要进行标准化封装或直接透传。

    说明（中文）：
      - 函数会对传入的 headers 做一次拷贝以避免修改原对象（兼容 dict 或 iterable）。
      - 函数会删除 Authorization 报头（若存在），以避免泄露本地凭据或传递 None 字符串到目标服务。
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
