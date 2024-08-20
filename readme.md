基于 flask 快速搭建 提供 restful 接口的应用。并提供丰富的应该扩展相关功能。

## 使用

## 基础镜像

### python

基础镜像

```bash
#3.6
docker build . --force-rm=true -f docker/Dockerfile.alpine.3.6 -t wuhanchu/python:3.6_alpie && docker push wuhanchu/python:3.6_alpie

# image first build
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine &

# image update
nohup docker build . --force-rm=true -f docker/Dockerfile.alpine_continue -t wuhanchu/python:3_alpine && docker push wuhanchu/python:3_alpine &
```

## 编译

普通编译

```bash
docker build -f ./frame/docker/Dockerfile.source  .
```

加密编译

```bash
docker build -f ./frame/docker/Dockerfile.encrypt  .
```

## 发布

```shell
pip3 install twine

rm -rf dist
python3 setup.py sdist bdist_wheel
twine upload dist/*
```

## 使用

### 调试

请求在 url 参数中加入 profile=true 可进入调试模式。

### 默认接口

get /flask/log 读取日志列表
get /flask/log/download 下载日志列表
get /static/log/{文件路径} 显示对应日志信息

## 配置

### 文件夹

http: 网络请求相关文件
requirements.txt 框架依赖的库

## 目录结构

```
|-- http                                  # 网络请求相关文件
|-- util                                  # 工具文件夹
|-- extension                             # 插件文件夹
|   |-- logura                            # 日志管理插件
|-- schema                                # 返回对象
|-- docker                                # 容器编译
|-- file                                  # 文件管理
|-- requirements.txt                      # 框架依赖的库
|-- requirements_all.txt                  # 规定使用项目用到的所有库和版本，作为基础镜像打包
```

## 配置信息

| 分组   | 配置项                  | 说明                                                            |
| ------ | ----------------------- | --------------------------------------------------------------- |
| 数据库 | SQLALCHEMY_DATABASE_URI | 数据库链接地址                                                  |
| 数据库 | DB_SCHEMA               | 对接的数据库 schema                                             |
| 数据库 | AUTO_UPDATE             | 是否自动更新数据库(DB_INIT_FILE,DB_VERSION_FILE,DB_UPDATE_FILE) |
| 数据库 | RECREATE_SCHEMA         | 如果 schema 已经存在强制重新创建 schema，默认 False             |
| 数据库 | DB_INIT_FILE            | 数据库初始化脚本                                                |
| 数据库 | DB_VERSION_FILE         | 数据库迭代脚本（根据版本更新）                                  |
| 数据库 | DB_UPDATE_FILE          | 数据库开发脚本（本次启动运行）                                  |
| 数据库 | DB_UPDATE_SWITCH        | 更新脚本开关（开则每次创建运行，关则必须有版本更新才会调用）    |
| 权限   | FETCH_USER              | 是否获取用户                                                    |
| 权限   | CHECK_API               | API 接口检查                                                    |
| 插件   | API_LOG_RETENTION_DAYS  | API 日志保留天数,默认 30 天                                     |

## 插件支持

ENABLED_EXTENSION 是配置项目中需要的插件

| 插件 | 说明 |
｜ redis | redis客户端|
｜ lock | 锁,依赖 redis｜

### api_log

- api_log: 记录 API 请求到数据库中进行保留
  - api_log_clean: celery 支持的自动日志清理函数，需要在 config 配置对应任务启用。

### sentry

支持配置 sentry 插件和对应的初始化参数。
初始化参数会从 app.config 取前缀未 sentry 的配置值。如果你想修改 sentry 的初始化参数，可以使用下面的对应逻辑。

environment -> SENTRY_ENVIRONMENT

只要 app.config 包含 SENTRY_ENVIRONMENT 的数据就可以在 sentry_sdk.init 传入 environment 参数。
