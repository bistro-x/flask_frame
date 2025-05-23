from urllib.parse import urlparse

from sqlalchemy.exc import InvalidRequestError, OperationalError

from celery import Celery, Task
from celery.signals import task_prerun, worker_init
from celery.utils.log import get_task_logger

logger = get_task_logger("celery_info")

celery = None
flask_app = None



def init_app(app):
    """初始化模块

    Args:
        app (_type_): _description_
    """
    global celery, flask_app

    flask_app = app

    # redis 主从集群 master name
    broker_url = app.config.get("REDIS_URL")
    celery = Celery(
        app.import_name,
        backend=broker_url,
        broker=broker_url,
    )

    # redis sentinel 模式
    if broker_url.startswith("sentinel"):
        redis_master_name = app.config.get("REDIS_MASTER_NAME", None)
        redbeat_redis_url = broker_url
        redbeat_redis_options = {}

        password = None
        sentinels = []
        urls = broker_url.split(";")
        for url in urls:
            url = urlparse(url)
            password = url.password
            sentinels.append((url.hostname, url.port))
        redbeat_redis_options["sentinels"] = sentinels
        redbeat_redis_options["service_name"] = redis_master_name
        redbeat_redis_url = "redis-sentinel"
        if password:
            redbeat_redis_options["password"] = password

        # 增加定时任务
        celery.config_from_object(
            {
                "CELERY_TIMEZONE": "Asia/Shanghai",
                "ENABLE_UTC": True,
                "redbeat_key_prefix": app.config.get("CELERY_DEFAULT_QUEUE")
                or app.config.get("PRODUCT_KEY"),
                "redbeat_lock_timeout": app.config.get("REDBEAT_LOCK_TIMEOUT", 360),
                "redbeat_redis_url": redbeat_redis_url,
                "redbeat_redis_options": redbeat_redis_options,
                **app.config,
            }
        )

        celery.conf.broker_transport_options.update(master_name=redis_master_name)
        celery.conf.result_backend_transport_options = (
            celery.conf.broker_transport_options
        )
    else:
        # 增加定时任务
        celery.config_from_object(
            {
                "CELERY_TIMEZONE": "Asia/Shanghai",
                "ENABLE_UTC": True,
                **app.config,
            }
        )

    # 设置上下文
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask


class BaseTask(Task):
    """基础任务

    Args:
        Task (_type_): _description_
    """

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def on_success(self, retval, task_id, args, kwargs):
        from .database import db

        if db:
            db.session.commit()
            db.session.remove()

        return super(BaseTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from .database import db

        if isinstance(exc, OperationalError) or isinstance(exc, InvalidRequestError):
            db.session.remove()
            db.engine.dispose()
        else:
            db.session.rollback()

        return super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        from .database import db

        if isinstance(exc, OperationalError) or isinstance(exc, InvalidRequestError):
            db.session.remove()
            db.engine.dispose()
        else:
            db.session.rollback()

        return super(BaseTask, self).on_retry(exc, task_id, args, kwargs, einfo)
