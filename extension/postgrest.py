import requests
from flask import request

flask_app = None
server_url = None


def proxy():
    global flask_app, server_url

    # request.url_rule
    if not flask_app or request.url_rule:
        return

    # get proxy config
    if not server_url and request.url_rule:
        return

    # proxy
    headers = {h[0]: h[1] for h in request.headers}
    headers['Authorization'] = None
    response = requests.request(request.method, server_url + request.path, data=request.json, headers=headers)

    headers = {key: response.headers.get(key) for key in response.headers if
               key not in ['Transfer-Encoding', 'Content-Encoding', 'Content-Location']}
    return response.content, response.status_code, headers


def init_app(app):
    global flask_app, server_url
    flask_app = app
    server_url = flask_app.config.get("PROXY_SERVER_URL")

    @app.before_request
    def app_proxy():
        return proxy()
