"""
数据库插件（SQLAlchemy + 自动迁移）。
核心功能：
  - 自动 URL 编码密码中的特殊字符
  - 支持 GaussDB 版本兼容
  - 启动时自动执行 SQL 迁移脚本（版本号通过文件名管理）
  - 自动 reflect 数据库表结构到 db.Model
  - 支持多 schema（逗号分隔）
"""
import json
import os
import random
import time
from itertools import zip_longest
import functools
from typing import TYPE_CHECKING

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from tenacity import retry, stop_after_attempt
from sqlalchemy import text
from ..lock import get_lock, Lock

__all__ = [
    "db",
    "db_schema",
    "BaseModel",
    "AutoMapModel",
    "current_app",
    "json_dumps",
    "init_app",
    "compare_version",
    "file_compare_version",
    "init_db",
    "update_db",
    "run_sql",
    "sql_concat",
]

if TYPE_CHECKING:
    from flask import Flask
    from flask_sqlalchemy.model import Model
    from flask_sqlalchemy import SQLAlchemy

    db: SQLAlchemy
    BaseModel: type[Model]
    AutoMapModel: type
    current_app: Flask
    db_schema: str | list[str]
else:
    db = None
    BaseModel = None
    AutoMapModel = None
    current_app = None
    db_schema = "public"


def json_dumps(*data, **kwargs) -> str:
    """JSON 序列化，确保非 ASCII 字符正确输出"""
    return json.dumps(*data, ensure_ascii=False, **kwargs)


def init_app(app: "Flask") -> None:
    """
    初始化数据库连接和自动迁移。
    
    Args:
        app: Flask 应用实例，需配置 SQLALCHEMY_DATABASE_URI 和 DB_SCHEMA。
    """

    global db, db_schema, BaseModel, AutoMapModel, current_app
    current_app = app
    db_schema = app.config.get("DB_SCHEMA")

    # 如果db_schema是字符串且包含逗号分隔符，则分割成列表
    if isinstance(db_schema, str) and "," in db_schema:
        db_schema = [s.strip() for s in db_schema.split(",") if s.strip()]

    # 编码密码，防止特殊字符
    password = (
        app.config.get("SQLALCHEMY_DATABASE_URI")
        .split("://", 1)[1]
        .split(":", 1)[1]
        .rsplit("@", 1)[0]
    )
    if not password.isalpha():  # 如果密码不是纯字母
        import urllib.parse

        app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get(
            "SQLALCHEMY_DATABASE_URI"
        )[::-1].replace(password[::-1], urllib.parse.quote_plus(password)[::-1], 1)[
            ::-1
        ]

    # 兼容高斯
    version = app.config.get("DB_VERSION")
    if version or "gaussdb" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        version_list = [int(item) for item in (version or "9.2").split(".")]

        from sqlalchemy.dialects.postgresql.base import PGDialect

        PGDialect._get_server_version_info = lambda *args: tuple(version_list)

    # 其余参数
    params = {}
    if app.config.get("session_options"):
        params["session_options"] = app.config.get("session_options")

    # 从环境变量获取参数
    if app.config.get("SQLALCHEMY_ENGINE_OPTIONS"):
        db = SQLAlchemy(app, **params)

    # 自定义参数初始化
    else:
        # 自定义变量
        engine_options_env = {}
        if app.config.get("DB_POOL_SIZE"):
            engine_options_env["pool_size"] = app.config.get("DB_POOL_SIZE")
        if app.config.get("DB_MAX_OVERFLOW"):
            engine_options_env["max_overflow"] = app.config.get("DB_MAX_OVERFLOW")

        # 初始化
        db = SQLAlchemy(
            app,
            engine_options={
                "json_serializer": json_dumps,  # 自定义 JSON 序列化函数，确保非 ASCII 字符正确处理
                "pool_recycle": 300,  # 连接池回收时间（秒），防止数据库连接过期
                "pool_size": 5,  # 连接池基础大小，保持的持久连接数
                "max_overflow": 30,  # 最大溢出连接数，允许额外创建的连接数
                "pool_pre_ping": True,  # 在使用连接前 ping 数据库，确保连接有效性
                "connect_args": {
                    "keepalives": 1,  # 启用 TCP keepalive 机制
                    "keepalives_idle": 60,  # 60秒空闲就开始发送探测包
                    "keepalives_interval": 10,  # 每次探测间隔10秒
                    "keepalives_count": 5,  # 连续5次失败才认为连接断开
                    # 针对 Python 运算的 options 组合
                    "options": (
                        "-c tcp_keepalives_idle=60 "  # 3. 核心：让数据库定时响应 Python
                    ),
                },
                **engine_options_env,  # 从环境变量获取的额外引擎选项
            },
            **params,
        )

    # init_database
    auto_update = app.config.get("AUTO_UPDATE", False)
    if auto_update:
        # 初始化数据库
        init_file_list = app.config.get("DB_INIT_FILE")

        #  开发版本更新
        import os

        version_file_list = app.config.get("DB_VERSION_FILE")

        if not version_file_list:
            sql_path = "sql/migrate"

            # 如果文件不存在跳过
            if os.path.exists(sql_path):
                version_file_list = [
                    os.path.join(sql_path, item) for item in os.listdir(sql_path)
                ]
            else:
                version_file_list = []

        if init_file_list:
            init_db(db, db_schema, init_file_list, version_file_list)

        # 更新开发脚本
        update_file_list = app.config.get("DB_UPDATE_FILE")
        update_file_switch = app.config.get("DB_UPDATE_SWITCH", False)

        if update_file_list and update_file_switch:
            update_db(db, db_schema, update_file_list)

    class BaseModel:
        """
        schema base model
        """

        # 如果db_schema是列表，使用第一个schema；否则使用db_schema
        schema_value = db_schema[0] if isinstance(db_schema, list) else db_schema
        __table_args__ = {"extend_existing": True, "schema": schema_value}

    with app.app_context():
        # 使用SQLAlchemy的reflect功能，从数据库中自动发现并加载指定schema中的所有表结构
        # 这允许在运行时动态获取表定义，而无需手动定义每个模型类
        # 如果db_schema是列表，则反射多个schema；如果是字符串，则反射单个schema
        if isinstance(db_schema, list):
            for schema in db_schema:
                db.Model.metadata.reflect(bind=db.engine, schema=schema, views=True)
        else:
            db.Model.metadata.reflect(bind=db.engine, schema=db_schema, views=True)


def compare_version(version1: str, version2: str) -> int:
    """
    比较两个版本号的大小。
    
    Args:
        version1: 版本号1，如 "1.0.0" 或文件路径（自动提取文件名）。
        version2: 版本号2。
    
    Returns:
        int: 大于返回 1，小于返回 -1，相等返回 0。
    """
    version1 = version1.split("/")[-1]

    for v1, v2 in zip_longest(version1.split("."), version2.split("."), fillvalue=0):
        x, y = int(v1), int(v2)
        if x != y:
            return 1 if x > y else -1
    return 0


def file_compare_version(file1: str, file2: str) -> int:
    """
    比较两个 SQL 文件名对应的版本号。
    
    Args:
        file1: 文件路径1。
        file2: 文件路径2。
    
    Returns:
        int: 版本比较结果。
    """
    return compare_version(
        os.path.splitext(os.path.split(file1)[1])[0],
        os.path.splitext(os.path.split(file2)[1])[0],
    )


def init_db(db, schema, file_list, version_file_list):
    """
    初始化数据库结构，执行初始化脚本和版本迁移脚本。
    使用分布式锁保证多实例部署时只执行一次。
    
    Args:
        db: SQLAlchemy 实例。
        schema: 数据库 schema 名称。
        file_list: 初始化 SQL 脚本路径列表（DB_INIT_FILE）。
        version_file_list: 版本迁移脚本路径列表，按文件名版本号排序执行。
    """
    with current_app.app_context():

        lock = get_lock("init-db")  # 给app注入一个外部锁
        time.sleep(random.randint(0, 3))
        lock.acquire()
        try:
            first_sql = f"set search_path to {schema}; "
            schema_exist = db.session.execute(
                text(
                    f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}'"
                )
            ).fetchone()

            # 获取版本
            version = None
            if schema_exist:
                table_exist = db.session.execute(
                    text(
                        f"select *  from pg_tables where tablename='param' and schemaname='{schema}'"
                    )
                ).fetchone()
                if table_exist:
                    version = db.session.execute(
                        text(first_sql + "select value from param where key='version';")
                    ).fetchone()
                if version:
                    version = version[0]

            # 初始化
            if not version:
                current_app.logger.info("初始化数据库")

                # 重新构建schema
                from flask_frame.util.com_tool import str_to_bool

                # 获取配置数据
                recreate_schema = False
                recreate_schema_key = "RECREATE_SCHEMA"
                if current_app.config.get(recreate_schema_key):
                    recreate_schema = current_app.config.get(recreate_schema_key)
                elif os.environ.get(recreate_schema_key):
                    recreate_schema = str_to_bool(os.environ.get(recreate_schema_key))

                # 判断是否创建
                if schema_exist and recreate_schema:
                    db.session.execute(
                        sqlalchemy.schema.DropSchema(db_schema, cascade=True)
                    )
                elif not schema_exist:
                    db.session.execute(sqlalchemy.schema.CreateSchema(db_schema))
                    db.session.execute(
                        text(f"GRANT ALL ON SCHEMA {db_schema} TO current_user;")
                    )

                # 运行初始化脚本
                for file_path in file_list:
                    run_sql(file_path, db, first_sql)

            elif version_file_list:
                #  根据版本运行更新脚本
                update_db_sign = False  # 数据库更新脚本执行标志
                for version_file in sorted(
                    version_file_list, key=functools.cmp_to_key(file_compare_version)
                ):
                    (file_path, temp_file_name) = os.path.split(version_file)
                    (current_version, extension) = os.path.splitext(temp_file_name)

                    # 小于当前版本 不执行
                    if compare_version(current_version, version) < 1:
                        continue

                    run_sql(version_file, db, first_sql)
                    update_db_sign = True

                # 在版本更新的时候去更新脚本
                if update_db_sign:
                    update_file_list = current_app.config.get("DB_UPDATE_FILE")
                    update_file_switch = current_app.config.get(
                        "DB_UPDATE_SWITCH", False
                    )

                    if update_file_list and not update_file_switch:
                        update_db(db, db_schema, update_file_list)
        finally:
            lock.release()


def update_db(db, schema, file_list):
    """
    执行开发阶段的更新脚本（DB_UPDATE_FILE）。
    通过分布式锁 + 文件锁双重保护，确保多实例环境中仅执行一次。
    
    Args:
        db: SQLAlchemy 实例。
        schema: 数据库 schema 名称。
        file_list: 更新 SQL 脚本路径列表。
    """
    with current_app.app_context():  # 添加这一行
        lock = get_lock("update-db")
        time.sleep(random.randint(0, 3))
        if lock.locked():
            current_app.logger.info(f"worker: {os.getpid()} detect update-db locked")
            return

        lock.acquire()

        # 判断服务实例本地是否有文件锁
        if Lock.get_file_lock("had-update-db", timeout=999999).locked():
            current_app.logger.info("had update db file lock locked")
            return

        # 查询是否有分布式锁
        if Lock.lock_type() == "redis_lock" and get_lock("had-update-db").locked():
            # 如果有分布式进程在执行 当前进程添加文件锁
            current_app.logger.info("had update db redis lock locked")
            Lock.get_file_lock("had-update-db", timeout=999999).acquire()
            return

        try:
            first_sql = f"set search_path to {schema}; "

            for file_path in file_list:
                current_app.logger.info(
                    f"worker: {os.getpid()} run: " + file_path + " begin"
                )
                run_sql(file_path, db, first_sql)
                current_app.logger.info(
                    f"worker: {os.getpid()} run: " + file_path + " end"
                )

            # 添加分布式锁
            if Lock.lock_type() == "redis_lock":
                get_lock("had-update-db", timeout=600).acquire()

            # 任何锁方式都添加文件锁
            Lock.get_file_lock("had-update-db", timeout=999999).acquire()

            current_app.logger.info(f"worker: {os.getpid()} executed update db")

        except Exception as e:
            current_app.logger.exception(e)
        finally:
            lock.release()


@retry(reraise=True, stop=stop_after_attempt(2))
def run_sql(file_path: str, db: "SQLAlchemy", first_sql: str) -> None:
    """
    执行 SQL 脚本文件，支持存储函数（$$...$$）的完整解析。
    
    Args:
        file_path: SQL 脚本文件路径。
        db: SQLAlchemy 实例。
        first_sql: 执行前预设的 SQL 语句（如设置 search_path）。
    
    Raises:
        Exception: 脚本执行失败时抛出，自动回滚事务。
    """
    db.session.execute(text(first_sql))

    sql_command = ""
    with open(file_path) as sql_file:
        try:
            # Iterate over all lines in the sql file
            function_start = False  # mean read function

            for line in sql_file:
                # function start
                if "$$" in line.lstrip():
                    function_start = True

                # Ignore commented lines
                if not line.lstrip().startswith("--") and line.strip("\n"):
                    # Append line to the command string
                    sql_command += " " + line.strip("\n").strip()

                    # If the command string ends with ';', it is a full statement
                    if (
                        not function_start and sql_command.endswith(";")
                    ) or sql_command.endswith("$$;"):
                        db.session.connection().execution_options(
                            no_parameters=True
                        ).execute(sql_command)
                        sql_command = ""
                        function_start = False

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception("脚本执行出错" + str(e))


def sql_concat(file_path: str, param: dict[str, str]) -> str:
    """SQL 语句模板拼接, 支持 --{变量名} 格式的条件插入.

    Args:
        file_path: SQL 模板文件路径.
        param: 参数字典, 键名对应模板中的 --{变量名} 标记.

    Returns:
        str: 拼接后的完整 SQL 语句.
    """
    sql_command = ""

    with open(file_path) as sql_file:
        for line in sql_file:
            text = line.strip()
            if (
                text.startswith("--{")
                and text.replace("--{", "").replace("}", "") in param.keys()
            ):
                text = line.replace("--", "").format(**param)
            elif text.startswith("--") and text:
                continue

            sql_command += " " + text

    return sql_command
