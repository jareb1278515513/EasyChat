from flask import jsonify, g
from flask_socketio import disconnect
from app.api import bp
from app.api.auth import admin_required
from app.models import User
from app.socket_events import get_sid_by_username
from app import socketio, db

# 定义管理员操作的API端点

@bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """
    [管理员] 获取系统中所有用户的列表。
    
    权限要求:
        - 必须是管理员（由 @admin_required 装饰器保证）。
    返回数据:
        - 一个包含所有用户信息的JSON数组。每个用户信息包括ID、用户名、邮箱、
          在线状态、IP地址和是否为管理员的标志。
    安全考虑:
        - 此接口仅返回公开或半公开的用户数据，不会泄露密码哈希等敏感信息。
    """
    # 从数据库中查询所有用户
    users = User.query.all()
    # 构建包含用户信息的字典列表，并将其转换为JSON响应
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_online': user.is_online,
        'ip_address': user.ip_address,
        'is_admin': user.is_admin
    } for user in users])

@bp.route('/admin/users/<string:username>/disconnect', methods=['POST'])
@admin_required
def disconnect_user(username):
    """
    [管理员] 强制将指定用户踢下线。
    
    路径参数:
        - username: 要强制下线的用户的用户名。
    业务逻辑:
        1. 查找目标用户是否存在。
        2. 检查用户是否真的在线。
        3. 如果在线，获取其对应的Socket.IO会话ID (SID)。
        4. 调用 `disconnect()` 函数强制关闭其WebSocket连接。
        5. 处理数据库状态与实时会话状态不一致的边缘情况。
    返回:
        - 200 OK: 操作成功或用户本就离线。
        - 404 Not Found: 目标用户不存在。
        - 500 Internal Server Error: 出现状态不一致的错误，但已尝试纠正。
    """
    # 根据用户名查找要操作的用户
    user_to_disconnect = User.query.filter_by(username=username).first()
    if not user_to_disconnect:
        # 如果用户不存在，返回404错误
        return jsonify({'error': 'User not found'}), 404
        
    # 如果数据库记录显示用户已离线，直接返回成功信息
    if not user_to_disconnect.is_online:
        return jsonify({'message': 'User is already offline'}), 200

    # 从内存中的在线用户字典里获取用户的SID
    sid = get_sid_by_username(username)
    if sid:
        # 如果找到了SID，说明用户当前有活跃的Socket.IO连接
        # 调用disconnect会触发 socket_events.py 中的 'disconnect' 事件处理器，
        # 该处理器会负责清理工作（如更新数据库中的在线状态）。
        # 注意：由于这是在一个HTTP请求上下文中调用，必须明确指定命名空间'/'。
        disconnect(sid, namespace='/')
        return jsonify({'message': f'Disconnect signal sent to {username}.'}), 200
    else:
        # 边缘情况处理：数据库显示用户在线，但在Socket.IO的会话中找不到他。
        # 这可能意味着上次非正常断开连接时，清理工作未能完成。
        # 这里主动纠正数据库中的状态，确保数据一致性。
        user_to_disconnect.is_online = False
        db.session.commit()
        return jsonify({'error': 'User is online in DB but not found in socket session. Status corrected.'}), 500

@bp.route('/admin/users/<string:username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """
    [管理员] 从系统中永久删除一个用户。
    
    路径参数:
        - username: 要删除的用户的用户名。
    业务逻辑:
        1. 防止管理员删除自己。
        2. 查找目标用户是否存在。
        3. 从数据库中删除该用户记录。
    """
    # g.current_user 是由 @admin_required 装饰器设置的当前管理员用户
    current_admin = g.current_user
    # 管理员不能删除自己，以防意外操作导致系统无法管理
    if current_admin.username == username:
        return jsonify({'error': 'Admin cannot delete themselves'}), 400

    # 查找要删除的用户
    user_to_delete = User.query.filter_by(username=username).first()
    if not user_to_delete:
        # 如果用户不存在，返回404错误
        return jsonify({'error': 'User not found'}), 404

    # 执行删除操作
    # 注意：由于我们在 User 模型中为相关的好友关系和好友请求设置了级联删除(cascade="all, delete-orphan")，
    # 所以在删除用户时，SQLAlchemy会自动删除所有与该用户相关的记录，无需手动清理。
    db.session.delete(user_to_delete)
    db.session.commit()

    return jsonify({'message': f'User {username} has been deleted successfully.'}), 200 