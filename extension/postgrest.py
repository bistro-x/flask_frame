import requests
from flask import request

flask_app = None
server_url = None


def proxy_request(method="GET", url="", headers=None, **kwargs):
    global flask_app, server_url
    response = requests.request(method=method, url=server_url + url, headers=headers, **kwargs)

    return response


def proxy_response(response):
    headers = {key: response.headers.get(key) for key in response.headers if
               key not in ['Transfer-Encoding', 'Content-Encoding', 'Content-Location']}
    return response.content, response.status_code, headers


def proxy():
    global flask_app, server_url

    # request.url_rule
    if not flask_app or request.url_rule:
        return

    # proxy
    headers = {h[0]: h[1] for h in request.headers}
    headers['Authorization'] = None
    other_param = {}
    if request.data:
        other_param["json"] = request.json

    response = proxy_request(request.method, request.full_path, headers=headers, **other_param)

    return proxy_response(response)


def init_app(app):
    global flask_app, server_url
    flask_app = app
    server_url = flask_app.config.get("PROXY_SERVER_URL")

    # get proxy config
    if not server_url:
        return

    @app.before_request
    def app_proxy():
        return proxy()
