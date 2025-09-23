# Flask RESTful 应用框架

基于 Flask 快速搭建 RESTful 接口应用，支持丰富插件扩展。

## 项目说明

本项目旨在为中小型后端服务、微服务接口、数据平台等场景，提供一个易用、可扩展的 Flask RESTful 框架。通过插件化设计，开发者可根据实际需求灵活集成日志、权限、分布式锁、异步任务、文件存储等功能。框架适合快速原型开发、企业级接口服务、自动化运维平台等应用。

**主要优势：**

- 结构清晰，易于二次开发和维护
- 插件系统灵活，扩展性强
- 支持数据库自动迁移、权限校验、API 日志等企业级特性
- 适配多种部署环境（Docker、Alpine、PyPI）

**目标用户：**

- 需要快速搭建 RESTful API 的 Python 开发者
- 关注可维护性和扩展性的后端团队
- 有插件化、自动化运维需求的项目组

## 快速开始

### 镜像构建

```bash
# 主镜像
docker build . --force-rm=true -f docker/Dockerfile.python -t wuhanchu/python:flask_frame_master && docker push wuhanchu/python:flask_frame_master

# Python 3.6 Alpine 版本
docker build . --force-rm=true -f docker/Dockerfile.alpine.3.6 -t wuhanchu/python:3.6_alpie && docker push wuhanchu/python:3.6_alpie

# 构建/更新 Alpine 镜像（后台运行）
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine > build_alpine.log 2>&1 &
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine_continue -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine &
```

### 应用编译

- 普通编译：`docker build -f ./frame/docker/Dockerfile.source .`
- 加密编译：`docker build -f ./frame/docker/Dockerfile.encrypt .`

### 本地开发调试

```bash
pip install -e .
```

使用 pip 的 editable 模式，便于调试和代码同步。

### 发布到 PyPI

```bash
pip3 install twine
rm -rf dist
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

## 框架功能

- RESTful API 快速开发
- 插件系统，支持多种扩展
- 日志管理、权限校验、数据库自动迁移等

### 默认接口

- `GET /flask/log` - 日志列表
- `GET /flask/log/download` - 下载日志
- `GET /static/log/{文件路径}` - 查看指定日志

## 配置项说明

### 项目基础配置

| 配置项                  | 类型 | 默认值            | 说明                                      |
| ----------------------- | ---- | ----------------- | ----------------------------------------- |
| PPRODUCT_KEY            | str  | 空字符串          | 项目名称                                  |
| SQLALCHEMY_DATABASE_URI | str  | 空字符串          | 数据库连接地址                            |
| DB_SCHEMA               | str  | 空字符串          | 数据库 schema 名称                        |
| AUTO_UPDATE             | bool | True              | 自动更新数据库结构                        |
| DB_UPDATE_SWITCH        | bool | False             | 数据库更新脚本开关                        |
| RECREATE_SCHEMA         | bool | False             | 是否强制重建 schema                       |
| DB_INIT_FILE            | str  | ./sql/init.sql    | 初始化脚本路径                            |
| DB_VERSION_FILE         | str  | ./sql/version.sql | 版本迭代脚本路径                          |
| DB_UPDATE_FILE          | str  | ./sql/update.sql  | 开发脚本路径                              |
| FETCH_USER              | bool | True              | 启用用户信息获取                          |
| CHECK_API               | bool | True              | 启用 API 权限检查                         |
| API_LOG_RETENTION_DAYS  | int  | 30                | API 日志保留天数                          |
| ENABLED_EXTENSION       | list | [redis, lock]     | 启用插件列表                              |
| ENCRYPTION_KEY          | str  | 空字符串          | 数据加密 Key，如果不指定使用 PPRODUCT_KEY |

### 插件相关配置

| 配置项             | 类型 | 默认值   | 说明               | 关联插件    |
| ------------------ | ---- | -------- | ------------------ | ----------- |
| SENTRY_DSN         | str  | 空字符串 | Sentry DSN 地址    | sentry      |
| SENTRY_ENVIRONMENT | str  | dev      | Sentry 环境标识    | sentry      |
| REDIS_URL          | str  | 空字符串 | Redis 连接地址     | redis, lock |
| MINIO_ENDPOINT     | str  | 空字符串 | MinIO 服务地址     | minio       |
| MINIO_ACCESS_KEY   | str  | 空字符串 | MinIO Access Key   | minio       |
| MINIO_SECRET_KEY   | str  | 空字符串 | MinIO Secret Key   | minio       |
| CELERY_BROKER_URL  | str  | 空字符串 | Celery Broker 地址 | celery      |
| CONSUL_HOST        | str  | 空字符串 | Consul 服务地址    | consul      |
| CONSUL_PORT        | int  | 8500     | Consul 服务端口    | consul      |
| API_LOG_DB_URI     | str  | 空字符串 | API 日志数据库地址 | api_log     |

> 插件相关配置仅在对应插件启用时生效，具体参数请参考插件源码或目录下 README。

## 插件系统

插件目录：`src/flask_frame/extension/`

典型插件：

| 插件名称 | 说明         | 依赖   |
| -------- | ------------ | ------ |
| redis    | Redis 客户端 | -      |
| lock     | 分布式锁     | redis  |
| api_log  | API 日志     | 数据库 |
| sentry   | 错误监控     | -      |
| celery   | 任务队列     | -      |
| minio    | 文件存储     | -      |
| consul   | 服务发现     | -      |

插件启用：在配置项 `ENABLED_EXTENSION` 中添加插件名称。

插件开发建议：

- 实现 `init_app(app)` 方法，供主应用加载
- 通过 `app.config` 获取配置

---

如需详细开发文档或插件扩展说明，请参考各目录下 README 或源码注释。

- 每个插件建议实现 `init_app(app)` 方法，供主应用统一加载。
- 插件通过读取 `app.config` 获取所需配置。

## 详细项目结构

## 项目结构

```
src/flask_frame/
	app.py                  # 主应用入口
	api/                    # 请求/响应/异常处理
	algorithm/              # 算法相关扩展
	annotation/             # 注解与元数据
	extension/              # 插件系统（如 redis、celery、sentry、minio 等）
		redis.py        # Redis 客户端封装
		lock.py         # 分布式锁实现
		celery.py       # Celery 集成
		sentry.py       # Sentry 错误监控
		minio.py        # MinIO 文件存储
		consul.py       # Consul 服务发现
		api_log/        # API 日志插件（可扩展为子目录）
	permission_context.py   # 权限上下文
	schema/                 # 数据模型
	sql/                    # SQL 脚本
	thread/                 # 线程相关工具
	util/                   # 工具类
```

## 插件开发与扩展

所有插件均放置于 `src/flask_frame/extension/` 目录下，按需启用。

典型插件目录结构：

```
src/flask_frame/extension/
	redis.py        # Redis 客户端封装
	lock.py         # 分布式锁实现
	celery.py       # Celery 集成
	sentry.py       # Sentry 错误监控
	minio.py        # MinIO 文件存储
	consul.py       # Consul 服务发现
	api_log/        # API 日志插件（可扩展为子目录）
```

插件启用方式：在配置文件 `ENABLED_EXTENSION` 列表中添加插件名称。

插件开发建议：

- 每个插件建议实现 `init_app(app)` 方法，供主应用统一加载。
- 插件可通过读取 app.config 获取所需配置。

---
