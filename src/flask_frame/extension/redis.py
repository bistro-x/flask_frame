import platform
import redis
from redis.sentinel import Sentinel
from urllib.parse import urlparse

redis_client = None


def init_app(app):
    """redis 客户端

    Args:
        app (_type_): _description_
    """
    global redis_client

    redis_cache_server_url = app.config.get("REDIS_URL")
    import socket

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

    if redis_cache_server_url.startswith("sentinel"):
        sentinel_options = {"service_name": redis_master_name}
        sentinels = []
        password = None
        urls = redis_cache_server_url.split(";")
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
    else:
        redis_client = redis.from_url(
            redis_cache_server_url,
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options,
        )
