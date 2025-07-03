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
    """检查上传的文件扩展名是否在允许的范围内"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 检查服务器是否运行
@bp.route('/ping')
def ping():
    """一个简单的服务健康检查接口，如果服务器正常运行，则返回 "Pong!" """
    return "Pong!"

@bp.route('/register', methods=['POST'])
def register():
    """
    用户注册接口。这是一个公开接口，无需认证。
    请求体JSON参数:
        - username (string): 用户名
        - email (string): 邮箱
        - password (string): 密码
    业务逻辑:
        1. 验证请求数据格式和必填字段。
        2. 检查用户名长度、用户名和邮箱是否已被占用。
        3. 创建新用户实例，对密码进行哈希加盐处理后存入数据库。
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # 验证关键字段是否存在
    if not username or not email or not password:
        return jsonify({'error': 'Missing username, email, or password'}), 400

    # 验证用户名长度
    if len(username) > 15:
        return jsonify({'error': 'Username cannot exceed 15 characters'}), 400

    # 检查用户名是否已存在，保证唯一性
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    # 检查邮箱是否已被注册，保证唯一性
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    # 创建用户对象
    user = User(username=username, email=email)
    # 调用模型中的方法设置密码，该方法会进行哈希处理
    user.set_password(password)
    # 将新用户添加到数据库会话并提交
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    """
    用户登录接口。这是一个公开接口。
    请求体JSON参数:
        - username (string): 用户名
        - password (string): 密码
        - port (int, optional): 客户端用于P2P通信的端口号
    业务逻辑:
        1. 验证用户名和密码。
        2. 如果验证成功，更新用户在数据库中的IP地址和端口号。
        3. 生成一个包含用户ID和过期时间的JWT。
    返回:
        - 成功: 返回JWT。
        - 失败: 返回401 Unauthorized错误。
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    # 从数据库查找用户
    user = User.query.filter_by(username=username).first()
    # 验证用户是否存在，并使用模型中的方法检查密码哈希值是否匹配
    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # 登录成功后，更新用户的IP地址和端口信息，用于P2P通信
    user.ip_address = request.remote_addr # remote_addr是请求来源的IP
    port = data.get('port')
    if port:
        user.port = port
    db.session.commit()

    # 生成JWT，有效期设置为24小时
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24) # 设置过期时间
        },
        current_app.config['SECRET_KEY'],  # 使用在应用配置中设置的密钥进行签名
        algorithm='HS256' # 指定签名算法
    )

    return jsonify({'token': token})

@bp.route('/keys', methods=['POST'])
@token_required
def upload_key():
    """
    上传用户的RSA公钥，用于后续的端到端加密密钥协商。
    请求体JSON参数:
        - public_key (string): 用户的RSA公钥字符串。
    """
    data = request.get_json()
    if not data or 'public_key' not in data:
        return jsonify({'error': 'Missing public_key in request body'}), 400
    
    # g.current_user 由 @token_required 装饰器提供
    user = g.current_user
    user.public_key = data['public_key']
    db.session.commit()
    
    return jsonify({'message': 'Public key updated successfully'}), 200

@bp.route('/users/<string:username>/public_key', methods=['GET'])
@token_required
def get_public_key(username):
    """获取指定用户的公钥，用于加密通信的发起方。"""
    # first_or_404: 如果找不到用户，会自动返回404错误
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
    """更新当前登录用户的邮箱地址。"""
    user = g.current_user
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Missing email in request body'}), 400

    new_email = data['email']
    # 检查新邮箱是否已被其他用户占用
    if User.query.filter_by(email=new_email).first():
        return jsonify({'error': 'Email already in use'}), 400

    user.email = new_email
    db.session.commit()
    return jsonify({'message': 'Email updated successfully'}), 200

@bp.route('/user/password', methods=['PUT'])
@token_required
def update_password():
    """更新当前登录用户的密码。"""
    user = g.current_user
    data = request.get_json()
    if not data or 'current_password' not in data or 'new_password' not in data:
        return jsonify({'error': 'Missing current_password or new_password'}), 400

    # 验证当前密码是否正确
    if not user.check_password(data['current_password']):
        return jsonify({'error': 'Invalid current password'}), 401

    # 设置新密码（同样会经过哈希处理）
    user.set_password(data['new_password'])
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'}), 200

@bp.route('/users/<string:username>/profile', methods=['GET'])
@token_required
def get_user_profile(username):
    """获取指定用户的公开个人资料。"""
    user = User.query.filter_by(username=username).first_or_404()
    # 返回用户的公开信息
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email, # 注意：此处返回email，前端可以根据需要决定是否对非好友隐藏
        'is_online': user.is_online,
        'gender': user.gender,
        'age': user.age,
        'bio': user.bio,
        # 生成完整的头像URL
        'avatar_url': url_for('static', filename=user.avatar_url, _external=True) if user.avatar_url else None
    })

@bp.route('/user/profile', methods=['PUT'])
@token_required
def update_profile():
    """更新当前用户的个人资料（性别、年龄、简介）。"""
    user = g.current_user
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    # 使用 .get(key, default) 方法安全地获取数据。
    # 如果请求中不包含某个字段，则保持数据库中原有的值不变。
    user.gender = data.get('gender', user.gender)
    user.age = data.get('age', user.age)
    user.bio = data.get('bio', user.bio)

    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@bp.route('/user/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """
    上传或更新当前用户的头像。
    请求为 multipart/form-data 类型。
    表单字段名:
        - avatar: 包含图片文件的字段。
    """
    # 检查请求中是否包含文件部分
    if 'avatar' not in request.files:
        return jsonify({'error': '没有文件部分'}), 400
    file = request.files['avatar']
    # 检查是否选择了文件
    if not file or not file.filename:
        return jsonify({'error': '未选择文件'}), 400
        
    # 检查文件类型是否合法
    if file and allowed_file(file.filename):
        user = g.current_user
        # 使用 secure_filename 清理文件名，防止不安全字符。
        # 然后结合用户ID和原始扩展名构造一个唯一的、安全的新文件名，避免冲突和覆盖。
        original_ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"user_{user.id}.{original_ext}")
        
        # 获取static文件夹的绝对路径
        static_folder = current_app.static_folder
        if not static_folder:
            # 这是一个服务器配置问题
            return jsonify({'error': 'Static folder not configured'}), 500

        # 构造头像存储的完整目录路径
        avatar_dir = os.path.join(static_folder, 'avatars')
        # 确保目录存在，如果不存在则创建它
        os.makedirs(avatar_dir, exist_ok=True)
        
        # 构造文件的完整保存路径
        full_path = os.path.join(avatar_dir, filename)
        # 保存文件到服务器
        file.save(full_path)

        # 在数据库中只保存相对于avatars目录的相对路径，便于管理
        db_avatar_path = f"avatars/{filename}"
        user.avatar_url = db_avatar_path
        db.session.commit()

        return jsonify({
            'message': '头像上传成功',
            # 返回新的头像URL，方便前端立即更新显示
            'avatar_url': url_for('static', filename=db_avatar_path, _external=True)
        }), 200
    else:
        # 如果文件类型不被允许
        return jsonify({'error': '文件类型不被允许'}), 400