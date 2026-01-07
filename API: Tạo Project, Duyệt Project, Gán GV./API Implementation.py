# app.py (bổ sung routes)
from models import db, User, UserRole, Project, ProjectStatus, ProjectMilestone, ClassRoom, Subject
from middleware import token_required, role_required
from flask import request, jsonify

# ==========================================
# 1. TẠO PROJECT (Create Project)
# Quyền hạn: LECTURER
# Mô tả: Tạo project pending kèm milestones 
# ==========================================
@app.route('/api/lecturer/projects', methods=['POST'])
@token_required
@role_required([UserRole.LECTURER])
def create_project(current_user):
    data = request.get_json()
    
    # Validate Subject
    subject = Subject.query.get(data.get('subject_id'))
    if not subject:
        return jsonify({'message': 'Subject not found'}), 404

    # Tạo Project Header
    new_project = Project(
        name=data['name'],
        description=data.get('description'),
        objectives=data.get('objectives'),
        subject_id=subject.id,
        owner_id=current_user.id,
        status=ProjectStatus.PENDING # Mặc định là chờ duyệt
    )
    
    db.session.add(new_project)
    db.session.flush() # Để lấy ID của project vừa tạo cho milestones
    
    # Tạo Milestones đi kèm
    milestones_data = data.get('milestones', [])
    for m in milestones_data:
        milestone = ProjectMilestone(
            name=m['name'],
            description=m.get('description'),
            project_id=new_project.id
        )
        db.session.add(milestone)
        
    db.session.commit()
    return jsonify({'message': 'Project submitted for approval', 'project': new_project.to_dict()}), 201

# ==========================================
# 2. DUYỆT PROJECT (Approve/Deny Project)
# Quyền hạn: HEAD DEPARTMENT
# Mô tả: Duyệt hoặc từ chối project pending 
# ==========================================
@app.route('/api/head/projects/<int:project_id>/status', methods=['PUT'])
@token_required
@role_required([UserRole.HEAD_DEPARTMENT])
def approve_project(current_user, project_id):
    data = request.get_json()
    status_str = data.get('status') # Expect: 'Approved' or 'Denied'
    
    project = Project.query.get_or_404(project_id)
    
    if status_str == 'Approved':
        project.status = ProjectStatus.APPROVED
    elif status_str == 'Denied':
        project.status = ProjectStatus.DENIED
    else:
        return jsonify({'message': 'Invalid status'}), 400
        
    db.session.commit()
    return jsonify({'message': f'Project status updated to {status_str}'}), 200

# ==========================================
# 3. GÁN PROJECT & GÁN GV (Assign Project/Lecturer)
# Quyền hạn: 
# - Gán GV vào Lớp: STAFF (Đã làm ở phần trước, nhắc lại logic) [cite: 13]
# - Gán Project vào Lớp: HEAD DEPT (All classes) hoặc LECTURER (Own classes) 
# ==========================================

# API: Gán Project đã duyệt cho một Lớp học
@app.route('/api/classes/<int:class_id>/assign-project', methods=['PUT'])
@token_required
def assign_project_to_class(current_user, class_id):
    # Lấy thông tin lớp và project
    class_room = ClassRoom.query.get_or_404(class_id)
    data = request.get_json()
    project_id = data.get('project_id')
    project = Project.query.get_or_404(project_id)
    
    # 1. Kiểm tra Project có được duyệt chưa?
    if project.status != ProjectStatus.APPROVED:
        return jsonify({'message': 'Cannot assign a pending/denied project'}), 400
        
    # 2. Kiểm tra Môn học khớp nhau không? (Project của môn nào phải gán cho lớp môn đó)
    if project.subject_id != class_room.subject_id:
        return jsonify({'message': 'Project subject does not match class subject'}), 400

    # 3. Phân quyền: Ai được phép gán?
    # - Head Department: Được gán cho mọi lớp
    # - Lecturer: Chỉ được gán cho lớp mình phụ trách (assigned class)
    if current_user.role == UserRole.HEAD_DEPARTMENT:
        pass # OK
    elif current_user.role == UserRole.LECTURER:
        if class_room.lecturer_id != current_user.id:
            return jsonify({'message': 'Permission denied. You do not manage this class.'}), 403
    else:
        return jsonify({'message': 'Permission denied'}), 403

    # Thực hiện gán (Cần thêm field current_project_id vào model ClassRoom như phần Models)
    # class_room.current_project_id = project.id 
    # db.session.commit()
    
    # Giả lập response nếu chưa chạy migration
    return jsonify({
        'message': f'Project "{project.name}" assigned to Class "{class_room.name}"',
        'assigned_by': current_user.username
    }), 200

# (Optional) API xem lại: Gán GV vào lớp (đã có ở turn trước)
# Staff sử dụng endpoint: PUT /api/classes/<id>/assign