from flask import jsonify, g
from app.api import bp
from app.api.auth import token_required
from app.models import User

@bp.route('/users/<string:username>/info', methods=['GET'])
@token_required
def get_user_info(username):
    """
    获取指定用户的在线状态和P2P连接信息（IP地址和端口）。
    这是建立P2P聊天前，客户端必须调用的信令(Signaling)接口之一。
    
    路径参数:
        - username (string): 目标用户的用户名。
        
    权限要求:
        - 请求者必须是目标用户本人，或者是目标用户的好友。
        - 这是为了保护用户的IP地址不被泄露给无关的第三方。
        
    返回:
        - 如果用户在线且权限验证通过：包含用户名、在线状态、IP和端口的JSON。
        - 如果用户离线：只包含用户名和在线状态为false的JSON。
        
    错误响应:
        - 404 Not Found: 如果目标用户不存在。
        - 403 Forbidden: 如果请求者不是目标用户的好友。
    """
    # g.current_user 由 @token_required 装饰器提供
    current_user = g.current_user
    # 根据路径参数中的用户名查找目标用户
    target_user = User.query.filter_by(username=username).first()

    # 如果在数据库中找不到该用户，返回404错误
    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # --- 关键的权限检查 ---
    # 只有用户自己或者他的好友才能查询其详细连接信息。
    # `current_user.is_friend(target_user)` 是在 User 模型中定义的方法。
    if target_user.id != current_user.id and not current_user.is_friend(target_user):
        return jsonify({'error': 'Access denied: you can only view info for your friends.'}), 403

    # 如果目标用户当前是离线状态
    if not target_user.is_online:
        # 只返回安全的、非敏感的基本信息
        return jsonify({
            'username': target_user.username,
            'is_online': False
        }), 200

    # 如果用户在线，并且权限检查通过，则返回完整的P2P连接信息
    return jsonify({
        'username': target_user.username,
        'is_online': True,
        'ip_address': target_user.ip_address,
        'port': target_user.port
    })