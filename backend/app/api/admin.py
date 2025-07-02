from flask import jsonify
from app.api import bp
from app.api.auth import admin_required
from app.models import User
from app.socket_events import get_sid_by_username
from app import socketio, db

@bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    """
    [ADMIN] Retrieves a list of all users and their status.
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
    """
    [ADMIN] Forcibly disconnects a user by their username.
    """
    user_to_disconnect = User.query.filter_by(username=username).first()
    if not user_to_disconnect:
        return jsonify({'error': 'User not found'}), 404
        
    if not user_to_disconnect.is_online:
        return jsonify({'message': 'User is already offline'}), 200

    sid = get_sid_by_username(username)
    if sid:
        # This will trigger the 'disconnect' event handler in socket_events.py
        socketio.disconnect(sid)
        return jsonify({'message': f'Disconnect signal sent to {username}.'}), 200
    else:
        # This case might happen if the in-memory map is out of sync with the DB
        # Forcing DB state to be correct
        user_to_disconnect.is_online = False
        db.session.commit()
        return jsonify({'error': 'User is online in DB but not found in socket session. Status corrected.'}), 500 