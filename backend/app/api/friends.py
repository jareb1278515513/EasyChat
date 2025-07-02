from flask import jsonify, g, request
from app.api import bp
from app.api.auth import token_required
from app.models import User, FriendRequest
from app import db, socketio

@bp.route('/friends', methods=['GET'])
@token_required
def get_friends():
    """
    Retrieves the list of friends for the currently authenticated user.
    """
    user = g.current_user
    friends = user.friends.all()
    return jsonify([{
        'id': friend.id, 
        'username': friend.username,
        'is_online': friend.is_online,
        'ip_address': friend.ip_address,
        'port': friend.port
    } for friend in friends])

@bp.route('/friend-requests', methods=['POST'])
@token_required
def send_friend_request():
    """
    Sends a friend request to another user and notifies them via WebSocket.
    """
    data = request.get_json()
    if not data or 'username' not in data:
        return jsonify({'error': 'Missing username in request body'}), 400

    receiver_username = data['username']
    requester = g.current_user

    if receiver_username == requester.username:
        return jsonify({'error': 'You cannot send a friend request to yourself'}), 400

    receiver = User.query.filter_by(username=receiver_username).first()
    if not receiver:
        return jsonify({'error': 'User not found'}), 404

    if requester.is_friend(receiver):
        return jsonify({'error': 'You are already friends with this user'}), 400

    existing_request = FriendRequest.query.filter(
        ((FriendRequest.requester_id == requester.id) & (FriendRequest.receiver_id == receiver.id)) |
        ((FriendRequest.requester_id == receiver.id) & (FriendRequest.receiver_id == requester.id))
    ).first()

    if existing_request and existing_request.status in ['pending', 'accepted']:
        return jsonify({'error': f'A friend request already exists with status: {existing_request.status}'}), 400

    new_request = FriendRequest(requester_id=requester.id, receiver_id=receiver.id, status='pending')
    db.session.add(new_request)
    db.session.commit()

    # Emit a notification to the receiver
    socketio.emit('new_friend_request', {
        'id': new_request.id,
        'requester_id': requester.id,
        'requester_username': requester.username,
        'timestamp': new_request.timestamp.isoformat() + 'Z'
    }, room=receiver.username)

    return jsonify({'message': 'Friend request sent successfully'}), 201

@bp.route('/friend-requests', methods=['GET'])
@token_required
def get_friend_requests():
    """
    Gets all incoming friend requests for the current user.
    """
    user = g.current_user
    requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()
    
    # We need to get the username of the requester
    requests_data = []
    for req in requests:
        requester = User.query.get(req.requester_id)
        requests_data.append({
            'id': req.id,
            'requester_id': req.requester_id,
            'requester_username': requester.username,
            'timestamp': req.timestamp
        })
        
    return jsonify(requests_data)

@bp.route('/friend-requests/<int:request_id>', methods=['PUT'])
@token_required
def respond_to_friend_request(request_id):
    """
    Accepts or rejects a friend request.
    """
    data = request.get_json()
    action = data.get('action')

    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action. Must be "accept" or "reject".'}), 400

    friend_request = FriendRequest.query.get_or_404(request_id)
    current_user = g.current_user

    if friend_request.receiver_id != current_user.id:
        return jsonify({'error': 'You are not authorized to respond to this request'}), 403

    if friend_request.status != 'pending':
        return jsonify({'error': 'This request has already been responded to'}), 400

    if action == 'accept':
        friend_request.status = 'accepted'
        requester = User.query.get(friend_request.requester_id)
        current_user.add_friend(requester)
    else: # action == 'reject'
        friend_request.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({'message': f'Friend request {action}ed successfully.'})

@bp.route('/friends/<int:friend_id>', methods=['DELETE'])
@token_required
def remove_friend(friend_id):
    """
    Removes a friend and deletes any existing friend requests between them.
    """
    current_user = g.current_user
    friend_to_remove = User.query.get(friend_id)

    if not friend_to_remove:
        return jsonify({'error': 'User not found'}), 404

    if not current_user.is_friend(friend_to_remove):
        return jsonify({'error': 'You are not friends with this user'}), 400

    # 1. Remove the friendship
    current_user.remove_friend(friend_to_remove)

    # 2. Delete any friend requests between them, in either direction
    FriendRequest.query.filter(
        ((FriendRequest.requester_id == current_user.id) & (FriendRequest.receiver_id == friend_to_remove.id)) |
        ((FriendRequest.requester_id == friend_to_remove.id) & (FriendRequest.receiver_id == current_user.id))
    ).delete()

    db.session.commit()

    return jsonify({'message': 'Friend removed successfully'}), 200 