from flask import jsonify, g
from app.api import bp
from app.api.auth import token_required
from app.models import User

@bp.route('/users/<string:username>/info', methods=['GET'])
@token_required
def get_user_info(username):
    """
    Retrieves the IP address and port for a specific user,
    provided they are online.
    For privacy, this information is only available for friends.
    """
    current_user = g.current_user
    target_user = User.query.filter_by(username=username).first()

    if not target_user:
        return jsonify({'error': 'User not found'}), 404

    # You can only get info about yourself or your friends.
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