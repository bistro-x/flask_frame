"""
Flask RESTful 框架库。
提供开箱即用的 REST API 开发能力，包括：
  - 应用工厂（create_app）
  - 统一响应封装（Response）
  - 请求参数提取（get_request_param）
  - 数据库 ORM（flask_frame.extension.database）
  - Redis 客户端（flask_frame.extension.redis）
  - 分布式锁（flask_frame.extension.lock）
  - 文件存储（flask_frame.extension.minio）
  - 权限校验（flask_frame.extension.permission）
  - 异步任务（flask_frame.extension.celery）
  - 服务发现（flask_frame.extension.consul）
  - PostgREST 代理（flask_frame.extension.postgrest）
  - 日志系统（flask_frame.extension.loguru）

使用示例：
    from flask_frame import create_app, Response, FlaskFrameConfig
    from flask_frame.extension.database import db, run_sql
    
    app = create_app({"PRODUCT_KEY": "my_service", ...})
    
    @app.route("/api/example")
    def example():
        return Response(data={"msg": "hello"}).make_flask_response()
"""
from .app import create_app
from .api.response import Response
from .api.request import get_request_param, proxy_request
from .api.exception import ResourceError, CallException, BusiError
from .schema import BaseSchema, DateTimeField
from .annotation import deprecated, profile
from .config import FlaskFrameConfig
from .openapi import generate_openapi, sync_to_apifox

__all__ = [
    "create_app",
    "Response",
    "get_request_param",
    "proxy_request",
    "ResourceError",
    "CallException",
    "BusiError",
    "BaseSchema",
    "DateTimeField",
    "deprecated",
    "profile",
    "FlaskFrameConfig",
    "generate_openapi",
    "sync_to_apifox",
]
