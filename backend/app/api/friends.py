from flask import jsonify, g, request, url_for
from app.api import bp
from app.api.auth import token_required
from app.models import User, FriendRequest
from app import db, socketio

# 好友相关的所有API操作都需要token认证，因此都使用 @token_required 装饰器

@bp.route('/friends', methods=['GET'])
@token_required
def get_friends():
    """
    获取当前登录用户的好友列表。
    
    返回:
        - 一个包含所有好友信息的JSON数组。每个好友对象包括ID、用户名、在线状态、
          P2P连接信息以及完整的头像URL。
        - 列表按好友添加时间排序（由数据库关系定义）。
    """
    # g.current_user 是由 @token_required 装饰器设置的
    user = g.current_user
    # user.friends 是在 User 模型中定义的 relationship，它会查询与当前用户关联的所有好友
    friends = user.friends.all()
    # 构建好友列表的JSON响应
    return jsonify([{
        'id': friend.id, 
        'username': friend.username,
        'is_online': friend.is_online,
        'ip_address': friend.ip_address,
        'port': friend.port,
        # 使用 url_for 生成头像的完整外部URL，以便前端能直接访问
        # 如果用户没有设置头像(avatar_url为空)，则返回null
        'avatar_url': url_for('static', filename=friend.avatar_url, _external=True) if friend.avatar_url else None
    } for friend in friends])

@bp.route('/friend-requests', methods=['POST'])
@token_required
def send_friend_request():
    """
    发送一个好友请求给指定用户。
    
    请求体 JSON 参数:
        - username (string): 接收好友请求的用户名。
    业务逻辑:
        1. 验证不能添加自己为好友。
        2. 验证目标用户是否存在。
        3. 验证双方是否已经是好友。
        4. 验证是否已存在待处理的、双向的好友请求。
        5. 创建新的好友请求记录，并通过WebSocket向接收方发送实时通知。
    """
    data = request.get_json()
    # 确保请求体中包含 'username'
    if not data or 'username' not in data:
        return jsonify({'error': 'Missing username in request body'}), 400

    receiver_username = data['username']
    requester = g.current_user

    # 1. 不能添加自己
    if receiver_username == requester.username:
        return jsonify({'error': 'You cannot send a friend request to yourself'}), 400

    # 2. 查找接收请求的用户
    receiver = User.query.filter_by(username=receiver_username).first()
    if not receiver:
        return jsonify({'error': 'User not found'}), 404

    # 3. 检查是否已经是好友
    if requester.is_friend(receiver):
        return jsonify({'error': 'You are already friends with this user'}), 400

    # 4. 检查是否已存在请求（无论是谁发给谁）
    existing_request = FriendRequest.query.filter(
        ((FriendRequest.requester_id == requester.id) & (FriendRequest.receiver_id == receiver.id)) |
        ((FriendRequest.requester_id == receiver.id) & (FriendRequest.receiver_id == requester.id))
    ).first()

    # 如果存在状态为'pending'或'accepted'的请求，则不允许重复发送
    if existing_request and existing_request.status in ['pending', 'accepted']:
        return jsonify({'error': f'A friend request already exists with status: {existing_request.status}'}), 400

    # 5. 创建新的好友请求记录，状态为'pending'
    new_request = FriendRequest(requester_id=requester.id, receiver_id=receiver.id, status='pending')
    db.session.add(new_request)
    db.session.commit()

    # 5.1 通过WebSocket向接收方实时推送新好友请求的通知
    #     使用接收方的用户名作为房间名(room)，确保只有他能收到
    socketio.emit('new_friend_request', {
        'id': new_request.id,
        'requester_id': requester.id,
        'requester_username': requester.username,
        'timestamp': new_request.timestamp.isoformat() + 'Z' # 使用ISO 8601格式的时间戳
    }, room=receiver.username)

    return jsonify({'message': 'Friend request sent successfully'}), 201

@bp.route('/friend-requests', methods=['GET'])
@token_required
def get_friend_requests():
    """
    获取当前用户收到的、所有待处理的好友请求。
    
    返回:
        - 一个包含所有待处理请求信息的JSON数组。每个请求对象包括请求ID、
          发送者ID、发送者用户名和请求时间戳。
    """
    user = g.current_user
    # 查询所有发送给当前用户且状态为'pending'的请求
    requests = FriendRequest.query.filter_by(receiver_id=user.id, status='pending').all()
    
    requests_data = []
    # 遍历请求，以附加发送者的用户名信息
    for req in requests:
        # 根据请求中的发送者ID查询其用户信息
        requester = User.query.get(req.requester_id)
        # 增加一个健壮性检查：确保发送请求的用户仍然存在
        if requester:
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
    处理一个好友请求（接受或拒绝）。
    
    路径参数:
        - request_id: 要处理的好友请求的ID。
    请求体 JSON 参数:
        - action (string): 'accept' 或 'reject'。
    业务逻辑:
        1. 验证请求的所有权，确保是接收者本人在操作。
        2. 验证请求当前是否为'pending'状态。
        3. 如果接受，则更新请求状态并建立双向好友关系。
        4. 如果拒绝，则直接从数据库中删除该请求记录。
    """
    data = request.get_json()
    action = data.get('action')

    # 验证action参数的有效性
    if action not in ['accept', 'reject']:
        return jsonify({'error': 'Invalid action. Must be "accept" or "reject".'}), 400

    # 查找好友请求记录，如果不存在则自动返回404
    friend_request = FriendRequest.query.get_or_404(request_id)
    current_user = g.current_user

    # 1. 验证当前用户是否是该请求的接收者
    if friend_request.receiver_id != current_user.id:
        return jsonify({'error': 'You are not authorized to respond to this request'}), 403

    # 2. 验证请求是否未被处理过
    if friend_request.status != 'pending':
        return jsonify({'error': 'This request has already been responded to'}), 400

    if action == 'accept':
        # 3. 如果接受请求
        friend_request.status = 'accepted' # 更新请求状态
        requester = User.query.get(friend_request.requester_id)
        current_user.add_friend(requester) # 调用模型中的方法添加好友（双向关系）
        db.session.commit()
        message = 'Friend request accepted successfully.'
    else: # action == 'reject'
        # 4. 如果拒绝请求，直接删除记录
        db.session.delete(friend_request)
        db.session.commit()
        message = 'Friend request rejected successfully.'
    
    return jsonify({'message': message})

@bp.route('/friends/<int:friend_id>', methods=['DELETE'])
@token_required
def remove_friend(friend_id):
    """
    删除一个好友。
    
    路径参数:
        - friend_id: 要删除的好友的用户ID。
    业务逻辑:
        1. 验证目标用户是否真的是当前用户的好友。
        2. 解除双向的好友关系。
        3. 清理掉双方之间所有历史好友请求记录。
    """
    current_user = g.current_user
    friend_to_remove = User.query.get(friend_id)

    if not friend_to_remove:
        return jsonify({'error': 'User not found'}), 404

    # 1. 验证好友关系是否存在
    if not current_user.is_friend(friend_to_remove):
        return jsonify({'error': 'You are not friends with this user'}), 400

    # 2. 调用模型中的方法解除好友关系（双向）
    current_user.remove_friend(friend_to_remove)

    # 3. 删除他们之间所有方向的好友请求记录，保持数据清洁
    FriendRequest.query.filter(
        ((FriendRequest.requester_id == current_user.id) & (FriendRequest.receiver_id == friend_to_remove.id)) |
        ((FriendRequest.requester_id == friend_to_remove.id) & (FriendRequest.receiver_id == current_user.id))
    ).delete()

    db.session.commit()

    return jsonify({'message': 'Friend removed successfully'}), 200 