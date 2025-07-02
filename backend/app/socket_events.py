from flask import g, request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models import User
from app.api.auth_socket import token_required_socket

"""
WebSocket事件处理模块
处理所有SocketIO相关事件和连接管理
"""

# 在线用户映射表(双向映射)
# 结构: {username: sid, sid: username}
# 用于快速查找用户连接状态
online_users = {}

def get_sid_by_username(username):
    """根据用户名获取对应的SocketIO会话ID"""
    return online_users.get(username)

@socketio.on('connect')
def handle_connect():
    """
    处理新客户端连接事件
    客户端应在连接后尽快进行身份验证
    """
    print(f'客户端已连接: {request.sid}')

@socketio.on('authenticate')
@token_required_socket
def handle_authenticate(data):
    """
    处理客户端认证事件
    功能:
    1. 更新用户在线状态
    2. 记录客户端IP和端口,用于P2P通信
    3. 加入用户专属房间
    4. 通知好友在线状态变更
    """
    user = g.current_user
    user.is_online = True
    # 客户端应提供其监听IP和端口,用于P2P直连
    user.ip_address = data.get('ip_address', request.remote_addr)
    user.port = data.get('port')
    db.session.commit()

    # 建立双向映射关系,用于断开连接处理
    online_users[user.username] = request.sid
    online_users[request.sid] = user.username

    # 加入以用户名为名的房间,用于定向消息发送
    join_room(user.username)
    print(f'用户 {user.username} 已认证, 状态设为在线, 并加入房间')

    # 通知好友当前用户上线,并通知当前用户其好友的在线状态
    for friend in user.friends:
        if friend.is_online:
            # 通知好友当前用户已上线
            emit('friend_status_update', {
                'username': user.username,
                'is_online': True,
                'ip_address': user.ip_address,  # P2P通信所需的ip
                'port': user.port               # P2P通信所需的端口
            }, to=friend.username)

            # 通知当前用户该好友在线
            emit('friend_status_update', {
                'username': friend.username,
                'is_online': True,
                'ip_address': friend.ip_address,
                'port': friend.port
            }, to=user.username)

@socketio.on('disconnect')
def handle_disconnect():
    """
    处理客户端断开连接事件
    功能:
    1. 更新用户离线状态
    2. 清理IP和端口信息
    3. 通知好友离线状态变更
    """
    if request.sid in online_users:
        username = online_users.pop(request.sid)  # 获取并移除用户名映射
        online_users.pop(username, None)  # 移除反向映射

        user = User.query.filter_by(username=username).first()
        if user:
            user.is_online = False
            user.ip_address = None  # 清除IP地址
            user.port = None       # 清除端口号
            db.session.commit()
            print(f'用户 {user.username} 已断开连接, 状态设为离线')

            # 通知好友该用户已离线
            for friend in user.friends:
                if friend.is_online:
                    emit('friend_status_update', {
                        'username': user.username,
                        'is_online': False
                    }, to=friend.username)

    print(f'客户端已断开: {request.sid}')

@socketio.on('private_message')
@token_required_socket
def handle_private_message(data):
    """
    处理私聊消息事件(已弃用)
    保留此事件仅用于向后兼容
    新的消息系统应使用WebRTC的P2P通信
    """
    recipient_username = data.get('to')
    print(f"[已弃用] 收到给 {recipient_username} 的私聊消息. 应使用P2P通信")

@socketio.on('webrtc_signal')
@token_required_socket
def handle_webrtc_signal(data):
    """
    处理WebRTC信令消息转发
    用于转发offer/answer/ICE候选等信令消息
    """
    to_username = data.get('to')
    if not to_username:
        print("[信令错误] 缺少接收者用户名(to字段)")
        return

    # 信令数据可以是offer/answer/ICE候选等
    # 此处仅做透明转发
    signal_data = data.get('signal')
    
    print(f"转发WebRTC信令: 从 {g.current_user.username} 到 {to_username}")

    emit('webrtc_signal', {
        'from': g.current_user.username,  # 发送者
        'signal': signal_data            # 信令数据
    }, to=to_username)