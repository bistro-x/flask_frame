from flask import request, json
from werkzeug.exceptions import HTTPException
from flask_frame.annotation import deprecated


class ResourceError(HTTPException):
    """
    服务调用异常
    用于处理服务端调用错误，返回标准化的错误信息和错误码。
    """
    code = 500  # http代码
    error_code = 500  # 标准错误代码

    def __init__(self, description=None, response=None, error_code=None, code=None, data=None):
        super(ResourceError, self).__init__(description, response)
        self.code = code or self.code
        self.error_code = self.code
        
        # 如果有响应对象，尝试从响应中获取错误码和描述
        if response and response.json:
            self.error_code = response.json.get("error_code", self.error_code)
            self.pa = response.json.get("description", self.description)
        
        self.data = data  # 新增 data 参数

    def __str__(self):
        error_code = self.error_code if self.error_code is not None else "???"
        return "代码:%s, 信息%s" % (error_code, self.description)

    def get_body(self, environ=None, scope=None):
        # 构造返回体
        body = dict(message=self.description, code=self.error_code)
        if self.data is not None:
            body["data"] = self.data  # 如果有 data，添加到返回体
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None, scope=None):
        """返回响应头列表。"""
        return [("Content-Type", "application/json")]
    
class CallException(HTTPException):
    """
    第三方调用异常
    """

    code = 500
    msg = "调用异常"
    error_code = 1001

    def __init__(self, msg=None, error_code=None, code=None, **kwargs):
        if code:
            self.code = code
        if error_code:
            self.error_code = error_code
        if msg:
            self.msg = msg
        super(CallException, self).__init__(msg, None)

    def get_body(self, environ=None, scope=None):
        body = dict(msg=self.msg, error_code=self.error_code)
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None, scope=None):
        """Get a list of headers."""
        return [("Content-Type", "application/json")]

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

    def get_body(self, environ=None, scope=None):
        body = dict(
            msg=self.msg,
            error_code=self.error_code,
            request=request.method + " " + self.get_url_no_param(),
            traceback=self.traceback,
        )
        text = json.dumps(body)
        return text

    def get_headers(self, environ=None, scope=None):
        """Get a list of headers."""
        return [("Content-Type", "application/json")]

    @staticmethod
    def get_url_no_param():
        full_path = str(request.full_path)
        main_path = full_path.split("?")
        return main_path[0]
