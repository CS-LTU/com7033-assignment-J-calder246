from app2 import db;
from flask_login import UserMixin;

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    id_admin = db.Column(db.Boolean, default=False) #sets default to not admin

    def __repr__(self):
        return f"<User {self.username}>"
        