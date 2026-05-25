"""
Flask Frame 配置类型定义。
提供 FlaskFrameConfig TypedDict，包含所有可用配置项及其类型。
AI 和类型检查器可利用此定义理解配置结构。

使用示例：
    from flask_frame.config import FlaskFrameConfig
    
    config: FlaskFrameConfig = {
        "PRODUCT_KEY": "my_service",
        "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@host/db",
        "ENABLED_EXTENSION": ["database", "redis", "lock"],
    }
"""
from typing import TypedDict, Required, NotRequired


class FlaskFrameConfig(TypedDict, total=False):
    """Flask Frame 框架配置类型定义。所有字段均为可选。"""

    # 基础配置
    PRODUCT_KEY: str
    """项目名称/锁前缀/schema标识。必填。"""

    SQLALCHEMY_DATABASE_URI: str
    """数据库连接 URI，格式：postgresql://user:pass@host:port/dbname。必填。"""

    DB_SCHEMA: str
    """数据库 schema，支持逗号分隔的多 schema（如 "public,user_auth"）。默认 "public"。"""

    DB_VERSION: str
    """数据库版本号（GaussDB 兼容）。默认 "9.2"。"""

    AUTO_UPDATE: bool
    """启用数据库自动迁移。默认 False。"""

    DB_INIT_FILE: list[str]
    """初始化 SQL 脚本路径列表。"""

    DB_VERSION_FILE: list[str]
    """版本迁移脚本路径列表（sql/migrate/ 目录）。"""

    DB_UPDATE_FILE: list[str]
    """开发阶段更新脚本路径列表。"""

    DB_UPDATE_SWITCH: bool
    """是否执行 DB_UPDATE_FILE。默认 False。"""

    RECREATE_SCHEMA: bool
    """启动时重建 schema（删除并重建）。默认 False。"""

    DB_POOL_SIZE: int
    """数据库连接池基础大小。默认 5。"""

    DB_MAX_OVERFLOW: int
    """数据库连接池最大溢出连接数。默认 30。"""

    ENABLED_EXTENSION: list[str]
    """启用的插件列表。如 ["database", "redis", "lock", "permission"]。"""

    FLASK_CONFIG: str
    """配置环境名（default/production/development）。"""

    session_options: dict
    """SQLAlchemy session 选项。"""

    PROFILE: bool
    """启用性能分析。默认 False。"""

    ENCRYPTION_KEY: str
    """加密密钥（Fernet）。"""

    # Redis 配置
    REDIS_URL: str
    """Redis 连接 URL。单机模式：redis://host:port；Sentinel 模式：sentinel://host:port;sentinel://host:port"""

    REDIS_MASTER_NAME: str
    """Redis Sentinel master 名称（Sentinel 模式必填）。"""

    # Lock 配置（继承 REDIS_URL 和 PRODUCT_KEY）
    # 无独立配置项

    # Celery 配置（继承 REDIS_URL）
    CELERY_DEFAULT_QUEUE: str
    """Celery 默认队列名。默认使用 PRODUCT_KEY。"""

    REDBEAT_LOCK_TIMEOUT: int
    """Redbeat 锁超时时间（秒）。默认 360。"""

    # Permission 配置
    CHECK_API: bool
    """启用 API 权限校验。默认 True。"""

    FETCH_USER: bool
    """启用用户信息获取。默认 True。"""

    ADMIN_TOKEN: str
    """管理员 TOKEN（跳过权限校验）。"""

    USER_AUTH_URL: str
    """用户认证服务地址。"""

    LICENSE_CHECK: bool
    """启用 License 校验。默认 True。"""

    # Sentry 配置
    SENTRY_DSN: str
    """Sentry DSN（推荐键名）。"""

    SENTRY_DS: str
    """Sentry DSN（兼容旧版键名）。"""

    LOG_LEVEL: str | int
    """日志级别。默认 INFO。"""

    # MinIO 配置
    MINIO_SERVER: str
    """MinIO 服务器地址。"""

    MINIO_ACCESS_KEY: str
    """MinIO Access Key。"""

    MINIO_SECRET_KEY: str
    """MinIO Secret Key。"""

    MINIO_ACCESS_URL: str
    """MinIO 文件访问 URL（外网代理地址）。"""

    MINIO_USE_HTTPS: bool
    """MinIO 使用 HTTPS。默认 False。"""

    # Consul 配置
    CONSUL_HOST: str
    """Consul 服务器地址。"""

    CONSUL_PORT: int
    """Consul 服务器端口。"""

    CONSUL_TOKEN: str
    """Consul ACL Token。"""

    SERVICE_HOST: str
    """服务注册地址（Docker 部署时使用）。"""

    SERVICE_PORT: int
    """服务注册端口（Docker 部署映射端口）。"""

    RUN_PORT: int
    """服务运行端口。"""

    HOST: str
    """服务主机地址（备用）。"""

    # Loguru 配置
    LOG_PATH: str
    """日志文件目录。默认 "./log"。"""

    LOG_NAME: str
    """日志文件名。默认 "{time:YYYY-MM-DD}.log"。"""

    LOG_LEVEL: str
    """日志级别。默认 "ERROR"。"""

    LOG_FORMAT: str
    """日志格式。"""

    LOG_ROTATION: str
    """日志轮转时间。默认 "00:00"。"""

    LOG_ENQUEUE: bool
    """日志队列模式（与 gevent 冲突）。默认 False。"""

    LOG_SERIALIZE: bool
    """日志序列化。默认 False。"""

    LOG_RETENTION: str
    """日志保留时间。默认 "30 days"。"""

    # API Log 配置
    API_LOG_RETENTION_DAYS: int
    """API 日志保留天数。默认 30。"""

    # PostgREST 配置
    PROXY_SERVICE_URL: str
    """PostgREST 服务地址。默认 "http://postgrest:3000"。"""

    PROXY_LOCAL: bool
    """本地模式（直接查询数据库）。默认 False。"""

    PROXY_CUSTOM: bool
    """自定义模式（不自动拦截请求）。默认 False。"""

    # 文件配置
    UPLOAD_FOLDER: str
    """上传文件目录。"""

    RETURN_FOLDER: str
    """返回文件目录。"""

    TEMP_FOLDER: str
    """临时文件目录。"""

    FILE_SERVICE_PREFIX: str
    """文件服务 URL 前缀。"""