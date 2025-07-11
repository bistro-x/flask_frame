# Flask RESTful 应用框架

基于 Flask 快速搭建提供 RESTful 接口的应用框架，并提供丰富的扩展功能。

## 功能特性

- 快速搭建 RESTful API 服务
- 丰富的扩展功能支持
- 完善的日志管理
- 数据库集成支持
- 插件化架构

## 使用指南

### 基础镜像构建

#### Python 基础镜像

```bash
# 主镜像
docker build . --force-rm=true -f docker/Dockerfile.python -t wuhanchu/python:flask_frame_master && docker push wuhanchu/python:flask_frame_master

# Python 3.6 Alpine 版本
docker build . --force-rm=true -f docker/Dockerfile.alpine.3.6 -t wuhanchu/python:3.6_alpie && docker push wuhanchu/python:3.6_alpie

# 首次构建 Alpine 镜像（后台运行）
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine > build_alpine.log 2>&1 &

# 更新 Alpine 镜像（后台运行）
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine_continue -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine &
```



### 应用编译

#### 普通编译

```bash
docker build -f ./frame/docker/Dockerfile.source .
```

#### 加密编译

```bash
docker build -f ./frame/docker/Dockerfile.encrypt .
```

### 本地测试

```bash
pip install -e .
```

使用上述命令将应用安装到本地环境，便于项目调试。

#### Flask Frame 开发调试：使用 pip link 关联

如果你在开发 `flask_frame` 并希望在其他项目中实时同步代码变更，可以使用 pip 的“editable”模式（软链接安装）：

```bash
pip install -e .
```

这样，其他依赖 `flask_frame` 的项目只需在虚拟环境中安装一次，后续对 `flask_frame` 代码的修改会立即生效，无需重新安装。

### 发布到 PyPI

```bash
pip3 install twine

rm -rf dist
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

## 框架使用

### 调试模式

在请求 URL 参数中加入 `profile=true` 可进入调试模式。

### 默认接口

- `GET /flask/log` - 读取日志列表
- `GET /flask/log/download` - 下载日志文件
- `GET /static/log/{文件路径}` - 显示指定日志内容

## 项目结构

```
|-- http/                  # 网络请求相关文件
|-- util/                   # 工具类
|-- extension/              # 插件系统
|   |-- logura/             # 日志管理插件
|-- schema/                 # 数据模型和返回对象
|-- docker/                 # Docker 相关配置
|-- file/                   # 文件管理
|-- requirements.txt        # 框架核心依赖
|-- requirements_all.txt    # 完整依赖（用于基础镜像构建）
```

## 配置参考

| 分类   | 配置项                  | 说明                                                                   |
| ------ | ----------------------- | ---------------------------------------------------------------------- |
| 数据库 | SQLALCHEMY_DATABASE_URI | 数据库连接地址                                                         |
| 数据库 | DB_SCHEMA               | 数据库 schema                                                          |
| 数据库 | AUTO_UPDATE             | 是否自动更新数据库(依赖 DB_INIT_FILE, DB_VERSION_FILE, DB_UPDATE_FILE) |
| 数据库 | DB_UPDATE_SWITCH        | 更新脚本开关（开启则每次启动运行，关闭则仅在版本更新时运行）           |
| 数据库 | RECREATE_SCHEMA         | 强制重新创建 schema（默认 False）                                      |
| 数据库 | DB_INIT_FILE            | 数据库初始化脚本路径                                                   |
| 数据库 | DB_VERSION_FILE         | 数据库版本迭代脚本                                                     |
| 数据库 | DB_UPDATE_FILE          | 数据库开发脚本（每次启动运行）                                         |
| 权限   | FETCH_USER              | 是否启用用户获取功能                                                   |
| 权限   | CHECK_API               | 是否启用 API 接口检查                                                  |
| 日志   | API_LOG_RETENTION_DAYS  | API 日志保留天数（默认 30 天）                                         |

## 插件系统

通过 `ENABLED_EXTENSION` 配置启用项目所需的插件。

### 核心插件

| 插件名称 | 描述             | 依赖  |
| -------- | ---------------- | ----- |
| redis    | Redis 客户端支持 | -     |
| lock     | 分布式锁支持     | redis |

### 扩展插件

#### api_log

- 记录 API 请求到数据库
- 提供 `api_log_clean` 清理函数（需配合 Celery 使用）

#### sentry

支持 Sentry 错误监控系统，自动从 app.config 加载配置（以 `SENTRY_` 为前缀的配置项）。

例如：

- `SENTRY_ENVIRONMENT` → `environment` 参数
- `SENTRY_DSN` → `dsn` 参数
