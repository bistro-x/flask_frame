import json

from flask_sqlalchemy import SQLAlchemy

db = None
db_schema = "public"
BaseModel = None
AutoMapModel = None


def json_dumps(*data, **kwargs):
    return json.dumps(*data, ensure_ascii=False, **kwargs)


def init_app(app):
    global db, db_schema, BaseModel, AutoMapModel
    db_schema = app.config.get("DB_SCHEMA")

    class BaseModel:
        """
        schema base model
        """
        __table_args__ = {'extend_existing': True, 'schema': db_schema}

    db = SQLAlchemy(app, engine_options={
        "json_serializer": json_dumps, "pool_size": 20, "max_overflow": 30
    })
    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)
