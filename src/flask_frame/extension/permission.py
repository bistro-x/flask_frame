from http import HTTPStatus
import os

import flask
import requests
from flask import request, abort, g

app = None

# 配置参数
fetch_user = True  # 是否获取用户
check_api = True  # 检查API权限


def init_app(flask_app):
    """初始化 extension

    Args:
        flask_app (_type_): _description_
    """
    global app, check_api, fetch_user, get_user_extend_info

    app = flask_app
    check_api = app.config.get("CHECK_API", True)
    admin_token = app.config.get(
        "ADMIN_TOKEN", os.getenv("ADMIN_TOKEN")
    )  # 固定可跳过校验的 TOKEN

    fetch_user = app.config.get("FETCH_USER", True)

    @app.before_request
    def app_proxy():
        # 获取 token
        token_string = request.headers.environ.get("HTTP_AUTHORIZATION")
        token_string = token_string.split(" ")[1] if token_string and len(token_string.split(" ")) >1  else None

        # 全局 TOKEN 校验
        if admin_token and token_string == admin_token:
            return

        # 检测权限和用户
        if fetch_user and not check_user_permission(token_string):
            if check_api:
                if not get_current_user():
                    abort(HTTPStatus.UNAUTHORIZED, {"message": "无法获取用户"})
                else:
                    abort(HTTPStatus.FORBIDDEN, {"message": "API未授权"})


def fetch_current_user(token_string,params={}):
    """
    查询当前用户
    :param token_string:
    :return:
    """
    global app

    # get users
    user_auth_url = app.config.get("USER_AUTH_URL")
    if not user_auth_url:
        return None

    try:
        if not token_string:
            return None

        response = requests.get(
            url=user_auth_url + "/auth/current",
            params=params,
            headers={
                "Authorization": "Bearer {token_string}".format(
                    token_string=token_string
                ),
            },
        )
        
        # 检查请求是否成功
        if not response.ok:
            app.logger.error(f"获取用户信息失败: {response.status_code} - {response.text}")
            g.current_user = None
            return g.current_user
            
        # 获取用户设置到全局中
        g.current_user = response.json().get("data",None)
        return g.current_user
    except requests.exceptions.RequestException as e:
        app.logger.exception(e)


def get_current_user():
    """获取当前用户"""
    if not flask.has_request_context():
        return None

    if hasattr(g, "current_user"):
        return g.current_user

    return None


def license_check():
    """检测 license

    Returns:
        _type_: _description_
    """
    global app

    user_auth_url = app.config.get("USER_AUTH_URL")
    if not user_auth_url or app.config.get("LICENSE_CHECK") is False:
        return True
    try:
        response = requests.get(
            url=user_auth_url + "/license/check",
            params={"product_key": app.config.get("PRODUCT_KEY")},
        )
        if not response.ok:
            abort(HTTPStatus.UNAUTHORIZED, response.json())

    except requests.exceptions.RequestException as e:
        app.logger.exception(e)


def check_user_permission(token_string=None):
    """
    权限检测
    :param token_string: token信息
    :return: 用户信息
    """

    # 请求方法

    # 权限验证
    user = fetch_current_user(token_string)
    return check_url_permission(user)


def check_url_permission(user, product_key=None):
    """检测是否有相关接口权限


    Args:
        user (_type_): 检测用户
    Returns:
        _type_: 是否通过
    """
    global check_api
    
    # 无需检测权限
    if not check_api:
        return True
    
    # 没有用户信息直接返回
    check_path = request.url_rule.rule if request.url_rule else request.path
    method = request.method

    # 静态文件不进行限制
    if check_path and check_path.startswith("/static/"):
        return True

    if not user:
        return False

    # 超级用户不需要检测权限
    if user and user.get("name") == "admin":
        return True

    # 客户端校验
    if user and user.get("client_id") and not user.get("id"):
        return True

    # 权限库没有定义的接口，就不进行限制。
    product_key = product_key or app.config.get("PRODUCT_KEY")
    if (
        user
        and user.get("no_permissions")
        and any(
            product_key == permission.get("product_key")
            and permission.get("url") == check_path
            and permission.get("method") == method
            for permission in user.get("no_permissions")
        )
    ):
        return False

    # 默认true
    return True


def param_add_department_filter(params={}):
    """
    添加组织权限过滤
    :param params: 当前参数
    :return: 过滤参数
    """
    user = g.current_user

    depart_list = []
    for item in user.get("department_key") or []:
        depart_list.append(f"department_key.like.{item}*")

    if len(depart_list) > 0:
        depart_str = ",".join(depart_list)
        params["or"] = f"(department_key.is.null,{depart_str})"
    else:
        params["department_key"] = "is.null"

    return params
