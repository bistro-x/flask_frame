from flask import request, json
from werkzeug.exceptions import HTTPException


class ResourceError(HTTPException):
    """
    服务调用异常
    """
    code = 500  # http代码
    error_code = 500  # 标准错误代码

    def __init__(self, description=None, response=None, error_code=None):
        super(ResourceError, self).__init__(description, response)
        self.error_code = error_code or self.error_code

        if response and response.json:
            self.error_code = response.json.get("error_code", self.error_code)
            self.pa = response.json.get("description", self.description)

    def __str__(self):
        error_code = self.error_code if self.error_code is not None else "???"
        return "代码:%s, 信息%s" % (error_code, self.description)

    def get_body(self, environ=None):
        body = dict(
            message=self.description,
            code=self.error_code
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]


class BusiError(HTTPException):
    """deprecated"""
    code = 500
    msg = "this is message!"
    traceback = None
    error_code = 1001

    def __init__(self, msg=None, traceback=None, error_code=None, code=None, **kwargs):
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        if msg:
            self.msg = msg
        if traceback:
            self.traceback = traceback
        super(BusiError, self).__init__(msg, None)

    def get_body(self, environ=None):
        body = dict(
            msg=self.msg,
            error_code=self.error_code,
            request=request.method + ' ' + self.get_url_no_param(),
            traceback=self.traceback
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [('Content-Type', 'application/json')]

    @staticmethod
    def get_url_no_param():
        full_path = str(request.full_path)
        main_path = full_path.split('?')
        return main_path[0]
