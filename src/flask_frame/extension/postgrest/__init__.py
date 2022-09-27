import requests
from flask import request
from ...api.response import Response

flask_app = None
server_url = None
proxy_local = None


def proxy_request(method="GET", url="", headers=None, params=None, **kwargs):
    """
    创建代理请求
    :param method:
    :param url:
    :param headers:
    :param kwargs:
    :return:
    """
    global flask_app, server_url

    # 本地代理
    if proxy_local:
        data, headers = local_run(
            method=method, url=url, params=params, headers=headers, **kwargs
        )
        return Response(data=data, headers=headers)

    send_headers = {}
    if headers:
        send_headers = (
            {h[0]: h[1] for h in headers} if not isinstance(headers, dict) else headers
        )
        send_headers["Authorization"] = None

    response = requests.request(
        method=method,
        url=server_url + url,
        params=params,
        headers=send_headers,
        **kwargs,
    )

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
    )


def proxy_response(response):
    """转换代理回应

    Args:
        response (_type_): _description_

    Returns:
        _type_: _description_
    """

    headers = {
        key: response.headers.get(key)
        for key in response.headers
        if key not in ["Transfer-Encoding", "Content-Encoding", "Content-Location"]
    }

    return response.content, response.status_code, headers

def is_send_proxy():
    """是否发送请求到代理服务

    Returns:
        boolean: 判断结果 
    """
    global flask_app, server_url
    
    # request.url_rule
    if not flask_app or (request.url_rule and not request.headers.get("proxy")):
        return False
    
    return True


def proxy():
    """
    发送代理请求
    :return: 返回
    """
    global flask_app, server_url

    # request.url_rule
    if not is_send_proxy():
        return

    # 调用远程服务
    other_param = {}
    if request.data:
        other_param["json"] = request.json

    response = proxy_request(
        request.method, request.path, request.headers, request.args, **other_param
    )
    
    return response.mark_flask_response()


def local_run(
    schema=None, method="GET", url="", headers=None, params=None, data=[], **kwargs
):
    """本地运行数据库操作

    Returns:
        _type_: data, headers
    """
    global flask_app

    from .sql_generator import generate_sql
    from ...extension.database import db

    # 调用本地转换
    exec_sql, count_sql = generate_sql(
        method or request.method,
        url or request.path,
        params or request.args,
        data or request.get_json(silent=True),
        headers or request.headers,
    )

    schema = schema or flask_app.config.get("PRODUCT_KEY")
    first_sql = f"set search_path to {schema};"

    # 执行语句
    data = None
    headers = {}
    if isinstance(exec_sql, list):
        for item_sql in exec_sql:
            if "returning" in item_sql:
                item = db.session.execute(first_sql + item_sql).fetchone()
                data = data or []
                item and data.append(dict(item))
            else:
                db.session.execute(first_sql + item_sql)
    elif "select" in exec_sql:
        if "application/vnd.pgrst.object+json" in request.headers.get("Accept"):
            query_result = db.session.execute(first_sql + exec_sql).fetchone()
            data = dict(query_result)
        else:
            query_result = db.session.execute(first_sql + exec_sql).fetchall()
            count_result = db.session.execute(first_sql + count_sql).fetchone()

            if query_result is not None:
                data = [dict(row) for row in query_result]
            else:
                data = []

            if count_result is not None:
                count_result = count_result[0]
                index_begin = int(request.args.get("offset", "0"))
                index_end = (
                    min(
                        index_begin + int(request.args.get("limit", "99999999")),
                        count_result,
                    )
                    - 1
                )
                headers[
                    "Content-Range"
                ] = f"{str(index_begin)}-{str(index_end)}/{count_result}"
    else:
        if "returning" in exec_sql:
            query_result = db.session.execute(first_sql + exec_sql).fetchall()
            data = [dict(row) for row in query_result]
        else:
            db.session.execute(first_sql + exec_sql)

    return data, headers


def init_app(app):
    global flask_app, server_url, proxy_local
    flask_app = app
    server_url = flask_app.config.get("PROXY_SERVER_URL")
    proxy_local = flask_app.config.get("PROXY_LOCAL", False)  # 本地代理
    proxy_custom = flask_app.config.get("PROXY_CUSTOM", False)  # 个性化代理

    # get proxy config
    if proxy_custom:
        return

    @app.before_request
    def app_proxy():
        return proxy()
