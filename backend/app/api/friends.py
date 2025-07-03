from flask import jsonify, g, request, url_for
from app.api import bp
from app.api.auth import token_required
from app.models import User, FriendRequest
from app import db, socketio

#好友相关操作均需要token认证

@bp.route('/friends', methods=['GET'])
@token_required
def get_friends():
    """获取当前用户的好友列表
    返回:
        - 好友ID、用户名、在线状态和连接信息
        - 按添加时间排序
    """
    user = g.current_user
    friends = user.friends.all()
    return jsonify([{
        'id': friend.id, 
        'username': friend.username,
        'is_online': friend.is_online,
        'ip_address': friend.ip_address,
        'port': friend.port,
        'avatar_url': url_for('static', filename=friend.avatar_url, _external=True) if friend.avatar_url else None
    } for friend in friends])

@bp.route('/friend-requests', methods=['POST'])
@token_required
def send_friend_request():
    """发送好友请求
    请求参数:
        - username: 目标用户名
    业务逻辑:
        1. 检查不能添加自己为好友
        2. 检查目标用户是否存在
        3. 检查是否已是好友
        4. 检查是否已有待处理请求
        5. 创建新请求并发送WebSocket通知
    返回:
        - 成功: 201状态码和成功消息
        - 失败: 400/404状态码和错误原因
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
    """获取当前用户收到的好友请求
    返回:
        - 请求ID、发送者ID、发送者用户名和时间戳
        - 仅包含状态为pending的请求
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
    """处理好友请求(接受/拒绝)
    路径参数:
        - request_id: 好友请求ID
    请求参数:
        - action: accept/reject
    业务逻辑:
        1. 验证请求状态必须为pending
        2. 接受请求会建立双向好友关系
        3. 拒绝请求仅更新状态
    返回:
        - 成功: 操作结果消息
        - 失败: 400/403状态码和错误原因
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
        db.session.commit()
        message = 'Friend request accepted successfully.'
    else: # action == 'reject'
        db.session.delete(friend_request)
        db.session.commit()
        message = 'Friend request rejected successfully.'
    
    return jsonify({'message': message})

@bp.route('/friends/<int:friend_id>', methods=['DELETE'])
@token_required
def remove_friend(friend_id):
    """删除好友关系
    路径参数:
        - friend_id: 好友用户ID
    业务逻辑:
        1. 解除双向好友关系
        2. 删除双方之间的所有好友请求记录
    返回:
        - 成功: 200状态码和成功消息
        - 失败: 400/404状态码和错误原因
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