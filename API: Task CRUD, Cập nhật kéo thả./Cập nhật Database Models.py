# models.py (bổ sung)
from datetime import datetime

# ... (Giữ nguyên các model User, Team cũ) ...

class TaskColumn(db.Model):
    __tablename__ = 'task_columns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False) # VD: Backlog, To Do, Doing, Done
    position = db.Column(db.Integer, default=0) # Thứ tự hiển thị cột
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False) # Mỗi team có board riêng
    
    # Quan hệ: Một cột chứa nhiều task
    tasks = db.relationship('Task', backref='column', lazy=True, order_by='Task.position')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'position': self.position,
            'tasks': [t.to_dict() for t in self.tasks] # Nested tasks để frontend dễ render board
        }

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    position = db.Column(db.Integer, default=0) # Thứ tự trong cột (cho việc kéo thả)
    due_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Khóa ngoại
    column_id = db.Column(db.Integer, db.ForeignKey('task_columns.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Người được giao việc
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'position': self.position,
            'column_id': self.column_id,
            'assignee_id': self.assignee_id,
            'due_date': self.due_date.isoformat() if self.due_date else None
        }