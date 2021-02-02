import os
from http import HTTPStatus

import flask
from flask import Flask
from flask import request

from config import config
from frame.http.exception import BusiError, ResourceError


def create_app(flask_config_name=None, config_custom=None, **kwargs):
    """
    create the app
    :param flask_config_name:
    :param config_custom
    :param kwargs:
    :return:
    """
    app = Flask(__name__, root_path=os.getcwd())

    # 初始化app
    config_name = flask_config_name if flask_config_name else os.getenv('FLASK_CONFIG', "default")
    app.config.from_object(config[config_name])
    if config_custom:
        app.config = {**app.config, **config_custom}

    # 加载配置文件
    os.environ['AUTHLIB_INSECURE_TRANSPORT'] = '1'

    from . import extension
    extension.init_app(app)

    @app.errorhandler(404)
    def page_not_found(error):
        app.logger.error("url:%s,%s" % (request.base_url, error.description))

        return "url:%s,%s" % (request.base_url, error.description)

    @app.teardown_request
    def teardown(e):

        from frame.extension.database import db
        if db:
            if e:
                db.session.rollback()
            else:
                db.session.commit()
            db.session.remove()

    # 全局异常处理
    @app.errorhandler(Exception)
    def exception_handle(error):
        app.logger.exception(error)
        if isinstance(error, BusiError):
            return error
        if isinstance(error, ResourceError):
            return error
        elif hasattr(error, "description") and hasattr(error, "code"):
            return flask.jsonify(error.description), error.code
        else:
            return flask.jsonify(
                {"message": str(error), "code": HTTPStatus.INTERNAL_SERVER_ERROR}), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/', methods=['GET'])
    def index():
        return "app is running"

    @app.route('/debug-sentry')
    def trigger_error():
        division_by_zero = 1 / 0

    return app


# remote debug
pycharm_ip = os.environ.get('PYCHARM_IP')
pycharm_port = os.environ.get('PYCHARM_PORT')
if pycharm_ip:
    import pydevd_pycharm

    pydevd_pycharm.settrace(pycharm_ip, port=int(pycharm_port), stdoutToServer=True, stderrToServer=True)
