import os
import time
import redis
import platform
from urllib.parse import urlparse

from redis.sentinel import Sentinel

from ..util.lock import FileLock

lock_type = "file_lock"
lock_index = None
redis_client = None


def init_app(app):
    global redis_client, lock_type, lock_index

    lock_index = app.config.get("PRODUCT_KEY")

    import socket

    if app.config.get("REDIS_URL"):

        redis_url = app.config.get("REDIS_URL")

        if platform.system() == "Linux":
            socket_keepalive_options = {
                socket.TCP_KEEPIDLE: 60,
                socket.TCP_KEEPINTVL: 30,
                socket.TCP_KEEPCNT: 3,
            }
        else:
            socket_keepalive_options = None

        # redis 主从集群 master name
        redis_master_name = app.config.get("REDIS_MASTER_NAME", None)

        if redis_url.startswith("sentinel"):
            sentinel_options = {"service_name": redis_master_name}
            sentinels = []
            password = None
            urls = redis_url.split(";")
            for url in urls:
                url = urlparse(url)
                password = url.password
                sentinels.append((url.hostname, url.port))
            if password:
                sentinel_options.update(password=password)
            redis_client = Sentinel(
                sentinels,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options=socket_keepalive_options,
            ).master_for(**sentinel_options)
            app.logger.info("using sentinel")
        else:
            redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_keepalive=True,
                socket_keepalive_options=socket_keepalive_options,
            )

        lock_type = "redis_lock"
        app.logger.info(f"process {os.getpid()} extension.lock use redis lock")


class Lock:
    @staticmethod
    def get_file_lock(lock_name="FLASK_LOCK", timeout=600):

        return FileLock(lock_name, timeout)

    @staticmethod
    def get_redis_lock(lock_name, timeout=600):
        global redis_client, lock_index

        if redis_client is None:
            return FileLock(lock_name, timeout)

        if lock_index:
            lock_name = f"{lock_index}.{lock_name}"

        return redis_client.lock(lock_name, timeout=timeout)

    @staticmethod
    def lock_type():
        global lock_type
        return lock_type


def get_lock(lock_name, timeout=600):
    global lock_type, redis_client

    if lock_type == "redis_lock":
        return Lock.get_redis_lock(lock_name, timeout)

    return Lock.get_file_lock(lock_name, timeout)
