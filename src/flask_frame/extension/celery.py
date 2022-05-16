import os
from urllib.parse import urlparse

from celery import Celery

celery = None
flask_app = None


def init_app(app):
    global celery
    global flask_app
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
