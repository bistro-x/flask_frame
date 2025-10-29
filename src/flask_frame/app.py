import os
from http import HTTPStatus
import flask
from flask import Flask, g, make_response, send_file
from flask import request
from pyinstrument import Profiler

from .api.exception import BusiError, ResourceError
from .util.file import zip_path
from .util.json import AppEncoder


def create_app(config, flask_config_name=None, config_custom=None, **kwargs):
    """
    创建并初始化 Flask 应用实例。

    :param config: 配置字典，包含所有环境的配置。
    :param flask_config_name: 选用的配置名称，默认为 "default"。
    :param config_custom: 额外的自定义配置。
    :param kwargs: 其他可选参数。
    :return: Flask 应用实例。
    """
    # 创建 Flask 应用实例
    app = Flask(__name__, root_path=os.getcwd())  # root_path 指定应用根目录
    app.json_encoder = AppEncoder  # 设置自定义的 JSON 编码器

    # 加载配置
    config_name = flask_config_name or os.getenv("FLASK_CONFIG", "default")
    app.config.from_object(config[config_name])  # 从配置字典中加载环境配置
    if config_custom:
        app.config.update(config_custom)  # 加载额外的自定义配置
    app.config.FLASK_CONFIG = config_name

    # 配置环境变量，允许不安全的传输（用于开发环境）
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

    # 导入并初始化扩展
    from . import extension

    extension.init_app(app)

    # 404 错误处理
    @app.errorhandler(404)
    def page_not_found(error):
        """
        处理 404 错误，记录错误信息。
        """
        app.logger.error("url:%s,%s" % (request.base_url, error.description))
        return f"url:{request.base_url},{error.description}"

    # 请求结束后，进行事务处理
    @app.teardown_request
    def teardown(e):
        """
        请求结束后进行事务提交和资源清理。
        """
        from .extension.database import db

        if db:
            if not e:  # 如果没有异常，提交事务
                db.session.commit()
            db.session.remove()  # 清理数据库会话

    # 全局异常处理
    @app.errorhandler(Exception)
    def exception_handle(error):
        """
        处理所有未捕获的异常，进行日志记录，并根据不同异常类型返回不同的响应。
        """
        from .extension.database import db

        if db:
            db.session.rollback()  # 回滚事务

        app.logger.exception(error)  # 记录异常信息

        # 处理自定义异常
        if isinstance(error, BusiError):
            return error
        if isinstance(error, ResourceError):
            return error

        # 如果是标准异常，返回异常描述和状态码
        elif hasattr(error, "description") and hasattr(error, "code"):
            return (
                flask.jsonify({"message": error.description, "code": error.code}),
                error.code,
            )
        else:
            return (
                flask.jsonify(
                    {
                        "message": f"{type(error).__name__}: {str(error)}",
                        "code": HTTPStatus.INTERNAL_SERVER_ERROR,
                    }
                ),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    # 首页路由，测试应用是否正常运行
    @app.route("/", methods=["GET"])
    def index():
        return "app is running"

    # 健康检查路由，返回服务状态
    @app.route("/healthy", methods=["GET"])
    def healthy():
        return flask.jsonify({"status": "healthy"}), 200

    # 手动触发错误路由，用于调试 Sentry
    @app.route("/debug-sentry")
    def trigger_error():
        """
        触发除零错误，用于调试 Sentry。
        """
        division_by_zero = 1 / 0

    # 获取日志文件列表
    @app.route("/flask/log")
    def get_log_list():
        """
        返回日志目录下的所有文件路径。
        """
        from flask import json

        def get_file(path):
            result = []
            # 遍历目录，获取所有文件路径
            for path, dir_list, file_list in os.walk("log"):
                for file_name in file_list:
                    result.append(os.path.join(path, file_name))
                for dir_name in dir_list:
                    result = result + get_file(os.path.join(path, dir_name))
            return result

        result = get_file("log")
        return json.dumps(result)  # 返回 JSON 格式的文件列表

    # 下载日志文件，打包为 ZIP 文件
    @app.route("/flask/log/download", methods=["GET"])
    def get_zip_download():
        """
        将日志文件夹压缩成 ZIP 文件并提供下载。
        """
        zip_file_path = "log.zip"
        zip_path("log", zip_file_path)  # 压缩日志文件夹
        return make_response(
            send_file(zip_file_path, as_attachment=True)
        )  # 返回压缩包文件

    # 在请求处理前启动性能分析
    @app.before_request
    def before_request():
        """
        在请求处理前，如果 URL 参数中包含 'profile'，则启动性能分析。
        """
        if "profile" in request.args:
            g.profiler = Profiler()
            g.profiler.start()

    # 在请求处理后停止性能分析，并返回分析报告
    @app.after_request
    def after_request(response):
        """
        请求处理后停止性能分析，并返回性能分析报告。
        """
        if "profile" not in request.args:
            return response  # 如果没有性能分析请求，直接返回响应
        g.profiler.stop()  # 停止性能分析
        output_html = g.profiler.output_html()  # 获取分析报告的 HTML 格式
        return make_response(output_html)  # 返回性能分析报告

    return app
