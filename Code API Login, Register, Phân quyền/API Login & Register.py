# app.py
from flask import Flask, request, jsonify
from models import db, User, UserRole
from middleware import token_required, role_required, SECRET_KEY
import jwt
import datetime

app = Flask(__name__)
# Cấu hình kết nối PostgreSQL 
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/collabsphere_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 1. API Đăng ký (Register)
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Kiểm tra user tồn tại
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400

    # Lấy role từ request hoặc mặc định là Student
    role_str = data.get('role', 'Student')
    try:
        # Map string sang Enum
        role_enum = UserRole(role_str)
    except ValueError:
        return jsonify({'message': 'Invalid role'}), 400

    new_user = User(
        username=data['username'],
        email=data['email'],
        role=role_enum
    )
    new_user.set_password(data['password'])
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User registered successfully'}), 201

# 2. API Đăng nhập (Login)
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not user.check_password(data.get('password')):
        return jsonify({'message': 'Invalid credentials'}), 401
        
    if not user.is_active:
        return jsonify({'message': 'Account is deactivated'}), 403

    # Tạo JWT Token
    token = jwt.encode({
        'user_id': user.id,
        'role': user.role.value,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({'token': token, 'user': user.to_dict()}), 200

# 3. Ví dụ API có Phân quyền (Protected Routes)

# API chỉ dành cho Admin (ví dụ: Deactivate account )
@app.route('/api/admin/users', methods=['GET'])
@token_required
@role_required([UserRole.ADMIN])
def get_all_users(current_user):
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200

# API dành cho Lecturer và Head Department (ví dụ: Approve Project )
@app.route('/api/projects/approve', methods=['POST'])
@token_required
@role_required([UserRole.HEAD_DEPARTMENT])
def approve_project(current_user):
    return jsonify({'message': f'Project approved by {current_user.role.value}'}), 200

# API dành cho Student (ví dụ: Submit Checkpoint [cite: 17])
@app.route('/api/student/submit', methods=['POST'])
@token_required
@role_required([UserRole.STUDENT])
def submit_checkpoint(current_user):
    return jsonify({'message': 'Checkpoint submitted successfully'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Tạo bảng nếu chưa có
    app.run(debug=True)