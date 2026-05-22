"""
MinIO 文件存储插件。
提供文件上传、下载、删除、存在性检查等功能。
支持两种上传方式：
  - upload_file_to_minio: 从本地文件上传
  - upload_bytes_to_minio: 从内存字节流上传
"""
import os
from io import BytesIO
from urllib.parse import urljoin, urlparse
from minio import Minio

client = None
access_url = None
service_url = None


def init_app(app):
    """
    初始化 MinIO 客户端。
    
    Args:
        app: Flask 应用实例，需配置 MINIO_SERVER、MINIO_ACCESS_KEY、MINIO_SECRET_KEY。
             可选配置：MINIO_USE_HTTPS、MINIO_ACCESS_URL。
    
    Raises:
        Exception: 缺少必要配置时抛出。
    """
    """
    初始化 MinIO 客户端，读取 Flask 配置中的 MinIO 相关参数。
    优先从 app.config 获取，若未设置则从环境变量读取。
    支持 MINIO_USE_HTTPS 的多种真值表示（"1","true","yes","on"）。
    """
    global client
    global service_url
    global access_url

    # 优先从 app.config 获取，若不存在则从环境变量读取
    minio_server = app.config.get("MINIO_SERVER") or os.environ.get("MINIO_SERVER")
    access_key = app.config.get("MINIO_ACCESS_KEY") or os.environ.get("MINIO_ACCESS_KEY")
    secret_key = app.config.get("MINIO_SECRET_KEY") or os.environ.get("MINIO_SECRET_KEY")

    # MINIO_ACCESS_URL 可选，优先使用 app.config，否则使用环境变量
    access_url = app.config.get("MINIO_ACCESS_URL") or os.environ.get("MINIO_ACCESS_URL")

    # MINIO_USE_HTTPS 支持多种表示方式
    use_https_raw = app.config.get("MINIO_USE_HTTPS")
    if use_https_raw is None:
        use_https_raw = os.environ.get("MINIO_USE_HTTPS", "false")
    use_https = str(use_https_raw).lower() in ("1", "true", "yes", "on")

    # 必要配置校验
    if not minio_server or not access_key or not secret_key:
        raise Exception(
            "MinIO 配置缺失：请在 app.config 或环境变量中设置 MINIO_SERVER、MINIO_ACCESS_KEY、MINIO_SECRET_KEY"
        )

    # 初始化 MinIO 客户端
    client = Minio(
        minio_server,
        access_key=access_key,
        secret_key=secret_key,
        secure=use_https,
    )

    # 构建服务基础 URL
    service_url = f"https://{minio_server}" if use_https else f"http://{minio_server}"

    # 获取文件访问基础 URL，优先使用配置或环境变量，再回退到 service_url
    if not access_url:
        access_url = service_url
    # 确保以 / 结尾，避免 urljoin 覆盖路径
    if access_url and not access_url.endswith("/"):
        access_url = access_url + "/"


def upload_file_to_minio(bucket_name, file_path, object_name, content_type=None):
    """
    上传本地文件到 MinIO。
    
    Args:
        bucket_name: 存储桶名称，不存在时自动创建。
        file_path: 本地文件路径。
        object_name: MinIO 中的对象名（路径）。
        content_type: MIME 类型，为空时自动推断。
    
    Returns:
        str: 文件相对路径，格式为 /{bucket_name}/{object_name}。
    
    Raises:
        Exception: 上传失败时抛出。
    """
    global client

    try:
        # 检查存储桶是否存在，不存在则创建
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # 自动推断 content_type
        if not content_type:
            import mimetypes

            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

        client.fput_object(
            bucket_name, object_name, file_path, content_type=content_type
        )

        # 获取文件在 MinIO 的相对路径
        relative_url = f"/{bucket_name}/{object_name}"
        return relative_url

    except Exception as e:
        raise Exception("上传文件到 MinIO 失败:" + str(e))


def get_access_url(file_path):
    """
    获取文件的完整访问 URL。
    
    Args:
        file_path: 文件相对路径，如 /bucket/object 或 bucket/object。
    
    Returns:
        str: 完整的 HTTP/HTTPS 访问地址。
    """
    # 去掉前导 /，避免覆盖 access_url 的路径前缀
    path = (file_path or "").lstrip("/")
    return urljoin(access_url, path)


def convert_to_access_url(full_url: str) -> str:
    """
    将任意 MinIO URL 的域名替换为配置的 access_url。
    常用于将 MinIO 预签名 URL（内网域名）转换为外网可访问的代理域名。
    
    Args:
        full_url: 原始完整 URL。
    
    Returns:
        str: 替换域名后的完整 URL。
    """
    if not full_url:
        return full_url
    parsed = urlparse(full_url)
    # 使用已存在的方法拼接代理域名 + 原始路径
    base = get_access_url(parsed.path)
    if parsed.query:
        sep = "&" if "?" in base else "?"
        base = f"{base}{sep}{parsed.query}"
    return base


def delete_file_from_minio(file_path):
    """
    从 MinIO 删除指定文件。
    
    Args:
        file_path: 文件路径，格式为 /bucket/object 或 bucket/object。
    
    Returns:
        bool: 删除成功返回 True。
    
    Raises:
        Exception: 删除失败或路径格式错误时抛出。
    """
    global client

    try:
        # 去除前导斜杠并分割
        path = file_path.lstrip("/")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise Exception(
                "文件路径格式错误，需为 /bucket_name/object_name 或 bucket_name/object_name"
            )
        bucket_name, object_name = parts
        client.remove_object(bucket_name, object_name)
        return True
    except Exception as e:
        raise Exception("从 MinIO 删除文件失败:" + str(e))


def upload_bytes_to_minio(data_bytes, object_name, bucket_name="datacenter", content_type=None):
    """
    上传字节流到 MinIO。
    
    Args:
        data_bytes: 要上传的字节数据（bytes 类型）。
        object_name: MinIO 中的对象名（路径）。
        bucket_name: 存储桶名称，默认为 'datacenter'。
        content_type: MIME 类型，可选。
    
    Returns:
        str: 文件相对路径，格式为 /{bucket_name}/{object_name}。
    
    Raises:
        Exception: 上传失败时抛出。
    """
    global client
    from io import BytesIO

    try:
        # 检查存储桶是否存在
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        # 将字节数据转换为BytesIO对象
        data_stream = BytesIO(data_bytes)
        data_length = len(data_bytes)

        # 上传字节流
        client.put_object(
            bucket_name,
            object_name,
            data_stream,
            data_length,
            content_type=content_type,
        )

        # 获取相对地址
        relative_url = f"/{bucket_name}/{object_name}"
        return relative_url

    except Exception as e:
        raise Exception("上传字节流到 MinIO 失败:" + str(e))


def download_file_from_minio(file_path, target_file_path=None):
    """
    从 MinIO 下载文件到本地。
    
    Args:
        file_path: MinIO 文件路径，格式为 /bucket/object 或 bucket/object。
        target_file_path: 本地保存路径，为空时自动生成临时文件。
    
    Returns:
        str: 本地文件路径。
    
    Raises:
        Exception: 下载失败或路径格式错误时抛出。
    """
    global client
    from flask_frame.util.file import create_temp_file_path

    try:
        # 去除前导斜杠并分割
        path = file_path.lstrip("/")
        parts = path.split("/", 1)
        if len(parts) != 2:
            raise Exception(
                "文件路径格式错误，需为 /bucket_name/object_name 或 bucket_name/object_name"
            )
        bucket_name, object_name = parts

        # 自动生成临时文件路径，传入扩展名
        if target_file_path is None:
            import os

            ext = os.path.splitext(object_name)[1]
            target_file_path = create_temp_file_path(ext)
        else:
            # 确保多级目录存在
            import os

            dir_path = os.path.dirname(target_file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

        response = client.get_object(bucket_name, object_name)
        with open(target_file_path, "wb") as f:
            for chunk in response.stream(32 * 1024):
                f.write(chunk)
        response.close()
        response.release_conn()
        return target_file_path
    except Exception as e:
        raise Exception("从 MinIO 下载文件失败:" + str(e))


def file_exists(file_path):
    """
    检查 MinIO 文件是否存在。
    
    Args:
        file_path: 文件路径，格式为 /bucket/object 或 bucket/object。
    
    Returns:
        bool: 存在返回 True，否则返回 False。
    
    Raises:
        Exception: 路径格式错误或非 "不存在" 类型的 S3 错误时抛出。
    """
    global client
    from minio.error import S3Error

    path = (file_path or "").lstrip("/")
    parts = path.split("/", 1)
    if len(parts) != 2:
        raise Exception("文件路径格式错误，需为 /bucket_name/object_name 或 bucket_name/object_name")
    bucket_name, object_name = parts
    try:
        client.stat_object(bucket_name, object_name)
        return True
    except S3Error as e:
        if e.code in ("NoSuchKey", "NoSuchObject", "NotFound", "NoSuchBucket"):
            return False
        raise
