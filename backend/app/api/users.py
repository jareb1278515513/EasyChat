from flask import request, jsonify, current_app, g
from app.api import bp
from app.models import User
from app import db
import jwt
from datetime import datetime, timedelta, timezone
from app.api.auth import token_required

# 检查服务器是否运行
@bp.route('/ping')
def ping():
    """简单检查接口，服务器正常运行则返回Pong!"""
    return "Pong!"

@bp.route('/register', methods=['POST'])
def register():
    """用户注册接口
    请求参数:
        - username: 用户名
        - email: 邮箱
        - password: 密码
    返回:
        - 成功: 201状态码和成功消息
        - 失败: 400状态码和错误原因
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 检查必填字段
    if not username or not email or not password:
        return jsonify({'error': 'Missing username, email, or password'}), 400

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    # 检查邮箱是否已注册
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    # 创建新用户并保存到数据库
    user = User(username=username, email=email)
    user.set_password(password)  # 密码会经过bcrypt加盐哈希处理
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    """用户登录接口
    请求参数:
        - username: 用户名
        - password: 密码
        - ip_address: 用户客户端IP地址
        - port: 用户客户端端口号
    返回:
        - 成功: JWT令牌
        - 失败: 401状态码和错误原因
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # 验证用户凭证
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # 更新用户登录信息(IP和端口)
    user.ip_address = request.remote_addr
    port = data.get('port')
    if port:
        user.port = port
    db.session.commit()

    # 生成JWT令牌(有效期24小时)
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        },
        current_app.config['SECRET_KEY'],  # 使用应用密钥签名
        algorithm='HS256'
    )

    return jsonify({'token': token})

@bp.route('/keys', methods=['POST'])
@token_required
def upload_key():
    """上传用户公钥接口
    请求参数:
        - public_key: 用户的RSA公钥
    返回:
        - 成功: 200状态码和成功消息
        - 失败: 400状态码和错误原因
    """
    data = request.get_json()
    if not data or 'public_key' not in data:
        return jsonify({'error': 'Missing public_key in request body'}), 400
    
    # 从JWT令牌中获取当前用户
    user = g.current_user
    user.public_key = data['public_key']
    db.session.commit()
    
    return jsonify({'message': 'Public key updated successfully'}), 200

@bp.route('/users/<string:username>/public_key', methods=['GET'])
@token_required
def get_public_key(username):
    """获取指定用户的公钥
    路径参数:
        - username: 目标用户名
    返回:
        - 成功: 用户ID、用户名和公钥
        - 失败: 404状态码和错误原因
    """
    user = User.query.filter_by(username=username).first_or_404()
    if not user.public_key:
        return jsonify({'error': 'User has not uploaded a public key'}), 404
        
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'public_key': user.public_key
    })