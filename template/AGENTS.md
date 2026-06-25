# 业务服务 AGENTS.md 模板

## 项目概况

基于 flask_frame 框架的 REST API 服务。

## 框架用法摘要（flask_frame）

### 核心导入

```python
# 入口函数
from flask_frame import create_app, Response, FlaskFrameConfig

# OpenAPI 文档生成
from flask_frame import generate_openapi

# 数据库
from flask_frame.extension.database import db, run_sql, sql_concat

# 请求处理
from flask_frame.api.request import get_request_param, proxy_request

# 异常
from flask_frame.api.exception import ResourceError, CallException

# 分布式锁
from flask_frame.extension.lock import get_lock

# 文件上传
from flask_frame.extension.minio import upload_file_to_minio, download_file_from_minio

# Redis
from flask_frame.extension.redis import redis_client

# 权限
from flask_frame.extension.permission import get_current_user

# Celery 异步任务
from flask_frame.extension.celery import celery, BaseTask
```

### 响应封装

```python
# 成功响应
return Response(data={"items": [...]}).make_flask_response()

# 失败响应
return Response(result=False, message="操作失败", detail="详细原因", http_status=400).make_flask_response()
```

### 数据库操作

```python
# ORM 查询
users = db.session.query(User).filter(User.active == True).all()

# 执行 SQL 脚本
from flask_frame.extension.database import run_sql, current_app
run_sql("sql/query.sql", db, "set search_path to my_schema;")

# SQL 模板拼接（支持 --{变量名} 条件插入）
sql = sql_concat("sql/template.sql", {"filter": "WHERE status = 'active'"})
db.session.execute(sql)
```

### 分布式锁

```python
lock = get_lock("my_operation", timeout=60)
lock.acquire()
try:
    # 执行需要加锁的操作
    ...
finally:
    lock.release()
```

### 文件上传

```python
# 上传本地文件
url = upload_file_to_minio("my_bucket", "/path/to/file.pdf", "uploads/file.pdf")

# 上传字节流
url = upload_bytes_to_minio(file_bytes, "uploads/data.json", bucket_name="datacenter")

# 获取访问 URL
full_url = get_access_url(url)
```

### 异步任务

```python
@celery.task(base=BaseTask)
def process_data(data_id):
    # 任务逻辑
    # BaseTask 自动处理事务：成功 commit，失败 rollback
    ...
```

### OpenAPI 文档生成

```python
from flask_frame.openapi import generate_openapi, sync_to_apifox
from flasgger import Swagger

# 直接解析模式（无需 flasgger，元数据较少）
generate_openapi(app, title="My API", output_dir="./api_json")

# Flasgger 模式同步（推荐，完整元数据）
swagger = Swagger(app)
with app.app_context():
    swagger_spec = swagger.get_apispecs()
sync_to_apifox(app, token="xxx", project_id="xxx", swagger_spec=swagger_spec)

# 按模块过滤
sync_to_apifox(app, token="xxx", project_id="xxx", swagger_spec=swagger_spec, modules=["inquiry", "quotation"])
```

CLI 同步（按约定自动创建应用，无需额外配置）：

```bash
python -m flask_frame sync_apifox --token xxx --project-id xxx
```

### 配置参考

```python
from flask_frame import FlaskFrameConfig

config: FlaskFrameConfig = {
    "PRODUCT_KEY": "my_service",
    "SQLALCHEMY_DATABASE_URI": "postgresql://user:pass@host:5432/db",
    "DB_SCHEMA": "my_schema",
    "REDIS_URL": "redis://localhost:6379",
    "ENABLED_EXTENSION": ["database", "redis", "lock", "permission", "minio"],
    # 其他配置见 flask_frame.config.FlaskFrameConfig
}
```

## 开发命令

```bash
pip install flask_frame    # 安装框架
pip install -e .           # 本地开发安装
python app.py              # 启动服务
```