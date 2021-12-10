import redis
import platform

from ..util.lock import FileLock

lock_type = "file_lock"
lock_index = None
redis_client = None


def init_app(app):
    global redis_client, lock_type, lock_index

    lock_index = app.config.get("PRODUCT_KEY")

    import socket

    if app.config.get("REDIS_URL"):

        if platform.system() == "Linux":
            socket_keepalive_options = {
                socket.TCP_KEEPIDLE: 60,
                socket.TCP_KEEPINTVL: 30,
                socket.TCP_KEEPCNT: 3,
            }
        else:
            socket_keepalive_options = None

        redis_client = RedisClient(
            app.config.get("REDIS_URL"),
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options,
        )

        lock_type = "redis_lock"
        app.logger.info("extension.lock use redis lock")


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

        return redis_client.client.lock(lock_name, timeout=timeout)

    @staticmethod
    def lock_type():
        global lock_type
        return lock_type


class RedisClient:

    def __init__(self, url, decode_responses=True, socket_keepalive=True, socket_keepalive_options=None, max_retry=5):
        self.url = url
        self.decode_responses = decode_responses
        self.socket_keepalive = socket_keepalive
        self.socket_keepalive_options = socket_keepalive_options
        self.max_retry = max_retry
        self._client = None
        self.init_client()

    def init_client(self):
        self._client = redis.Redis.from_url(
            self.url,
            decode_responses=self.decode_responses,
            socket_keepalive=self.socket_keepalive,
            socket_keepalive_options=self.socket_keepalive_options
        )

    @property
    def client(self):
        """
        每次调用前ping()检测链接, 异常重新初始化客户端
        """
        _client = None

        for _ in range(self.max_retry):
            try:
                self._client.ping()
                _client = self._client
            finally:
                if _client:
                    return _client
                else:
                    self.init_client()
                    time.sleep(0.1)

        return _client


def get_lock(lock_name, timeout=600):
    global lock_type, redis_client

    if lock_type == "redis_lock":
        return Lock.get_redis_lock(lock_name, timeout)

    return Lock.get_file_lock(lock_name, timeout)
