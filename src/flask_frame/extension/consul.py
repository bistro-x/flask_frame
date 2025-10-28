import consul
import socket
import os
import struct

consul_client = None  # 全局 Consul 客户端实例


def init_app(app):
    global consul_client

    # 简化：从 app.config 或环境读取，"None"/空字符串视为缺失
    def _get_conf(key):
        v = app.config.get(key, None)
        if v is None:
            v = os.environ.get(key)
        if isinstance(v, str):
            s = v.strip()
            if not s or s.lower() == "none":
                return None
        return v

    consul_host = _get_conf("CONSUL_HOST")
    consul_port = _get_conf("CONSUL_PORT")
    consul_token = _get_conf("CONSUL_TOKEN")

    # 尝试将端口转换为整数（转换失败则跳过注册）
    if consul_port is not None:
        try:
            consul_port = int(consul_port)
        except Exception:
            app.logger.warning("CONSUL_PORT 无效，跳过注册服务：%r", consul_port)
            return

    # 必须同时有 host/port/token，缺一则跳过注册
    if not (consul_host and consul_port and consul_token):
        app.logger.warn(
            "Consul 未配置完全，跳过注册 (host=%r, port=%r, token_present=%s)",
            consul_host,
            consul_port,
            bool(consul_token),
        )
        return

    # 注册服务名称和端口
    service_name = app.config.get("PRODUCT_KEY")
    service_port = app.config.get("RUN_PORT")

    # 初始化 python-consul2 客户端
    consul_client = consul.Consul(
        host=consul_host, port=consul_port, token=consul_token
    )

    # 初始化配置（从 Consul KV 获取）
    kv_prefix_list = ["config/common/", f"config/{service_name}/"]
    for kv_prefix in kv_prefix_list:

        # 获取所有以 kv_prefix 开头的 key
        index, kvs = consul_client.kv.get(kv_prefix, recurse=True)
        if kvs:
            for item in kvs:
                key = item["Key"]
                value = item["Value"]
                # Consul KV 返回的是 bytes 类型，需要解码为字符串
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8")
                    except Exception:
                        pass  # 解码失败则保留原值
                config_key = key.replace(kv_prefix, "").upper()
                app.config[config_key] = value

    # 注册服务 - Docker 部署时优先使用环境变量配置的服务地址
    service_host = (
        app.config.get("SERVICE_HOST")
        or os.environ.get("SERVICE_HOST")
        or app.config.get("HOST")
        or get_local_ip()
    )

    # Docker 部署时可能需要使用映射后的端口
    external_service_port = (
        app.config.get("SERVICE_PORT") or os.environ.get("SERVICE_PORT") or service_port
    )

    # 健康检查地址，Docker 部署时可能需要使用外部可访问的地址
    check_url = f"http://{service_host}:{external_service_port}/"
    check = consul.Check.http(check_url, interval="60s")

    consul_client.agent.service.register(
        name=service_name,
        service_id=service_name,
        address=service_host,
        port=int(external_service_port),
        check=check,
    )

    # 获取注册名
    url = get_service_url(service_name)  # 确保服务已注册
    print(f"Consul service {service_name} registered at {url}")
    print(f"Health check URL: {check_url}")


def get_local_ip():
    """自动获取本机 IP 地址（Docker bridge 模式下获取宿主机内网 IP）"""

    # 方法1: 优先从环境变量获取宿主机 IP（推荐方式）
    host_ip = os.environ.get("HOST_IP")
    if host_ip:
        return host_ip

    # 方法2: Docker bridge 模式下，通过 host.docker.internal 解析宿主机 IP
    try:
        host_ip = socket.gethostbyname("host.docker.internal")
        if host_ip and host_ip != "127.0.0.1":
            return host_ip
    except:
        pass

    # 方法3: 检查 Docker bridge 网络，通过网关获取宿主机网段的 IP
    try:
        # 读取默认路由获取网关
        with open("/proc/net/route", "r") as f:
            for line in f:
                fields = line.strip().split()
                if fields[1] != "00000000" or not int(fields[3], 16) & 2:
                    continue
                gateway_ip = socket.inet_ntoa(struct.pack("<L", int(fields[2], 16)))

                # bridge 模式下网关通常是 172.17.0.1，宿主机 IP 需要通过其他方式获取
                if gateway_ip.startswith("172.17.0."):
                    # 尝试连接宿主机网络获取真实的宿主机 IP
                    try:
                        # 获取本机所有网络接口，查找非 Docker 内部的 IP
                        import netifaces

                        for interface in netifaces.interfaces():
                            if interface.startswith("eth") and not interface.startswith(
                                "eth0"
                            ):
                                continue
                            addrs = netifaces.ifaddresses(interface)
                            if netifaces.AF_INET in addrs:
                                for addr in addrs[netifaces.AF_INET]:
                                    ip = addr["addr"]
                                    # 排除 Docker 内部 IP 和回环地址
                                    if not (
                                        ip.startswith("172.17.")
                                        or ip.startswith("127.")
                                        or ip == "0.0.0.0"
                                    ):
                                        return ip
                    except ImportError:
                        # 如果没有 netifaces，使用备选方案
                        pass
                break
    except:
        pass

    # 方法4: 从 DOCKER_HOST 环境变量解析
    if "DOCKER_HOST" in os.environ:
        docker_host = os.environ.get("DOCKER_HOST", "")
        if "://" in docker_host:
            host_part = docker_host.split("://")[1]
            if ":" in host_part:
                return host_part.split(":")[0]

    # 方法5: 传统方法获取本地 IP（最后的兜底方案）
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        return ip
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def get_service_url(service_name):
    """获取指定服务的健康实例地址"""
    global consul_client
    if not consul_client:
        raise RuntimeError("Consul 客户端未初始化，请先调用 init_app。")  # 中文报错

    index, nodes = consul_client.health.service(service_name, passing=True)
    if not nodes:
        return None

    # 返回第一个健康实例的地址和端口
    node = nodes[0]
    address = node["Service"]["Address"]
    port = node["Service"]["Port"]

    return f"http://{address}:{port}/"  # 返回完整的 URL    return f"http://{address}:{port}"
