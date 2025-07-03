from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from app.models import User

def token_required(f):
    """JWT认证装饰器
    功能:
        1. 从Authorization头获取token
        2. 验证token有效性
        3. 验证用户是否存在
        4. 将当前用户存入g对象
    异常处理:
        - 401: token缺失/过期/无效
        - 401: 用户不存在
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            g.current_user = User.query.get(data['user_id'])
            if not g.current_user:
                 return jsonify({'message': 'Token is invalid!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    """管理员权限装饰器(继承自token_required函数)
    额外功能:
        1. 验证用户is_admin标志
    异常处理:
        - 403: 非管理员用户
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            g.current_user = User.query.get(data['user_id'])
            if not g.current_user:
                return jsonify({'message': 'Token is invalid!'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401

        
        if not g.current_user.is_admin:
            return jsonify({'message': 'Administrator access required!'}), 403
        
        return f(*args, **kwargs)

    return decorated