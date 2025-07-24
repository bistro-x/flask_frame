import os
from urllib.parse import urljoin
from minio import Minio

# MinIO 客户端实例
client = None
# MinIO 文件访问基础 URL
access_url = None
# MinIO 服务基础 URL
service_url = None


def init_app(app):
    """
    初始化 MinIO 客户端，读取 Flask 配置中的 MinIO 相关参数。
    """
    global client
    global service_url
    global access_url

    # 从 Flask 配置中获取 MinIO 配置信息
    minio_server = app.config.get("MINIO_SERVER")
    access_key = app.config.get("MINIO_ACCESS_KEY")
    secret_key = app.config.get("MINIO_SECRET_KEY")
    use_https = app.config.get("MINIO_USE_HTTPS", "false").lower() == "true"

    # 初始化 MinIO 客户端
    client = Minio(
        minio_server,  # MinIO 服务器地址
        access_key=access_key,
        secret_key=secret_key,
        secure=use_https,  # 是否使用 HTTPS
    )

    # 构建服务基础 URL
    service_url = (
        f"http://{minio_server}" if not use_https else f"https://{minio_server}"
    )

    # 获取文件访问基础 URL，优先使用 ACCESS_URL 配置
    access_url = app.config.get(
        "ACCESS_URL",
        service_url,
    )


def upload_file_to_minio(bucket_name, file_path, object_name):
    """
    上传文件到 MinIO 指定存储桶。

    Args:
        bucket_name (_type_): 存储桶名称
        file_path (_type_): 本地文件路径
        object_name (_type_): 存储到 MinIO 的对象名

    Returns:
        str: 文件在 MinIO 的相对路径
    """
    global client

    try:
        # 检查存储桶是否存在，不存在则创建
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # 上传文件到 MinIO
        client.fput_object(bucket_name, object_name, file_path)

        # 获取文件在 MinIO 的相对路径
        relative_url = f"/{bucket_name}/{object_name}"
        return relative_url

    except Exception as e:
        raise Exception("上传文件到 MinIO 失败:" + str(e))


def get_access_url(file_path):
    """
    获取文件的完整访问地址

    Args:
        file_path (_type_): 文件的路径地址（相对路径）

    Returns:
        str: 完整访问 URL
    """

    return urljoin(access_url, file_path)


def delete_file_from_minio(file_path):
    """
    从 MinIO 删除指定对象文件

    Args:
        file_path (str): MinIO 文件路径（格式: /bucket_name/object_name 或 bucket_name/object_name）

    Returns:
        bool: 删除成功返回 True，否则抛出异常
    """
    global client

    try:
        # 去除前导斜杠并分割
        path = file_path.lstrip("/")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise Exception("文件路径格式错误，需为 /bucket_name/object_name 或 bucket_name/object_name")
        bucket_name, object_name = parts
        client.remove_object(bucket_name, object_name)
        return True
    except Exception as e:
        raise Exception("从 MinIO 删除文件失败:" + str(e))