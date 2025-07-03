from flask import request, jsonify, current_app, g, url_for
from app.api import bp
from app.models import User
from app import db
import jwt
from datetime import datetime, timedelta, timezone
from app.api.auth import token_required
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

    # 检查用户名长度
    if len(username) > 15:
        return jsonify({'error': 'Username cannot exceed 15 characters'}), 400

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

@bp.route('/user/email', methods=['PUT'])
@token_required
def update_email():
    """更新用户邮箱"""
    user = g.current_user
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email in request body'}), 400

    new_email = data['email']
    if User.query.filter_by(email=new_email).first():
        return jsonify({'error': 'Email already in use'}), 400

    user.email = new_email
    db.session.commit()
    return jsonify({'message': 'Email updated successfully'}), 200

@bp.route('/user/password', methods=['PUT'])
@token_required
def update_password():
    """更新用户密码"""
    user = g.current_user
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'error': 'Missing current_password or new_password'}), 400

    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Invalid current password'}), 401

    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'}), 200

@bp.route('/users/<string:username>/profile', methods=['GET'])
@token_required
def get_user_profile(username):
    """获取指定用户的公开信息"""
    user = User.query.filter_by(username=username).first_or_404()
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email, # 注意：此处返回email，前端可以决定是否显示
        'is_online': user.is_online,
        'gender': user.gender,
        'age': user.age,
        'bio': user.bio,
        'avatar_url': url_for('static', filename=user.avatar_url, _external=True) if user.avatar_url else None
    })

@bp.route('/user/profile', methods=['PUT'])
@token_required
def update_profile():
    """更新当前用户的个人资料"""
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    # 使用.get()来安全地获取数据，如果不存在则保持原样
    user.gender = data.get('gender', user.gender)
    user.age = data.get('age', user.age)
    user.bio = data.get('bio', user.bio)

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@bp.route('/user/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """上传用户头像"""
    if 'avatar' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    file = request.files['avatar']
    if not file or not file.filename:
        return jsonify({'error': '未选择文件'}), 400
        
    if file and allowed_file(file.filename):
        user = g.current_user
        # 使用 secure_filename 保证文件名安全，并结合用户ID确保唯一性
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"user_{user.id}.{original_ext}")
        
        static_folder = current_app.static_folder
        if not static_folder:
            return jsonify({'error': 'Static folder not configured'}), 500

        avatar_dir = os.path.join(static_folder, 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        full_path = os.path.join(avatar_dir, filename)
        file.save(full_path)

        # 数据库中只保存相对于 static/avatars 的文件名
        db_avatar_path = f"avatars/{filename}"
        user.avatar_url = db_avatar_path
        db.session.commit()

        return jsonify({
            'message': '头像更新成功',
            'avatar_url': url_for('static', filename=db_avatar_path, _external=True)
        }), 200
    else:
        return jsonify({'error': '文件类型不被允许'}), 400