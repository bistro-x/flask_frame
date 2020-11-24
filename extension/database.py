import json

import sqlalchemy
from flask_sqlalchemy import SQLAlchemy

from frame.util.lock import Lock

db = None
db_schema = "public"
BaseModel = None
AutoMapModel = None


def json_dumps(*data, **kwargs):
    return json.dumps(*data, ensure_ascii=False, **kwargs)


def init_app(app):
    global db, db_schema, BaseModel, AutoMapModel
    db_schema = app.config.get("DB_SCHEMA")
    db = SQLAlchemy(app, engine_options={
        "json_serializer": json_dumps, "pool_size": 20, "max_overflow": 30
    })

    # init_database
    auto_update = app.config.get("AUTO_UPDATE", False)
    if auto_update:
        init_file_list = app.config.get("DB_INIT_FILE")
        if init_file_list:
            update_table(db, db_schema, init_file_list)

    class BaseModel:
        """
        schema base model
        """
        __table_args__ = {'extend_existing': True, 'schema': db_schema}

    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)


def update_table(db, schema, init_file_list):
    """更新数据库到当前"""
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
            if schema_exist:
                db.engine.execute(sqlalchemy.schema.DropSchema(db_schema, cascade=True))
            db.engine.execute(sqlalchemy.schema.CreateSchema(db_schema))

            for file_path in init_file_list:
                run_sql(file_path, db, first_sql)
    finally:
        lock.release()


def run_sql(file_path, db, first_sql):
    # Create an empty command string
    db.session.execute(first_sql)

    sql_command = ''
    with open(file_path) as sql_file:

        # Iterate over all lines in the sql file
        for line in sql_file:
            # Ignore commented lines
            if not line.startswith('--') and line.strip('\n'):
                # Append line to the command string
                sql_command += " " + line.strip('\n')

                # If the command string ends with ';', it is a full statement
                if sql_command.endswith(';'):
                    # Try to execute statement and commit it
                    try:
                        db.session.execute(sqlalchemy.text(sql_command))
                        db.session.commit()

                    # Assert in case of error
                    except Exception as e:
                        raise Exception("脚本执行出差" + e.get("message"))

                    # Finally, clear command string
                    finally:
                        sql_command = ''
