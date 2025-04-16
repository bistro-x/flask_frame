from src.flask_frame.extension.database import db

class Permission(db.Model):
    __tablename__ = 'permission'
    __table_args__ = {'extend_existing': True, 'schema': "user_auth"}

    key = db.Column(db.Text, primary_key=True)
