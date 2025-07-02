from flask import jsonify, g
from app.api import bp
from app.api.auth import token_required
from app.models import User

@bp.route('/users/<string:username>/info', methods=['GET'])
@token_required
def get_user_info(username):
    """
    获取指定用户的在线状态和连接信息
    
    参数:
        username: 目标用户名
        
    返回:
        JSON响应包含:
        - 基础用户信息
        - 在线状态(is_online)
        - 如果在线则包含IP和端口(仅对好友可见)
        
    错误响应:
        404: 用户不存在
        403: 不是好友关系，无权限查看
    """
    current_user = g.current_user
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        # 用户不存在时返回404
        return jsonify({'error': 'User not found'}), 404

    # 权限检查: 只能查看自己或好友的信息
    if target_user.id != current_user.id and not current_user.is_friend(target_user):
        # 非好友关系返回403禁止访问
        return jsonify({'error': 'Access denied: you can only view info for your friends.'}), 403

    # 检查用户在线状态
    if not target_user.is_online:
        return jsonify({
            'username': target_user.username,
            'is_online': False
        }), 200

    # 返回完整的在线用户信息
    return jsonify({
        'username': target_user.username,  # 用户名
        'is_online': True,                # 在线状态标志
        'ip_address': target_user.ip_address,  # 用户IP
        'port': target_user.port          # 用户端口
    })