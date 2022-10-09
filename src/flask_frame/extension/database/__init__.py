import json
import os
import random
import time
from itertools import zip_longest
import functools
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

from ..lock import get_lock, Lock

db = None
db_schema = "public"
BaseModel = None
AutoMapModel = None
current_app = None


def json_dumps(*data, **kwargs):
    return json.dumps(*data, ensure_ascii=False, **kwargs)


def init_app(app):
    """初始化数据库

    Args:
        app (flask app): _description_
    """

    global db, db_schema, BaseModel, AutoMapModel, current_app
    current_app = app
    db_schema = app.config.get("DB_SCHEMA")

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
                "json_serializer": json_dumps,
                # 配置成1200 会导致对接 高斯 断开报错
                "pool_recycle": 600,
                "pool_size": 5,
                "max_overflow": 30,
                "pool_pre_ping": True,
                **engine_options_env,
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
            version_file_list = [
                os.path.join(sql_path, item) for item in os.listdir(sql_path)
            ]

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

        __table_args__ = {"extend_existing": True, "schema": db_schema}

    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)


def compare_version(version1: str, version2: str) -> int:
    """
    版本号管理 版本1 - 版本2
    :param version1: 版本1
    :param version2: 版本2
    :return: 版本距离
    """
    version1 = version1.split("/")[-1]

    for v1, v2 in zip_longest(version1.split("."), version2.split("."), fillvalue=0):
        x, y = int(v1), int(v2)
        if x != y:
            return 1 if x > y else -1
    return 0


def file_compare_version(file1: str, file2: str) -> int:
    return compare_version(
        os.path.splitext(os.path.split(file1)[1])[0],
        os.path.splitext(os.path.split(file2)[1])[0],
    )


def init_db(db, schema, file_list, version_file_list):
    """
    初始化数据库到当前
    :param db: 数据库实例
    :param schema: schema
    :param file_list: 文件列表
    :param version_file_list: 版本文件列表
    """
    lock = get_lock("init-db")  # 给app注入一个外部锁
    time.sleep(random.randint(0, 3))
    lock.acquire()

    try:
        first_sql = f"set search_path to {schema}; "

        schema_exist = db.engine.execute(
            f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}'"
        ).fetchone()

        # 获取版本
        version = None
        if schema_exist:
            table_exist = db.engine.execute(
                f"select *  from pg_tables where tablename='param' and schemaname='{schema}'"
            ).fetchone()
            if table_exist:
                version = db.engine.execute(
                    first_sql + "select value from param where key='version';"
                ).fetchone()
            if version:
                version = version[0]

        # 初始化
        if not version:
            current_app.logger.info("初始化数据库")

            if schema_exist:
                db.engine.execute(sqlalchemy.schema.DropSchema(db_schema, cascade=True))

            db.engine.execute(sqlalchemy.schema.CreateSchema(db_schema))
            db.engine.execute(f"GRANT ALL ON SCHEMA {db_schema} TO current_user;")
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
                update_file_switch = current_app.config.get("DB_UPDATE_SWITCH", False)

                if update_file_list and not update_file_switch:
                    update_db(db, db_schema, update_file_list)
    finally:
        lock.release()


def update_db(db, schema, file_list):
    """
    初始化数据库到当前
    :param db: 数据库实例
    :param schema: schema
    :param file_list: 文件列表
    """
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
            current_app.logger.info(f"worker: {os.getpid()} run: " + file_path + " end")

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


def run_sql(file_path, db, first_sql):
    """
    对数据库云信脚本文件
    :param file_path: 文件路径
    :param db: 数据库对象
    :param first_sql: 估计头部语句
    """
    # Create an empty command string
    db.session.execute(first_sql)

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
                        db.session.execute(sqlalchemy.text(sql_command))
                        sql_command = ""
                        function_start = False

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception("脚本执行出错" + str(e))


def sql_concat(file_path, param):
    """
    sql 语句拼接
    :param file_path: 文件路径
    :param param: 传入参数
    :return: 返回完整的 sql 语句
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
