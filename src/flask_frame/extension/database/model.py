from . import BaseModel, db, db_schema



class Param(BaseModel, db.Model):
    __tablename__ = "param"
    __table_args__ = {"extend_existing": True, "schema": db_schema}
    id = db.Column(db.Integer, primary_key=True)
