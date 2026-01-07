# app.py (bổ sung routes cho Task Management)
from models import db, User, UserRole, Team, TaskColumn, Task
from middleware import token_required, role_required
from flask import request, jsonify
from sqlalchemy import func

# ==========================================
# HELPER: Kiểm tra quyền truy cập Team
# ==========================================
def check_team_access(user, team_id):
    # Logic: User phải là thành viên của Team (cần bảng team_members để check chuẩn xác)
    # Hoặc Lecturer phụ trách lớp chứa Team đó.
    # Ở đây giả lập check đơn giản:
    return True 

# ==========================================
# 1. API: Lấy dữ liệu Board (Columns + Tasks)
# ==========================================
@app.route('/api/teams/<int:team_id>/board', methods=['GET'])
@token_required
def get_team_board(current_user, team_id):
    # Check permission...
    
    columns = TaskColumn.query.filter_by(team_id=team_id).order_by(TaskColumn.position).all()
    # Nếu team chưa có cột nào, tạo mặc định
    if not columns:
        default_cols = ['To Do', 'In Progress', 'Done']
        for idx, name in enumerate(default_cols):
            col = TaskColumn(name=name, team_id=team_id, position=idx)
            db.session.add(col)
        db.session.commit()
        columns = TaskColumn.query.filter_by(team_id=team_id).order_by(TaskColumn.position).all()

    return jsonify([col.to_dict() for col in columns]), 200

# ==========================================
# 2. CRUD TASK
# ==========================================

# CREATE Task
@app.route('/api/tasks', methods=['POST'])
@token_required
@role_required([UserRole.STUDENT]) # Chỉ sinh viên tạo task
def create_task(current_user):
    data = request.get_json()
    column_id = data.get('column_id')
    
    # Tính toán position mới (đưa xuống cuối cột)
    max_pos = db.session.query(func.max(Task.position)).filter_by(column_id=column_id).scalar()
    new_pos = (max_pos + 1) if max_pos is not None else 0

    new_task = Task(
        title=data['title'],
        description=data.get('description', ''),
        column_id=column_id,
        creator_id=current_user.id,
        assignee_id=data.get('assignee_id'),
        position=new_pos
    )
    
    db.session.add(new_task)
    db.session.commit()
    return jsonify(new_task.to_dict()), 201

# UPDATE Task Content (Title, Description, Assignee)
@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@token_required
@role_required([UserRole.STUDENT])
def update_task_details(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    task.title = data.get('title', task.title)
    task.description = data.get('description', task.description)
    task.assignee_id = data.get('assignee_id', task.assignee_id)
    # Không update column/position ở đây
    
    db.session.commit()
    return jsonify(task.to_dict()), 200

# DELETE Task
@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@token_required
@role_required([UserRole.STUDENT])
def delete_task(current_user, task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'}), 200

# ==========================================
# 3. DRAG & DROP UPDATE (Quan trọng)
# Mô tả: Di chuyển task sang cột khác hoặc đảo thứ tự trong cột
# ==========================================
@app.route('/api/tasks/<int:task_id>/move', methods=['PUT'])
@token_required
@role_required([UserRole.STUDENT])
def move_task(current_user, task_id):
    """
    Payload nhận vào:
    {
        "target_column_id": 5,
        "new_position": 2
    }
    """
    task = Task.query.get_or_404(task_id)
    data = request.get_json()
    
    target_col_id = data.get('target_column_id')
    new_pos = data.get('new_position')
    
    if not target_col_id or new_pos is None:
        return jsonify({'message': 'Missing target column or position'}), 400

    old_col_id = task.column_id
    old_pos = task.position
    
    # Trường hợp 1: Di chuyển trong cùng một cột (Reorder)
    if old_col_id == target_col_id:
        if old_pos != new_pos:
            # Shift các task khác để nhường chỗ
            if old_pos < new_pos:
                # Kéo xuống dưới: Các task ở giữa giảm position đi 1
                tasks_to_shift = Task.query.filter(
                    Task.column_id == old_col_id,
                    Task.position > old_pos,
                    Task.position <= new_pos
                ).all()
                for t in tasks_to_shift:
                    t.position -= 1
            else:
                # Kéo lên trên: Các task ở giữa tăng position thêm 1
                tasks_to_shift = Task.query.filter(
                    Task.column_id == old_col_id,
                    Task.position >= new_pos,
                    Task.position < old_pos
                ).all()
                for t in tasks_to_shift:
                    t.position += 1
            
            task.position = new_pos

    # Trường hợp 2: Di chuyển sang cột khác
    else:
        # B1: Điều chỉnh cột cũ (Shift up các task nằm dưới task bị chuyển đi)
        old_col_tasks = Task.query.filter(
            Task.column_id == old_col_id,
            Task.position > old_pos
        ).all()
        for t in old_col_tasks:
            t.position -= 1
            
        # B2: Điều chỉnh cột mới (Shift down các task để lấy chỗ trống)
        new_col_tasks = Task.query.filter(
            Task.column_id == target_col_id,
            Task.position >= new_pos
        ).all()
        for t in new_col_tasks:
            t.position += 1
            
        # B3: Cập nhật task
        task.column_id = target_col_id
        task.position = new_pos

    db.session.commit()
    return jsonify({'message': 'Task moved successfully', 'task': task.to_dict()}), 200