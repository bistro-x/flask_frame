"""
自定义异常模块。
提供三种异常类型：
  - ResourceError: 服务调用异常，用于 HTTP 错误响应
  - CallException: 第三方调用异常
  - BusiError: 已废弃，请使用 ResourceError 替代

所有异常均继承 HTTPException，可直接被 Flask 的 errorhandler 捕获。
"""
from flask import request, json
from werkzeug.exceptions import HTTPException
from flask_frame.annotation import deprecated


class ResourceError(HTTPException):
    """
    服务调用异常，用于返回标准化的错误响应。
    
    Attributes:
        code: HTTP 状态码，默认 500。
        error_code: 业务错误码，默认与 HTTP 状态码相同。
        data: 附加数据（可选）。
    """

    code = 500
    error_code = 500

    def __init__(self, description=None, response=None, error_code=None, code=None, data=None):
        """
        初始化异常。
        
        Args:
            description: 错误描述信息。
            response: 原始响应对象（可从中提取 error_code）。
            error_code: 业务错误码（覆盖默认值）。
            code: HTTP 状态码（覆盖默认值）。
            data: 附加数据，会包含在响应体中。
        """
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
    第三方服务调用异常。
    
    Attributes:
        code: HTTP 状态码，默认 500。
        msg: 错误信息。
        error_code: 业务错误码，默认 1001。
    """

    code = 500
    msg = "调用异常"
    error_code = 1001

    def __init__(self, msg=None, error_code=None, code=None, **kwargs):
        """
        初始化异常。
        
        Args:
            msg: 错误信息。
            error_code: 业务错误码。
            code: HTTP 状态码。
            **kwargs: 其他参数。
        """
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
    """
    已废弃：业务异常类，请使用 ResourceError 替代。
    
    Attributes:
        code: HTTP 状态码，默认 500。
        msg: 错误信息。
        traceback: 堆栈追踪信息。
        error_code: 业务错误码，默认 1001。
    """

    code = 500
    msg = "this is message!"
    traceback = None
    error_code = 1001

    def __init__(self, msg=None, traceback=None, error_code=None, code=None, **kwargs):
        """
        初始化异常。
        
        Args:
            msg: 错误信息。
            traceback: 堆栈追踪。
            error_code: 业务错误码。
            code: HTTP 状态码。
            **kwargs: 其他参数。
        """
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
