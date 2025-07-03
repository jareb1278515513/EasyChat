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
        
        return jsonify({'error': 'User not found'}), 404

    
    if target_user.id != current_user.id and not current_user.is_friend(target_user):
        
        return jsonify({'error': 'Access denied: you can only view info for your friends.'}), 403

    
    if not target_user.is_online:
        return jsonify({
            'username': target_user.username,
            'is_online': False
        }), 200

    
    return jsonify({
        'username': target_user.username,  
        'is_online': True,                
        'ip_address': target_user.ip_address,  
        'port': target_user.port          
    })