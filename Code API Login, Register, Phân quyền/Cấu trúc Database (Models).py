# models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import enum

db = SQLAlchemy()

# Định nghĩa các Role dựa trên tài liệu 
class UserRole(enum.Enum):
    ADMIN = 'Admin'
    HEAD_DEPARTMENT = 'Head Department'
    STAFF = 'Staff'
    LECTURER = 'Lecturer'
    STUDENT = 'Student'

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = db.Column(db.Boolean, default=True) # Admin có quyền deactivate 

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role.value
        }