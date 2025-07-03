from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from app.models import User

def token_required(f):
    """JWT认证装饰器
    
    功能:
        1. 从请求头 'Authorization' 中获取JWT。
        2. 解码并验证JWT的有效性（包括签名和过期时间）。
        3. 从JWT负载中获取用户ID，并查询数据库确认用户存在。
        4. 将查询到的当前用户对象存储在Flask的全局对象 `g` 中，以便后续的视图函数使用。
        
    异常处理:
        - 返回 401 Unauthorized: 如果token缺失、格式错误、签名无效、已过期或token中包含的用户不存在。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. 从 'Authorization' 请求头中获取token
        token = None
        # 标准的JWT认证请求头格式为 'Bearer <token>'
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # 从 'Bearer ' 字符串后提取token本身
            token = auth_header.split(' ')[1]

        # 如果请求头中没有token，则返回错误
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # 2. 解码并验证JWT
            # 使用在Flask应用配置中定义的SECRET_KEY和HS256算法进行解码
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            # 3. 从解码后的数据中获取用户ID，并查询数据库
            g.current_user = User.query.get(data['user_id'])
            # 如果根据ID找不到对应的用户，也视为token无效
            if not g.current_user:
                 return jsonify({'message': 'Token is invalid!'}), 401
        except jwt.ExpiredSignatureError:
            # token已过期
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            # token签名无效或格式错误
            return jsonify({'message': 'Token is invalid!'}), 401
        
        # 4. 所有验证通过，执行被装饰的原始视图函数
        return f(*args, **kwargs)

    return decorated

def admin_required(f):
    """管理员权限验证装饰器
    
    这个装饰器依赖于 `token_required` 的逻辑，首先验证用户是否已登录，
    然后额外检查该用户是否具有管理员权限。
    
    额外功能:
        1. 在通过token验证后，进一步检查用户的 `is_admin` 属性。
        
    异常处理:
        - 继承 `token_required` 的所有401错误。
        - 返回 403 Forbidden: 如果用户已登录但不是管理员。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # --- 这部分逻辑与 token_required 完全相同，用于验证用户身份 ---
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
        # --- 身份验证结束 ---

        # 额外检查管理员权限
        if not g.current_user.is_admin:
            # 如果用户不是管理员，返回403权限不足错误
            return jsonify({'message': 'Administrator access required!'}), 403
        
        # 验证通过，执行被装饰的函数
        return f(*args, **kwargs)

    return decorated