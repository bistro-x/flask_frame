# Flask RESTful 应用框架

基于 Flask 快速搭建 RESTful 接口应用，支持丰富插件扩展。

## 快速开始

### 本地开发

```bash
pip3 install -e .
```

### 发布到 PyPI

```bash
rm -rf dist && python3.12 setup.py sdist bdist_wheel && twine upload dist/*
```

### 镜像构建

```bash
# 主镜像
docker build . --force-rm=true -f docker/Dockerfile.python -t wuhanchu/python:flask_frame_master && docker push wuhanchu/python:flask_frame_master

# Alpine 镜像
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine > build_alpine.log 2>&1 &
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine_continue -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine &
```

### 应用编译

- 普通编译：`docker build -f ./frame/docker/Dockerfile.source .`
- 加密编译：`docker build -f ./frame/docker/Dockerfile.encrypt .`

## 默认接口

- `GET /` - 健康检查（返回 "app is running"）
- `GET /healthy` - 健康状态（JSON）
- `GET /flask/log` - 日志文件列表
- `GET /flask/log/download` - 下载日志压缩包
- `GET /debug-sentry` - 触发错误（调试 Sentry）
- 任意接口加 `?profile` 参数可获取性能分析报告

## OpenAPI 文档生成

从 Flask 路由自动生成 API 规范，支持导入 Apifox 或通过 API 自动推送（增量同步）。

### VS Code Task 配置

在业务项目中创建 `.vscode/tasks.json`：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "sync_to_apifox",
      "type": "shell",
      "command": "/usr/bin/python3.12",
      "args": [
        "-m", "flask_frame", "sync_apifox",
        "--token", "afxp_xxx",
        "--project-id", "xxx"
      ],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": true,
        "panel": "dedicated",
        "showReuseMessage": false,
        "clear": false
      },
      "problemMatcher": []
    }
  ]
}
```

`Ctrl+Shift+B` 选择 `sync_to_apifox` 即可推送。

**约定**：框架自动检测业务项目结构创建应用——导入 `config` 调 `create_app(config)`，检测 `module`/`context` 包自动初始化，最后用 flasgger 生成 swagger spec。项目只需有 `config.py`（含 `config` 变量）和标准的 `module`、`context` 模块即可。

如需自定义 app 创建逻辑，可传 `--app` 参数指定工厂函数：

```bash
python -m flask_frame sync_apifox --app "app:create_app" --token xxx --project-id xxx
```

获取凭据：Apifox 项目设置 → API 认证获取 Token，项目设置 → 基本信息获取项目 ID。

## 配置项

### 基础配置

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| PRODUCT_KEY | str | | 项目名称，也作为数据库 schema、锁前缀等 |
| SQLALCHEMY_DATABASE_URI | str | | 数据库连接地址（PostgreSQL） |
| DB_SCHEMA | str | | 数据库 schema，支持逗号分隔多 schema（如 `"public,user_auth"`） |
| AUTO_UPDATE | bool | True | 启动时自动执行数据库迁移 |
| DB_UPDATE_SWITCH | bool | False | 是否执行 DB_UPDATE_FILE |
| RECREATE_SCHEMA | bool | False | 是否强制重建 schema |
| DB_INIT_FILE | str/list | | 初始化 SQL 脚本路径 |
| DB_VERSION_FILE | str/list | | 版本迁移脚本路径，默认扫描 `sql/migrate/` 目录 |
| DB_UPDATE_FILE | str/list | | 开发更新脚本路径 |
| ENABLED_EXTENSION | list | | 启用的插件列表，如 `['database', 'redis', 'lock']` |
| FETCH_USER | bool | True | 是否获取用户信息（需 permission 插件） |
| CHECK_API | bool | True | 是否启用 API 权限校验（需 permission 插件） |
| ADMIN_TOKEN | str | | 可跳过鉴权的固定 Token |
| ENCRYPTION_KEY | str | | 数据加密 Key，未指定时使用 PRODUCT_KEY |
| DB_POOL_SIZE | int | 5 | 数据库连接池大小 |
| DB_MAX_OVERFLOW | int | 30 | 最大溢出连接数 |
| DB_VERSION | str | | 指定数据库版本号（兼容 GaussDB） |

### 插件配置

| 配置项 | 关联插件 | 说明 |
|--------|----------|------|
| REDIS_URL | redis, lock, celery | Redis 连接地址，支持 Sentinel 模式（`sentinel://...`） |
| REDIS_MASTER_NAME | redis, lock, celery | Sentinel 模式的 master 名称 |
| SENTRY_DSN / SENTRY_DS | sentry | Sentry DSN 地址（优先 SENTRY_DSN，兼容 SENTRY_DS） |
| LOG_LEVEL | sentry, loguru | 日志级别 |
| MINIO_SERVER | minio | MinIO 服务地址（host:port） |
| MINIO_ACCESS_KEY | minio | MinIO Access Key |
| MINIO_SECRET_KEY | minio | MinIO Secret Key |
| MINIO_ACCESS_URL | minio | MinIO 文件访问基础 URL |
| MINIO_USE_HTTPS | minio | 是否使用 HTTPS（`"1"/"true"/"yes"/"on"`） |
| CONSUL_HOST | consul | Consul 地址 |
| CONSUL_PORT | consul | Consul 端口 |
| CONSUL_TOKEN | consul | Consul Token（必需） |
| API_LOG_DB_URI | api_log | API 日志数据库地址 |
| API_LOG_RETENTION_DAYS | api_log | API 日志保留天数，默认 30 |
| CELERY_DEFAULT_QUEUE | celery | Celery 默认队列名 |
| PROXY_SERVICE_URL | postgrest | PostgREST 代理服务地址 |
| PROXY_LOCAL | postgrest | 是否使用本地数据库代理（`"True"`/`"False"`） |
| PROXY_CUSTOM | postgrest | 是否自定义代理路由 |
| USER_AUTH_URL | permission | 用户认证服务地址 |
| LICENSE_CHECK | permission | 是否检查 License |

## 插件系统

插件目录：`src/flask_frame/extension/`

在 `ENABLED_EXTENSION` 配置列表中添加插件名称即可启用。每个插件实现 `init_app(app)` 方法。

| 插件名称 | 说明 | 依赖 |
|----------|------|------|
| database | SQLAlchemy 数据库 + 自动迁移 | - |
| redis | Redis 客户端（支持 Sentinel） | - |
| lock | 分布式锁（优先 Redis，降级文件锁） | redis |
| celery | Celery 异步任务（使用 REDIS_URL 作为 broker） | redis |
| permission | 用户鉴权 + API 权限校验 | - |
| api_log | API 请求日志记录 | database, celery |
| sentry | Sentry 错误监控 | - |
| minio | MinIO 文件存储 | - |
| consul | Consul 服务发现 + KV 配置 | - |
| loguru | Loguru 日志系统 | lock |
| marshmallow | Flask-Marshmallow 集成 | - |
| postgrest | PostgREST 代理（本地/远程） | database |

## 项目结构

```
src/flask_frame/
├── app.py                     # 应用工厂 create_app()
├── openapi.py                 # OpenAPI 文档生成（generate_openapi）
├── api/                       # 请求/响应/异常处理
│   ├── request.py             #   get_request_param(), proxy()
│   ├── response.py            #   Response.make_flask_response()
│   └── exception.py           #   ResourceError, CallException, BusiError(deprecated)
├── annotation/                # @deprecated, @profile 装饰器
├── extension/                 # 插件系统
│   ├── __init__.py            #   遍历 ENABLED_EXTENSION 动态加载
│   ├── database/              #   数据库插件（SQLAlchemy + 自动迁移 + reflect）
│   ├── redis.py               #   Redis 客户端
│   ├── lock.py                #   分布式锁
│   ├── celery.py              #   Celery 任务
│   ├── permission.py          #   权限校验
│   ├── api_log/               #   API 日志
│   ├── sentry.py              #   Sentry 监控
│   ├── minio.py               #   MinIO 文件存储
│   ├── consul.py              #   Consul 服务发现
│   ├── loguru/                #   Loguru 日志
│   ├── marshmallow.py         #   Marshmallow 集成
│   └── postgrest/             #   PostgREST 代理
├── schema/                    # BaseSchema（自动剔除空值字段）
├── algorithm/                 # 算法扩展
├── sql/                       # 内置 SQL 脚本（api_log, param）
├── util/                      # 工具类（db, file, json, lock, rsa, sql, fernet）
└── thread/                    # 线程相关
```

### 其他目录

- `tasks/` — 应用层代码，含权限初始化逻辑（`tasks/database.py`），非框架核心
- `docker/` — Docker 构建文件
- `test/` — 测试目录（失效测试已清理，当前无可运行用例）
- `doc/` — 迁移文档
