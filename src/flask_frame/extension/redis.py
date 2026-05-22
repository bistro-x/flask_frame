"""
Redis 客户端插件。
支持两种部署模式：
  - 单机模式：REDIS_URL 格式为 redis://host:port
  - Sentinel 高可用模式：REDIS_URL 格式为 sentinel://host:port;sentinel://host:port
  Sentinel 模式需额外配置 REDIS_MASTER_NAME 指定 master 名称。
"""
import platform
import redis
from redis.sentinel import Sentinel
from urllib.parse import urlparse

redis_client = None


def init_app(app):
    """初始化 Redis 客户端，根据 URL 前缀自动选择单机或 Sentinel 模式。"""
    global redis_client

    redis_cache_server_url = app.config.get("REDIS_URL")
    import socket

    # Linux 下启用 TCP Keepalive，防止长时间空闲连接被防火墙断开
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
