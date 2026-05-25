"""
权限校验插件。
通过 before_request 钩子在每次请求前执行鉴权流程：
  1. 从 Authorization 头获取 token
  2. 检查是否为 ADMIN_TOKEN（跳过校验）
  3. 调用用户认证服务获取用户信息（依赖 USER_AUTH_URL 配置）
  4. 校验用户是否有当前接口的访问权限

权限判定规则（按优先级）：
  - CHECK_API=False 时跳过所有权限校验
  - 静态文件（/static/）不校验
  - admin 用户拥有全部权限
  - 客户端模式（有 client_id 无 id）通过
  - 在 no_permissions 列表中的接口拒绝访问
  - 其余情况默认允许
"""
from http import HTTPStatus
import os
from typing import Any, TYPE_CHECKING

import flask
import requests
from flask import request, abort, g

__all__ = [
    "init_app",
    "fetch_current_user",
    "get_current_user",
    "license_check",
    "check_user_permission",
    "check_url_permission",
    "param_add_department_filter",
]

if TYPE_CHECKING:
    from flask import Flask
    app: Flask
else:
    app = None

fetch_user: bool = True
check_api: bool = True


def init_app(flask_app: "Flask") -> None:
    """初始化权限校验，注册 before_request 钩子"""
    global app, check_api, fetch_user

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


def fetch_current_user(token_string: str | None, params: dict[str, Any] = {}) -> dict[str, Any] | None:
    """
    调用用户认证服务获取当前用户信息，结果缓存到 g.current_user。
    依赖 USER_AUTH_URL 配置指向用户认证服务地址。
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


def get_current_user() -> dict[str, Any] | None:
    """从请求上下文获取当前用户（由 fetch_current_user 缓存在 g 中）"""
    if not flask.has_request_context():
        return None

    if hasattr(g, "current_user"):
        return g.current_user

    return None


def license_check() -> bool:
    """调用用户认证服务检查 License 是否有效"""
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


def check_user_permission(token_string: str | None = None) -> bool:
    """
    权限检测
    :param token_string: token信息
    :return: 用户信息
    """

    # 请求方法

    # 权限验证
    user = fetch_current_user(token_string)
    return check_url_permission(user)


def check_url_permission(user: dict[str, Any] | None, product_key: str | None = None) -> bool:
    """
    校验用户是否有当前请求路径的访问权限。
    权限白名单：admin 用户、客户端模式、静态文件路径。
    权限黑名单：no_permissions 列表中精确匹配的接口会被拒绝。
    未在黑名单中的接口默认允许访问。
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


def param_add_department_filter(params: dict[str, Any] = {}) -> dict[str, Any]:
    """
    为查询参数添加组织权限过滤条件。
    根据当前用户的 department_key 列表生成 PostgREST 风格的 like 过滤条件。
    无部门信息时过滤 department_key 为 null 的记录。
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
