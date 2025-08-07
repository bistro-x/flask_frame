import consul
import socket

consul_client = None  # 全局 Consul 客户端实例


def init_app(app):
    global consul_client

    # 获取配置
    consul_host = app.config.get("CONSUL_HOST")
    consul_port = app.config.get("CONSUL_PORT")
    consul_token = app.config.get("CONSUL_TOKEN")

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

    # 注册服务
    service_host = app.config.get("HOST", get_local_ip())
    check = consul.Check.http(f"http://{service_host}:{service_port}/", interval="60s")
    consul_client.agent.service.register(
        name=service_name,
        service_id=service_name,
        address=service_host,
        port=service_port,
        check=check,
    )


    
    # 获取注册名
    url = get_service_url(service_name)  # 确保服务已注册
    print(f"Consul service {service_name} registered at {url}")

def get_local_ip():
    """自动获取本机 IP 地址（非 127.0.0.1）"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 连接到一个外部地址（不需要实际连通）
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


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
    
    
    return f"http://{address}:{port}"
