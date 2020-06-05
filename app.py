import os
from http import HTTPStatus

import flask
from flask import Flask
from flask import request

from config import config
from frame.http.exception import BusiError


def create_app(flask_config_name="default", **kwargs):
    """
    create the app
    :param flask_config_name:
    :param kwargs:
    :return:
    """
    app = Flask(__name__, root_path=os.getcwd())

    # 初始化app
    config_name = os.getenv('FLASK_CONFIG', flask_config_name)
    app.config.from_object(config[config_name])

    # 加载配置文件
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

    from . import extension
    extension.init_app(app)

    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.error("url:%s,%s" % (request.base_url, error.description))

        return "url:%s,%s" % (request.base_url, error.description)

    # 全局异常处理
    @app.errorhandler(Exception)
    def exception_handle(error):
        app.logger.exception(error)
        if isinstance(error, BusiError):
            return error
        if isinstance(error, Resouc):

        elif hasattr(error, "description") and hasattr(error, "code"):
            return flask.jsonify(error.description), error.code
        else:
            return flask.jsonify({"message": error.message, "code": error.code}), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/', methods=['GET'])
    def index():
        return "app is running"

    @app.route('/debug-sentry')
    def trigger_error():
        division_by_zero = 1 / 0

    return app
