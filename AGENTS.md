# AGENTS.md

## 项目概况

Flask RESTful 框架库（`flask_frame`），通过 PyPI 分发。目标用户为基于 Flask 搭建后端服务的团队。

- **入口**: `src/flask_frame/app.py` → `create_app(config)` 工厂函数
- **Python**: 3.12（系统 `python3` 指向 3.12，pip 装在 3.12 下）
- **包布局**: `src/` 布局（`setup.py` 中 `package_dir={"": "src"}`）

## 开发命令

```bash
pip install -e .                    # 本地可编辑安装
python3.12 setup.py sdist bdist_wheel && twine upload dist/*   # PyPI 发布
```

## 测试

```bash
python3.12 -m pytest test/ -q
```

> 注意：`test/` 目录下的失效测试文件已清理。当前无可运行的测试用例。

## 架构要点

- **插件系统**: `src/flask_frame/extension/__init__.py` 遍历 `app.config['ENABLED_EXTENSION']` 列表，动态 import 并调用每个插件的 `init_app(app)`。新增插件只需在此目录下放 `.py` 文件或子包并实现 `init_app`。
- **核心插件**: `database`（SQLAlchemy + 自动迁移）、`redis`、`lock`（分布式锁，依赖 redis 插件）、`permission`（用户鉴权）、`api_log`、`celery`、`sentry`、`minio`、`consul`、`marshmallow`、`loguru`、`postgrest`
- **数据库自动迁移**: `AUTO_UPDATE=True` 时，启动时自动执行 `DB_INIT_FILE` → `sql/migrate/` 版本脚本 → `DB_UPDATE_FILE`（需 `DB_UPDATE_SWITCH=True`）。版本号通过 SQL 文件名对比管理。
- **请求事务**: `app.py` 中 `teardown_request` 自动 commit，全局异常处理自动 rollback。
- **自定义异常**: `BusiError`（已 deprecated）、`ResourceError`、`CallException`，均继承 `HTTPException`。
- **响应封装**: `Response.make_flask_response()` 返回标准 Flask Response，包含 `result/code/message/data/create_time` 结构。

## 容易踩坑的地方

- `BaseSchema`（`schema/__init__.py`）在 `pre_load` 阶段会自动剔除 `None`、`''`、`[]`、`{}` 值的字段，调试反序列化问题时需注意。
- `setup.py` 版本号是唯一的版本来源，当前为 `1.2.0`。
- `tasks/` 目录是应用层代码（非框架核心），含权限初始化逻辑，依赖使用方自行调用。
- `DB_SCHEMA` 配置支持逗号分隔的多 schema（如 `"public,user_auth"`）。
- `extension/database/__init__.py` 会自动 reflect 数据库表到 `db.Model`，无需手动定义所有 Model。
- 数据库密码中的特殊字符会被自动 URL 编码。
- `SENTRY_DSN`（兼容旧配置键 `SENTRY_DS`）配置同时支持两个键名
- `lock` 插件优先使用 Redis 分布式锁，无 Redis 时降级为文件锁。
