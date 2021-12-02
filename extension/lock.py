import redis

from ..util.lock import FileLock

lock_type = "file_lock"
lock_index = None
redis_client = None


def init_app(app):
    global redis_client, lock_type, lock_index

    lock_index = app.config.get("PRODUCT_KEY")

    if app.config.get("REDIS_URL"):
        redis_client = redis.from_url(app.config.get("REDIS_URL"))
        lock_type = "redis_lock"


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
