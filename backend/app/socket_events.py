from flask import g, request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import User
from app.api.auth_socket import token_required_socket

"""
WebSocket 事件处理模块

本模块定义了所有通过Socket.IO进行实时通信的事件处理器。
它负责管理用户的连接、认证、在线状态同步，以及为WebRTC P2P连接提供信令服务。
"""

# 在线用户名字典，用于快速查找用户的会话ID(sid)和用户名。
# 这是一个双向映射，方便通过sid找到用户名，或通过用户名找到sid。
# 结构: { 'username1': 'sid123', 'sid123': 'username1', ... }
online_users = {}

def get_sid_by_username(username):
    """一个辅助函数，根据用户名从在线用户字典中获取其对应的Socket.IO会话ID。"""
    return online_users.get(username)

@socketio.on('connect')
def handle_connect():
    """
    处理客户端成功建立WebSocket连接的事件。
    这是一个初始握手，此时服务器只知道有一个新的匿名连接建立。
    客户端需要在连接成功后，立即发送 'authenticate' 事件并附上JWT来进行身份验证。
    """
    print(f'客户端已连接，会话ID: {request.sid}')

@socketio.on('authenticate')
@token_required_socket
def handle_authenticate(data):
    """
    处理客户端的身份验证事件。这是连接后最关键的一步。
    此事件受 `token_required_socket` 装饰器保护，确保只有携带有效JWT的客户端才能认证成功。
    
    功能:
    1. 将数据库中用户的在线状态(is_online)标记为True。
    2. 存储客户端上报的用于P2P通信的IP地址和端口号。
    3. 将当前连接加入一个以该用户命名的"房间"(Room)，方便服务器后续向该用户定向发送消息。
    4. 维护 online_users 字典，建立用户名和sid的双向映射。
    5. 向该用户的所有好友广播其上线的消息（包括P2P连接信息）。
    6. 向该用户发送其所有在线好友的列表和状态。
    """
    # g.current_user 由 @token_required_socket 装饰器提供
    user = g.current_user
    user.is_online = True
    # 从客户端发送的数据中获取用于P2P的IP和端口，如果未提供，IP地址默认为请求来源IP
    user.ip_address = data.get('ip_address', request.remote_addr)
    user.port = data.get('port')
    db.session.commit()

    # 4. 在内存中建立双向映射，用于快速查找
    online_users[user.username] = request.sid
    online_users[request.sid] = user.username

    # 3. 加入以用户名为名的专属房间
    join_room(user.username)
    print(f'用户 {user.username} (SID: {request.sid}) 已通过认证，加入房间并标记为在线。')

    # 5 & 6. 遍历用户的好友列表，进行双向状态通知
    for friend in user.friends:
        # 只通知在线的好友
        if friend.is_online:
            # 通知好友"我"上线了，并把"我"的连接信息发给他
            emit('friend_status_update', {
                'username': user.username,
                'is_online': True,
                'ip_address': user.ip_address,
                'port': user.port
            }, to=friend.username) # 'to'参数指定了接收消息的房间名

            # 同时，也通知"我"这个好友是在线的，并把他的连接信息发给"我"
            emit('friend_status_update', {
                'username': friend.username,
                'is_online': True,
                'ip_address': friend.ip_address,
                'port': friend.port
            }, to=user.username)

@socketio.on('disconnect')
def handle_disconnect():
    """
    处理客户端断开连接的事件。
    功能:
    1. 从 online_users 字典中移除该用户的映射关系。
    2. 将数据库中用户的在线状态(is_online)标记为False，并清除IP和端口。
    3. 向该用户的所有在线好友广播其下线的消息。
    """
    # 检查断开连接的sid是否是已认证的用户
    if request.sid in online_users:
        # 1. 通过sid找到用户名，然后移除两个方向的映射
        username = online_users.pop(request.sid)
        online_users.pop(username, None)

        # 2. 更新数据库状态
        user = User.query.filter_by(username=username).first()
        if user:
            user.is_online = False
            user.ip_address = None
            user.port = None
            db.session.commit()
            print(f'用户 {user.username} 已断开连接，状态更新为离线。')

            # 3. 通知所有在线好友该用户已下线
            for friend in user.friends:
                if friend.is_online:
                    emit('friend_status_update', {
                        'username': user.username,
                        'is_online': False
                    }, to=friend.username)

    print(f'客户端已断开，会话ID: {request.sid}')

@socketio.on('private_message')
@token_required_socket
def handle_private_message(data):
    """
    处理私聊消息事件（已弃用）。
    在旧的C/S架构中，此事件用于通过服务器转发消息。
    在当前的P2P架构中，消息直接在客户端之间传输，不再经过服务器。
    保留此事件仅用于调试或向后兼容目的。
    """
    recipient_username = data.get('to')
    print(f"[警告：已弃用事件] 收到给 {recipient_username} 的私聊消息。消息应通过WebRTC P2P通道传输。")

@socketio.on('webrtc_signal')
@token_required_socket
def handle_webrtc_signal(data):
    """
    处理WebRTC信令消息的转发。这是P2P连接建立过程中的核心。
    
    WebRTC建立连接需要一个"信令服务器"来交换元数据，例如：
    - SDP (Session Description Protocol) 的 offer 和 answer：描述了媒体流的配置。
    - ICE (Interactive Connectivity Establishment) 候选地址：描述了可能的网络路径。
    
    此函数扮演的就是信令服务器的角色。它只是一个透明的中间人，
    将信令消息从一个客户端原封不动地转发给另一个客户端。
    """
    # 获取信令的目标接收者用户名
    to_username = data.get('to')
    if not to_username:
        print("[WebRTC 信令错误] 转发请求缺少 'to' 字段，无法确定接收者。")
        return

    # 'signal' 字段中包含了WebRTC所需交换的任意信令数据 (offer/answer/candidate)
    signal_data = data.get('signal')
    
    print(f"正在转发WebRTC信令: 从 {g.current_user.username} -> 至 {to_username}")

    # 将信令数据包发送到指定用户的房间
    emit('webrtc_signal', {
        'from': g.current_user.username, # 附上发送者用户名
        'signal': signal_data            # 原始信令数据
    }, to=to_username)