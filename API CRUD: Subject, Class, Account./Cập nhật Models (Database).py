# models.py (bổ sung)
from sqlalchemy import ForeignKey

# ... (Giữ nguyên User và UserRole ở phần trước) ...

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False) # Mã môn (VD: SE101)
    name = db.Column(db.String(100), nullable=False)
    syllabus_url = db.Column(db.String(255)) # Link file syllabus
    
    # Quan hệ: Một môn học có nhiều lớp
    classes = db.relationship('ClassRoom', backref='subject', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'syllabus_url': self.syllabus_url
        }

class ClassRoom(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # Tên lớp (VD: SE1701)
    
    # Khóa ngoại liên kết với Subject
    subject_id = db.Column(db.Integer, ForeignKey('subjects.id'), nullable=False)
    
    # Khóa ngoại liên kết với Lecturer (User có role Lecturer)
    lecturer_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=True)

    # Quan hệ: Lấy thông tin giảng viên
    lecturer = db.relationship('User', foreign_keys=[lecturer_id])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'lecturer_name': self.lecturer.username if self.lecturer else "Not Assigned"
        }