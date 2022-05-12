from http import HTTPStatus

import flask
import requests
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6750 import BearerTokenValidator
from flask import request, abort, g

require_oauth = ResourceProtector()
app = None

# 配置参数
check_api = True  # 检查API权限
fetch_user = True  # 是否获取用户


def fetch_current_user(token_string):
    """
    todo 使用缓存
    获取当前用户
    :param token_string:
    :return:
    """
    global app

    from authlib.integrations.flask_oauth2 import current_token
    user_auth_local = app.config.get("USER_AUTH_LOCAL")

    if current_token and current_token.user and user_auth_local:
        from module.user.service import get_user_extend_info
        return get_user_extend_info(current_token.user)

    # get users
    user_auth_url = app.config.get("USER_AUTH_URL")
    if not user_auth_url:
        return None

    try:
        if not token_string:
            return None

        response = requests.get(
            url=user_auth_url + "/user/current",
            headers={
                "Authorization": "Bearer {token_string}".format(token_string=token_string),
            },
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        app.logger.exception(e)


def license_check():
    """证书检测
    """
    global app

    user_auth_url = app.config.get("USER_AUTH_URL")
    if not user_auth_url or app.config.get("LICENSE_CHECK") is False:
        return True
    try:
        response = requests.get(
            url=user_auth_url + "/license/check",
            params={
                "product_key": app.config.get("PRODUCT_KEY")
            }
        )
        if not response.ok:
            abort(HTTPStatus.UNAUTHORIZED, response.json())

    except requests.exceptions.RequestException as e:
        app.logger.exception(e)


def config_oauth(app):
    # protect resource
    require_oauth.register_token_validator(_BearerTokenValidator())


def check_user_permission(token_string=None):
    """
    check current token
    :param token_string:
    :return:
    """
    method = request.method

    user_auth_local = app.config.get("USER_AUTH_LOCAL")

    if user_auth_local and request.url_rule:
        return True

    if user_auth_local:
        from module.auth.extension.oauth2 import require_oauth

        @require_oauth('profile')
        def local_oauth():
            pass

        local_oauth()

    # get current user
    if not user_auth_local:

        # get users
        user_auth_url = app.config.get("USER_AUTH_URL")
        if not user_auth_url:
            return {}

        # 证书校验
        license_check()

    # 权限验证
    response = fetch_current_user(token_string)
    user = response if response else None

    # 超级用户
    g.current_user = user
    if user and user.get("name") == "admin":
        return user

    check_path = request.url_rule.rule if request.url_rule else request.path
    if user and check_api and user.get("permissions") and any(
            permission.get(
                "url") == check_path and permission.get(
                "method") == method for permission in
            user.get("permissions")):
        return user
    elif check_path and check_path.startswith("/static/"):
        return True

    return user


class _BearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        check_user_permission(token_string)


def get_current_user():
    """获取当前用户"""
    if not flask.has_request_context():
        return None

    if hasattr(g, 'current_user'):
        return g.current_user

    return None


def param_add_department_filter(params={}):
    """
    添加组织权限过滤
    :param params: 当前参数
    :return:
    """
    user = g.current_user

    depart_list = []
    for item in user.get('department_key') or []:
        depart_list.append(f'department_key.like.{item}*')

    if len(depart_list) > 0:
        depart_str = ",".join(depart_list)
        params["or"] = f"(department_key.is.null,{depart_str})"
    else:
        params["department_key"] = f"is.null"

    return params


def init_app(flask_app):
    global app, check_api, fetch_user

    app = flask_app
    check_api = app.config.get("CHECK_API", True)
    fetch_user = app.config.get("FETCH_USER", True)

    @app.before_request
    def app_proxy():
        # check permission
        token_string = request.headers.environ.get('HTTP_AUTHORIZATION')
        token_string = token_string.split(" ")[1] if token_string else None
        if fetch_user and not check_user_permission(token_string):
            if check_api:
                abort(HTTPStatus.UNAUTHORIZED, {"message": "API未授权"})
