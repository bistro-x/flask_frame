"""
分布式锁插件：优先使用 Redis 分布式锁，未配置 Redis 时自动降级为本地文件锁。
降级策略：lock 模块独立初始化 Redis 客户端（与 redis 插件解耦），避免循环依赖。
使用方式：get_lock(name, timeout) 根据当前锁类型自动返回对应的锁实例。
"""
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
    """初始化锁服务，配置 Redis 前缀和客户端。未配置 REDIS_URL 时使用文件锁。"""
    global redis_client, lock_type, lock_index

    lock_index = app.config.get("PRODUCT_KEY")+":lock"

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

        # 支持 Sentinel 高可用集群，URL 格式：sentinel://host:port;sentinel://host:port
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
    """锁工具类，提供文件锁和 Redis 锁的统一接口"""

    @staticmethod
    def get_file_lock(lock_name="FLASK_LOCK", timeout=600):

        return FileLock(lock_name, timeout)

    @staticmethod
    def get_redis_lock(lock_name, timeout=600):
        """获取 Redis 分布式锁，自动添加 PRODUCT_KEY 前缀避免冲突"""
        global redis_client, lock_index

        if lock_index:
            lock_name = f"{lock_index}:{lock_name}"

        return redis_client.lock(lock_name, timeout=timeout)


    @staticmethod
    def clear():
        """清除当前产品下所有锁（扫描并删除匹配 lock_index:* 的键）"""
        global lock_index

        cursor = 0  # 初始 cursor 值为整数 0
        while True:
            cursor, keys = redis_client.scan(cursor=cursor, match=f"{lock_index}:*")
            if keys:
                redis_client.delete(*keys)
            if cursor == 0:
                break

    @staticmethod
    def lock_type():
        global lock_type
        return lock_type


def get_lock(lock_name, timeout=600):
    """统一获取锁入口：根据 lock_type 自动选择 Redis 锁或文件锁"""
    global lock_type, redis_client

    if lock_type == "redis_lock":
        return Lock.get_redis_lock(lock_name, timeout)

    return Lock.get_file_lock(lock_name, timeout)
