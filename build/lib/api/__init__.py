from contextlib import closing

import requests
from flask import request, Response
from urllib.parse import urljoin


def proxy(server_url):
    """
    代理请求发送到别的服务i
    :param server_url:
    :return:
    """
    method = request.method
    data = request.data or request.form or None
    headers = dict()
    for name, value in request.headers:
        if not value or name in ['Cache-Control']:
            continue
        headers[name] = value

    with closing(
            requests.request(method, urljoin(server_url, request.full_path), headers=headers, data=data,
                             files=request.files,
                             stream=True)
    ) as r:
        resp_headers = []
        for name, value in r.headers.items():
            if name.lower() in ('content-length', 'connection',
                                'content-encoding'):
                continue
            resp_headers.append((name, value))
        return Response(r, status=r.status_code, headers=resp_headers)
