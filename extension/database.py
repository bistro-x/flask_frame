import json
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
    db = SQLAlchemy(app, engine_options={
        "json_serializer": json_dumps, "pool_size": 20, "max_overflow": 30
    })

    # init_database
    auto_update = app.config.get("AUTO_UPDATE", False)
    if auto_update:
        init_file_list = app.config.get("DB_INIT_FILE")
        if init_file_list:
            init_db(db, db_schema, init_file_list)

        update_file_list = app.config.get("DB_UPDATE_FILE")
        if update_file_list:
            update_db(db, db_schema, update_file_list)

    class BaseModel:
        """
        schema base model
        """
        __table_args__ = {'extend_existing': True, 'schema': db_schema}

    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)


def update_db(db, schema, update_file_list):
    """更新数据库到当前"""
    lock = Lock.get_file_lock("update_db")
    time.sleep(random.randint(0, 3))
    if lock.locked():
        return

    current_app.logger.info("获取锁")
    lock.acquire()
    current_app.logger.info("更新数据库")

    try:
        first_sql = f"set search_path to {schema}; "

        for file_path in update_file_list:
            run_sql(file_path, db, first_sql)
    finally:
        lock.release()


def init_db(db, schema, init_file_list):
    """初始化数据库到当前"""
    lock = Lock.get_file_lock()  ##给app注入一个外部锁
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

            for file_path in init_file_list:
                run_sql(file_path, db, first_sql)
        # todo 根据版本运行更新脚本

    finally:
        lock.release()


def run_sql(file_path, db, first_sql):
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
                    sql_command += " " + line.strip('\n')

                    # If the command string ends with ';', it is a full statement
                    if sql_command.endswith(';'):
                        db.session.execute(sqlalchemy.text(sql_command))
                        sql_command = ""

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise Exception("脚本执行出差" + e.get("message"))
