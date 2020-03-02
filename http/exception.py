from flask import request, json
from werkzeug.exceptions import HTTPException


class PermissionError(HTTPException):
    code = 403
    pass


class BusiError(HTTPException):
    code = 500
    msg = "this is message!"
    traceback = None
    error_code = 1001

    def __init__(self, msg=None, traceback=None, error_code=None, code=None, ):
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
