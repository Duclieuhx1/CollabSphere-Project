# models.py (bổ sung)
import enum
from datetime import datetime

# ... (Giữ nguyên các model User, Subject, ClassRoom cũ) ...

class ProjectStatus(enum.Enum):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    DENIED = 'Denied'

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    objectives = db.Column(db.Text) # Mục tiêu dự án
    status = db.Column(db.Enum(ProjectStatus), default=ProjectStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # FK: Dự án thuộc về môn học nào
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    # FK: Giảng viên nào tạo
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Quan hệ
    milestones = db.relationship('ProjectMilestone', backref='project', cascade="all, delete-orphan")
    subject = db.relationship('Subject')
    owner = db.relationship('User')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject.code if self.subject else None,
            'owner': self.owner.username,
            'status': self.status.value,
            'milestones': [m.to_dict() for m in self.milestones]
        }

class ProjectMilestone(db.Model):
    __tablename__ = 'project_milestones'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # Ví dụ: Sprint 1, Design Phase
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

# Cập nhật ClassRoom để thêm trường project_id (Lớp đang chạy dự án nào)
# Lưu ý: Cần migrate DB nếu đang chạy thực tế
# class ClassRoom(db.Model):
#     ...
#     current_project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True)
#     current_project = db.relationship('Project')