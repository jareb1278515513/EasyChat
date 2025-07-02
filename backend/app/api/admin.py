from flask import jsonify, g
from flask_socketio import disconnect
from app.api import bp
from app.api.auth import admin_required
from app.models import User
from app.socket_events import get_sid_by_username
from app import socketio, db

@bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """[管理员]获取所有用户信息
    权限要求:
        - 管理员权限(通过admin_required装饰器验证)
    返回数据:
        - 用户ID、用户名、邮箱
        - 在线状态、IP地址
        - 管理员标志
    安全考虑:
        - 仅返回必要信息，不包含敏感数据如密码哈希
    """
    users = User.query.all()
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
    """[管理员]强制断开用户连接
    路径参数:
        - username: 目标用户名
    业务逻辑:
        1. 验证目标用户存在
        2. 检查用户当前在线状态
        3. 通过WebSocket强制断开连接
        4. 处理状态不一致情况(DB与WebSocket会话不同步)
    返回:
        - 200: 操作成功
        - 404: 用户不存在
        - 500: 状态不一致
    """
    user_to_disconnect = User.query.filter_by(username=username).first()
    if not user_to_disconnect:
        return jsonify({'error': 'User not found'}), 404
        
    if not user_to_disconnect.is_online:
        return jsonify({'message': 'User is already offline'}), 200

    sid = get_sid_by_username(username)
    if sid:
        # This will trigger the 'disconnect' event handler in socket_events.py
        # We must specify the namespace, as this is called from an HTTP request context
        disconnect(sid, namespace='/')
        return jsonify({'message': f'Disconnect signal sent to {username}.'}), 200
    else:
        # This case might happen if the in-memory map is out of sync with the DB
        # Forcing DB state to be correct
        user_to_disconnect.is_online = False
        db.session.commit()
        return jsonify({'error': 'User is online in DB but not found in socket session. Status corrected.'}), 500

@bp.route('/admin/users/<string:username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """[管理员]删除用户"""
    current_admin = g.current_user
    if current_admin.username == username:
        return jsonify({'error': 'Admin cannot delete themselves'}), 400

    user_to_delete = User.query.filter_by(username=username).first()
    if not user_to_delete:
        return jsonify({'error': 'User not found'}), 404

    # 由于在User模型中配置了级联删除，
    # 删除用户时，与之相关的好友关系和好友请求将自动被清理。
    db.session.delete(user_to_delete)
    db.session.commit()

    return jsonify({'message': f'User {username} has been deleted successfully.'}), 200 