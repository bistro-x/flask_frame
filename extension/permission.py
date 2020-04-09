from http import HTTPStatus

import requests
from authlib.integrations.flask_oauth2 import ResourceProtector
from authlib.oauth2.rfc6750 import BearerTokenValidator
from flask import request, abort, g

require_oauth = ResourceProtector()
app = None


def fetch_current_user(token_string):
    from authlib.integrations.flask_oauth2 import current_token
    if current_token and current_token.user:
        return current_token.user

    # get users
    user_auth_url = app.config.get("USER_AUTH_URL")
    if not user_auth_url:
        return True

    try:
        response = requests.get(
            url=user_auth_url + "/user/current",
            headers={
                "Authorization": "Bearer {token_string}".format(token_string=token_string),
            },
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
        return response.json()
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


def license_check():
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
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
        if not response.ok:
            abort(HTTPStatus.UNAUTHORIZED, response.json())

    except requests.exceptions.RequestException:
        print('HTTP Request failed')


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
    if user and any(
            permission.get(
                "url") == check_path and permission.get(
                "method") == method for permission in
            user.get("permissions")):
        return user


class _BearerTokenValidator(BearerTokenValidator):
    def authenticate_token(self, token_string):
        check_user_permission(token_string)


def config_oauth(app):
    # protect resource
    require_oauth.register_token_validator(_BearerTokenValidator())


def get_current_user():
    return g.current_user


def init_app(flask_app):
    global app
    app = flask_app

    @app.before_request
    def app_proxy():
        # check permission
        token_string = request.headers.environ.get('HTTP_AUTHORIZATION')
        token_string = token_string.split(" ")[1] if token_string else None
        if not check_user_permission(token_string):
            abort(HTTPStatus.METHOD_NOT_ALLOWED, {"message": "API未授权"})
