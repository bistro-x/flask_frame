import os
from http import HTTPStatus

import flask
from flask import Flask, g, make_response, send_file
from flask import request
from pyinstrument import Profiler

from .api.exception import BusiError, ResourceError
from .util.file import zip_path


def create_app(config, flask_config_name=None, config_custom=None, **kwargs):
    """
    create the app
    :param flask_config_name:
    :param config_custom
    :param kwargs:
    :return:
    """
    app = Flask(__name__, root_path=os.getcwd())

    # 初始化app
    config_name = (
        flask_config_name if flask_config_name else os.getenv("FLASK_CONFIG", "default")
    )
    app.config.from_object(config[config_name])
    if config_custom:
        app.config = {**app.config, **config_custom}

    # 加载配置文件
    os.environ["AUTHLIB_INSECURE_TRANSPORT"] = "1"

    from . import extension

    extension.init_app(app)

    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.error("url:%s,%s" % (request.base_url, error.description))

        return "url:%s,%s" % (request.base_url, error.description)

    @app.teardown_request
    def teardown(e):

        from .extension.database import db

        if db:
            db.session.commit()
            db.session.remove()

    # 全局异常处理
    @app.errorhandler(Exception)
    def exception_handle(error):
        from .extension.database import db

        db.session.rollback()
        app.logger.exception(error)

        if isinstance(error, BusiError):
            return error
        if isinstance(error, ResourceError):
            return error
        elif hasattr(error, "description") and hasattr(error, "code"):
            return flask.jsonify(error.description), error.code
        else:
            return (
                flask.jsonify(
                    {"message": str(error), "code": HTTPStatus.INTERNAL_SERVER_ERROR}
                ),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    @app.route("/", methods=["GET"])
    def index():
        return "app is running"

    @app.route("/debug-sentry")
    def trigger_error():
        division_by_zero = 1 / 0

    @app.route("/flask/log")
    def get_log_list():
        from flask import json

        def get_file(path):
            result = []
            for path, dir_list, file_list in os.walk("log"):
                for file_name in file_list:
                    result.append(os.path.join(path, file_name))
                for dir_name in dir_list:
                    result = result + get_file(os.path.join(path, dir_name))

            return result

        result = get_file("log")
        return json.dumps(result)

    @app.route("/flask/log/download", methods=["GET"])
    def get_zip_download():
        zip_file_path = "log.zip"
        zip_path("log", zip_file_path)
        return make_response(send_file(zip_file_path, as_attachment=True))

    @app.before_request
    def before_request():
        if "profile" in request.args:
            g.profiler = Profiler()
            g.profiler.start()

    @app.after_request
    def after_request(response):
        if "profile" not in request.args:
            return response
        g.profiler.stop()
        output_html = g.profiler.output_html()
        return make_response(output_html)

    return app


# remote debug
pycharm_ip = os.environ.get("PYCHARM_IP")
pycharm_port = os.environ.get("PYCHARM_PORT")
if pycharm_ip:
    import pydevd_pycharm

    pydevd_pycharm.settrace(
        pycharm_ip, port=int(pycharm_port), stdoutToServer=True, stderrToServer=True
    )
