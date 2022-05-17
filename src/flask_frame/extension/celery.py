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
    redis_master_name = app.config.get("REDIS_MASTER_NAME", None)
    redbeat_redis_url = broker_url
    redbeat_redis_options = {}

    # redis sentinel 模式
    if broker_url.startswith("sentinel"):
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

    celery = Celery(
        "tasks",
        backend=broker_url,
        broker=broker_url,
    )

    # 增加定时任务
    celery.config_from_object(
        {
            "CELERY_TIMEZONE": "Asia/Shanghai",
            "ENABLE_UTC": True,
            "redbeat_key_prefix": app.config.get("PRODUCT_KEY"),
            "redbeat_lock_timeout": app.config.get("REDBEAT_LOCK_TIMEOUT", 360),
            "redbeat_redis_url": redbeat_redis_url,
            "redbeat_redis_options": redbeat_redis_options,
            **app.config,
        }
    )

    celery.conf.broker_transport_options.update(master_name=redis_master_name)
    celery.conf.result_backend_transport_options = celery.conf.broker_transport_options


class BaseTask(Task):
    """基础任务

    Args:
        Task (_type_): _description_
    """

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def on_success(self, retval, task_id, args, kwargs):
        from .database import db
        from .database.model import Param

        Param.query.session.commit()
        if db:
            db.session.commit()
            db.session.remove()

        return super(BaseTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        from .database import db
        from .database.model import Param

        if isinstance(exc, OperationalError) or isinstance(exc, InvalidRequestError):
            db.session.remove()
            db.engine.dispose()
            Param.query.session.close()
        else:
            db.session.rollback()
            db.session.remove()

        return super(BaseTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@worker_init.connect
def before_worker_init(**kwargs):
    from .database import db
    from .database.model import Param

    with flask_app.app_context():
        db.engine.dispose()
        Param.query.session.close()


@task_prerun.connect
def before_task_start(**kwargs):
    from .database import db
    from .database.model import Param

    try:
        Param.query.session.execute("SELECT 1")
    except Exception as e:
        if isinstance(e, OperationalError) or isinstance(e, InvalidRequestError):
            logger.info("before task ping error")
            Param.query.session.close()
            db.session.remove()
            db.engine.dispose()
        else:
            logger.error(f"execute ping catch {str(e)}")
