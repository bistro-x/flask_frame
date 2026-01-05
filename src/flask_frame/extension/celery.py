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
        app (_type_): Flask应用实例
    """
    global celery, flask_app

    flask_app = app

    # 获取Redis URL作为broker
    broker_url = app.config.get("REDIS_URL")
    celery = Celery(
        app.import_name,
        backend=broker_url,
        broker=broker_url,
    )

    # 如果broker URL以sentinel开头，使用Redis Sentinel模式
    if broker_url.startswith("sentinel"):
        redis_master_name = app.config.get("REDIS_MASTER_NAME", None)
        redbeat_redis_url = broker_url
        redbeat_redis_options = {}

        password = None
        sentinels = []
        # 解析sentinel URL，提取主机、端口和密码
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

        # 配置定时任务，使用redbeat
        celery.config_from_object(
            {
                "timezone": "Asia/Shanghai",  # 时区设置为亚洲上海
                "enable_utc": True,  # 启用UTC时间
                "redbeat_key_prefix": app.config.get(
                    "CELERY_DEFAULT_QUEUE"
                )  # redbeat键前缀，使用默认队列或产品键
                or app.config.get("PRODUCT_KEY"),  # 产品键
                "redbeat_lock_timeout": app.config.get(
                    "REDBEAT_LOCK_TIMEOUT", 360
                ),  # redbeat锁超时时间，默认360秒
                "redbeat_redis_url": redbeat_redis_url,  # redbeat Redis URL
                "redbeat_redis_options": redbeat_redis_options,  # redbeat Redis选项
                **app.config,  # 展开应用配置
            }
        )

        # 设置broker传输选项
        celery.conf.broker_transport_options.update(master_name=redis_master_name)
        celery.conf.result_backend_transport_options = (
            celery.conf.broker_transport_options
        )
    else:
        # 如果配置是大写 需要增加前缀 CELERY_
        # 非sentinel模式，配置定时任务
        celery.config_from_object(
            {
                "timezone": "Asia/Shanghai",  # 时区设置为亚洲上海
                "enable_utc": True,  # 启用UTC时间
                **app.config,  # 展开应用配置
            }
        )

    # 定义上下文任务类，确保在Flask应用上下文中运行
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    # 将Celery的Task基类替换为上下文任务类
    celery.Task = ContextTask


class BaseTask(Task):
    """基础任务类

    Args:
        Task (_type_): Celery Task基类
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
