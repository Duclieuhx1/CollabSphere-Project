# app.py (bổ sung các routes)
from models import db, User, UserRole, Subject, ClassRoom
from middleware import token_required, role_required
from flask import request, jsonify

# ==========================================
# 1. SUBJECT APIs (Quản lý Môn học)
# Quyền hạn: Chỉ STAFF mới được thêm/sửa/xóa [cite: 12]
# ==========================================

@app.route('/api/subjects', methods=['POST'])
@token_required
@role_required([UserRole.STAFF])
def create_subject(current_user):
    data = request.get_json()
    # Staff có thể import file để tạo, ở đây mô phỏng tạo bằng JSON
    new_subject = Subject(
        code=data['code'],
        name=data['name'],
        syllabus_url=data.get('syllabus_url', '')
    )
    db.session.add(new_subject)
    db.session.commit()
    return jsonify({'message': 'Subject created successfully', 'subject': new_subject.to_dict()}), 201

@app.route('/api/subjects', methods=['GET'])
@token_required
def get_subjects(current_user):
    # Head Department, Staff, Lecturer, Student đều có thể cần xem danh sách môn
    subjects = Subject.query.all()
    return jsonify([sub.to_dict() for sub in subjects]), 200

@app.route('/api/subjects/<int:id>', methods=['PUT'])
@token_required
@role_required([UserRole.STAFF])
def update_subject(current_user, id):
    subject = Subject.query.get_or_404(id)
    data = request.get_json()
    
    subject.code = data.get('code', subject.code)
    subject.name = data.get('name', subject.name)
    subject.syllabus_url = data.get('syllabus_url', subject.syllabus_url)
    
    db.session.commit()
    return jsonify({'message': 'Subject updated', 'subject': subject.to_dict()}), 200

@app.route('/api/subjects/<int:id>', methods=['DELETE'])
@token_required
@role_required([UserRole.STAFF])
def delete_subject(current_user, id):
    subject = Subject.query.get_or_404(id)
    db.session.delete(subject)
    db.session.commit()
    return jsonify({'message': 'Subject deleted'}), 200

# ==========================================
# 2. CLASS APIs (Quản lý Lớp học)
# Quyền hạn: STAFF tạo lớp và gán giảng viên [cite: 15]
# ==========================================

@app.route('/api/classes', methods=['POST'])
@token_required
@role_required([UserRole.STAFF])
def create_class(current_user):
    data = request.get_json()
    
    # Kiểm tra subject tồn tại
    subject = Subject.query.get(data['subject_id'])
    if not subject:
        return jsonify({'message': 'Subject not found'}), 404

    new_class = ClassRoom(
        name=data['name'],
        subject_id=data['subject_id'],
        lecturer_id=data.get('lecturer_id') # Có thể gán giảng viên ngay hoặc sau này
    )
    db.session.add(new_class)
    db.session.commit()
    return jsonify({'message': 'Class created successfully', 'class': new_class.to_dict()}), 201

@app.route('/api/classes/<int:id>/assign', methods=['PUT'])
@token_required
@role_required([UserRole.STAFF])
def assign_lecturer_to_class(current_user, id):
    # Staff gán giảng viên vào lớp 
    class_room = ClassRoom.query.get_or_404(id)
    data = request.get_json()
    
    lecturer_id = data.get('lecturer_id')
    lecturer = User.query.filter_by(id=lecturer_id, role=UserRole.LECTURER).first()
    
    if not lecturer:
        return jsonify({'message': 'Lecturer not found or invalid role'}), 400
        
    class_room.lecturer_id = lecturer.id
    db.session.commit()
    return jsonify({'message': f'Assigned {lecturer.username} to class {class_room.name}'}), 200

# ==========================================
# 3. ACCOUNT APIs (Quản lý Tài khoản)
# Quyền hạn: ADMIN (View All/Deactivate), STAFF (Manage Lecturer/Student)
# ==========================================

# ADMIN: Xem tất cả tài khoản (Head, Staff, Lecturer, Student) 
@app.route('/api/admin/accounts', methods=['GET'])
@token_required
@role_required([UserRole.ADMIN])
def get_all_accounts(current_user):
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

# ADMIN: Deactivate tài khoản user 
@app.route('/api/admin/accounts/<int:id>/deactivate', methods=['PUT'])
@token_required
@role_required([UserRole.ADMIN])
def deactivate_account(current_user, id):
    user = User.query.get_or_404(id)
    user.is_active = False
    db.session.commit()
    return jsonify({'message': f'User {user.username} has been deactivated'}), 200

# STAFF: Chỉ xem và quản lý tài khoản Lecturer và Student [cite: 26]
@app.route('/api/staff/accounts', methods=['GET'])
@token_required
@role_required([UserRole.STAFF])
def get_managed_accounts(current_user):
    # Staff view list of lecturer/student accounts
    users = User.query.filter(User.role.in_([UserRole.LECTURER, UserRole.STUDENT])).all()
    return jsonify([u.to_dict() for u in users]), 200

# STAFF: Tạo tài khoản Lecturer/Student (Giả lập import file) 
@app.route('/api/staff/accounts', methods=['POST'])
@token_required
@role_required([UserRole.STAFF])
def create_managed_account(current_user):
    data = request.get_json()
    
    role_str = data.get('role')
    if role_str not in ['Lecturer', 'Student']:
         return jsonify({'message': 'Staff can only create Lecturer or Student accounts'}), 403

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        role=UserRole(role_str)
    )
    new_user.set_password(data['password']) # Trong thực tế, có thể auto-generate password và gửi email
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': f'{role_str} account created successfully'}), 201