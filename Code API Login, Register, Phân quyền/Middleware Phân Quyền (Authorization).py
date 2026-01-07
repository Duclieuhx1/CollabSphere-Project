# middleware.py
from functools import wraps
from flask import request, jsonify
import jwt
from models import User, UserRole

SECRET_KEY = "your_secret_key_here" # Nên để trong biến môi trường

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Lấy token từ header Authorization: Bearer <token>
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
            
        return f(current_user, *args, **kwargs)
    return decorated

# Decorator kiểm tra quyền cụ thể
def role_required(required_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in required_roles:
                return jsonify({'message': 'Permission denied!'}), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator