import json
import os
import random
import time

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

from frame.util.lock import Lock

db = None
db_schema = "public"
BaseModel = None
AutoMapModel = None
current_app = None


def json_dumps(*data, **kwargs):
    return json.dumps(*data, ensure_ascii=False, **kwargs)


def init_app(app):
    global db, db_schema, BaseModel, AutoMapModel, current_app
    current_app = app
    db_schema = app.config.get("DB_SCHEMA")

    if app.config.get("SQLALCHEMY_ENGINE_OPTIONS"):
        db = SQLAlchemy(app)
    else:
        db = SQLAlchemy(app, engine_options={
            "json_serializer": json_dumps, "pool_size": 20, "max_overflow": 30, "pool_pre_ping": True
        })

    # init_database
    auto_update = app.config.get("AUTO_UPDATE", False)
    if auto_update:
        # 初始化数据库
        init_file_list = app.config.get("DB_INIT_FILE")

        #  开发版本更新
        version_file_list = app.config.get("DB_VERSION_FILE")

        if init_file_list:
            init_db(db, db_schema, init_file_list, version_file_list)

        # 更新开发脚本
        update_file_list = app.config.get("DB_UPDATE_FILE")
        if update_file_list:
            update_db(db, db_schema, update_file_list)

    class BaseModel:
        """
        schema base model
        """
        __table_args__ = {'extend_existing': True, 'schema': db_schema}

    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)


def init_db(db, schema, file_list, version_file_list):
    """
    初始化数据库到当前
    :param db: 数据库实例
    :param schema: schema
    :param file_list: 文件列表
    :param version_file_list: 版本文件列表
    """
    lock = Lock.get_file_lock()  # 给app注入一个外部锁
    time.sleep(random.randint(0, 3))
    lock.acquire()

    try:
        first_sql = f"set search_path to {schema}; "

        schema_exist = db.engine.execute(
            f"SELECT 1 FROM information_schema.schemata WHERE schema_name = '{schema}'").fetchone()

        # 获取版本
        version = None
        if schema_exist:
            table_exist = db.engine.execute(
                f"select *  from pg_tables where tablename='param' and schemaname='{schema}'").fetchone()
            if table_exist:
                version = db.engine.execute(
                    first_sql + "select value from param where key='version';").fetchone()
            if version:
                version = version[0]

        # 初始化
        if not version:
            current_app.logger.info("初始化数据库")

            if schema_exist:
                db.engine.execute(sqlalchemy.schema.DropSchema(db_schema, cascade=True))

            db.engine.execute(sqlalchemy.schema.CreateSchema(db_schema))

            for file_path in file_list:
                run_sql(file_path, db, first_sql)

        elif version_file_list:
            #  根据版本运行更新脚本
            for version_file in sorted(version_file_list):
                (file_path, temp_file_name) = os.path.split(version_file)
                (current_version, extension) = os.path.splitext(temp_file_name)

                # 小于当前版本 不执行
                if current_version <= version:
                    continue
                run_sql(version_file, db, first_sql)
    finally:
        lock.release()


def update_db(db, schema, file_list):
    """
   初始化数据库到当前
   :param db: 数据库实例
   :param schema: schema
   :param file_list: 文件列表
   """
    lock = Lock.get_file_lock("update_db")
    time.sleep(random.randint(0, 3))
    if lock.locked():
        return

    lock.acquire()
    if Lock.get_file_lock("update_db_end", timeout=999999).locked():
        return

    try:
        first_sql = f"set search_path to {schema}; "

        for file_path in file_list:
            current_app.logger.info("run: " + file_path + " begin")
            run_sql(file_path, db, first_sql)
            current_app.logger.info("run: " + file_path + " end")

    finally:
        Lock.get_file_lock("update_db_end").acquire()
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

    sql_command = ''
    with open(file_path) as sql_file:
        try:
            # Iterate over all lines in the sql file
            for line in sql_file:
                # Ignore commented lines
                if not line.lstrip().startswith('--') and line.strip('\n'):
                    # Append line to the command string
                    sql_command += " " + line

                    # If the command string ends with ';', it is a full statement
                    if sql_command.endswith(';'):
                        db.session.execute(sqlalchemy.text(sql_command))
                        sql_command = ""

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise Exception("脚本执行出错" + e.get("message"))


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
            if text.startswith('--{') and text.replace("--{", "").replace("}", "") in param.keys():
                text = line.replace("--", "").format(**param)
            elif text.startswith('--') and text:
                continue

            sql_command += " " + text

    return sql_command
