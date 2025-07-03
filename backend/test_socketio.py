import socketio
import time
import jwt
import threading

#配置区
BASE_URL = 'http://10.21.206.207:5000'  # 服务器地址
SECRET_KEY = 'a-hard-to-guess-string'   # JWT密钥
USER_A_ID = 1
USER_A_USERNAME = 'alice'
USER_B_ID = 2
USER_B_USERNAME = 'bob'

#JWT令牌生成
def generate_token(user_id):
    """为指定用户生成JWT令牌"""
    payload = {'user_id': user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

#客户端类
class UserClient:
    """
    客户端类
    包括用户ID、用户名、socketio客户端、JWT令牌、连接状态
    以及发送消息、接收消息等功能
    """
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.sio = socketio.Client()
        self.token = generate_token(user_id)
        self.is_connected = False
        self.setup_handlers()

    def setup_handlers(self):
        # 连接成功事件
        @self.sio.event
        def connect():
            print(f"[{self.username}] 连接成功.")
            self.sio.emit('authenticate', {'token': self.token})
            print(f"[{self.username}] 已发送认证信息.")
            self.is_connected = True

        # 断开连接事件
        @self.sio.event
        def disconnect():
            print(f"[{self.username}] 已断开连接.")
            self.is_connected = False

        # 收到新消息事件
        @self.sio.on('new_message')
        def on_new_message(data):
            print(f"[{self.username}] 收到消息: {data}")

        # 好友状态更新事件
        @self.sio.on('friend_status_update')
        def on_friend_status_update(data):
            print(f"[{self.username}] 收到好友状态更新: {data}")

        # 错误事件
        @self.sio.on('error')
        def on_error(data):
            print(f"[{self.username}] 收到错误: {data}")

    def connect(self):
        self.sio.connect(BASE_URL)

    def disconnect(self):
        if self.is_connected:
            self.sio.disconnect()
    
    def wait(self):
        self.sio.wait()

    def send_message(self, recipient_username, message):
        if not self.is_connected:
            print(f"[{self.username}] 未连接，无法发送消息.")
            return
        print(f"[{self.username}] 向{recipient_username}发送消息.")
        self.sio.emit('private_message', {
            'to': recipient_username,
            'message': message,
            'token': self.token
        })

#主流程
if __name__ == '__main__':
    # 创建Alice和Bob的客户端
    alice_client = UserClient(USER_A_ID, USER_A_USERNAME)
    bob_client = UserClient(USER_B_ID, USER_B_USERNAME)

    try:
        # 先让Bob连接，准备接收消息
        bob_thread = threading.Thread(target=bob_client.connect)
        bob_thread.start()
        time.sleep(2) # 等待Bob连接并认证

        # 再让Alice连接，Bob应收到状态更新
        alice_client.connect()
        time.sleep(2) # 等待Alice连接并认证

        # Alice给Bob发消息
        alice_client.send_message(USER_B_USERNAME, "Hello, Bob! This is Alice.")
        
        # 保持脚本运行，便于Bob接收消息
        print("\n客户端运行中，按Ctrl+C退出.")
        time.sleep(5) # 等待消息交换

    except Exception as e:
        print(f"发生异常: {e}")
    finally:
        print("\n断开客户端连接，Bob应收到Alice下线通知.")
        alice_client.disconnect()
        bob_client.disconnect()
        time.sleep(2) # 等待断开事件处理