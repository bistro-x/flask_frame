from ..database import BaseModel, db, db_schema


class ApiLog(BaseModel, db.Model):
    __tablename__ = "api_log"
    __table_args__ = {"extend_existing": True, "schema": db_schema}
    id = db.Column(db.Integer, primary_key=True)
