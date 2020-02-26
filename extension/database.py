from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

db = None
db_schema = "public"
BaseModel = None
AutoMapModel = None


def init_app(app):
    global db, db_schema, BaseModel, AutoMapModel
    db_schema = app.config.get("DB_SCHEMA")

    class BaseModel:
        """
        schema base model
        """
        __table_args__ = {'extend_existing': True, 'schema': db_schema}

    db = SQLAlchemy(app)
    db.Model.metadata.reflect(bind=db.engine, schema=db_schema)
