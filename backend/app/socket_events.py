from flask import g, request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import User
from app.api.auth_socket import token_required_socket

# In-memory mapping of session IDs to usernames and vice-versa
# This allows for quick lookups in both directions
online_users = {} # {username: sid, sid: username}

def get_sid_by_username(username):
    return online_users.get(username)

@socketio.on('connect')
def handle_connect():
    """
    Handles a new client connection.
    The client is expected to authenticate shortly after connecting.
    """
    print(f'Client connected: {request.sid}')
    # In a real application, you might have a timeout for unauthenticated connections.

@socketio.on('authenticate')
@token_required_socket
def handle_authenticate(data):
    """
    Authenticates a user, updates their online status, IP address, and port,
    and joins them to a room.
    """
    user = g.current_user
    user.is_online = True
    # The client should send its listening IP and port for P2P communication.
    user.ip_address = data.get('ip_address', request.remote_addr)
    user.port = data.get('port')
    db.session.commit()

    # Map SID to user ID for disconnect handling
    online_users[user.username] = request.sid
    online_users[request.sid] = user.username

    join_room(user.username)
    print(f'User {user.username} authenticated, status set to online, and joined room.')

    # Notify friends that this user is now online AND notify this user of their friends' statuses
    for friend in user.friends:
        if friend.is_online:
            # Notify the friend that the current user is online
            emit('friend_status_update', {
                'username': user.username,
                'is_online': True,
                'ip_address': user.ip_address,
                'port': user.port
            }, to=friend.username)

            # Notify the current user that this friend is online
            emit('friend_status_update', {
                'username': friend.username,
                'is_online': True,
                'ip_address': friend.ip_address,
                'port': friend.port
            }, to=user.username)

@socketio.on('disconnect')
def handle_disconnect():
    """
    Handles a client disconnection, updating their online status.
    """
    if request.sid in online_users:
        username = online_users.pop(request.sid) # Get and remove the username
        online_users.pop(username, None) # Remove the reverse mapping

        user = User.query.filter_by(username=username).first()
        if user:
            user.is_online = False
            user.ip_address = None # Clear IP address on disconnect
            user.port = None # Clear port on disconnect
            db.session.commit()
            print(f'User {user.username} disconnected, status set to offline.')

            # Notify friends that this user is now offline
            for friend in user.friends:
                if friend.is_online:
                    emit('friend_status_update', {
                        'username': user.username,
                        'is_online': False
                    }, to=friend.username)

    print(f'Client disconnected: {request.sid}')

@socketio.on('private_message')
@token_required_socket
def handle_private_message(data):
    """
    DEPRECATED: This event is no longer used for messaging.
    It is kept for backward compatibility or potential future use.
    The new messaging system is P2P via WebRTC.
    """
    recipient_username = data.get('to')
    print(f"[DEPRECATED] Private message received for {recipient_username}. P2P should be used.")

@socketio.on('webrtc_signal')
@token_required_socket
def handle_webrtc_signal(data):
    """
    Forwards WebRTC signaling messages (offers, answers, ICE candidates)
    from the sender to the recipient.
    """
    to_username = data.get('to')
    if not to_username:
        print("[Signal Error] 'to' field missing in signal data")
        return

    # The signal data can be anything (offer, answer, candidate),
    # we just forward it transparently.
    signal_data = data.get('signal')
    
    print(f"Forwarding WebRTC signal from {g.current_user.username} to {to_username}")

    emit('webrtc_signal', {
        'from': g.current_user.username,
        'signal': signal_data
    }, to=to_username) 