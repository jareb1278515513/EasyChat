from functools import wraps
from flask import request, g, current_app
import jwt
from app.models import User

def token_required_socket(f):
    """
    WebSocket事件专用的JWT认证装饰器。
    
    这个装饰器用于保护那些需要用户登录才能触发的Socket.IO事件。
    
    与HTTP版本的 `token_required` 装饰器的主要区别:
        1. 获取Token的方式更灵活：它会先尝试从WebSocket连接的初始HTTP头中获取，
           如果获取不到，则会尝试从事件自身传递的数据中获取。这允许在连接时和
           后续的每个事件中都能进行认证。
        2. 错误处理方式不同：由于Socket.IO事件处理器在认证失败时无法像HTTP请求
           那样直接返回一个错误响应给客户端，因此这里的错误处理以降序的方式进行：
           在服务器控制台打印错误日志，并简单地 `return` 来终止后续函数的执行，
           从而静默地拒绝服务。
           
    认证流程:
        1. 检查 'Authorization' 连接头。
        2. 如果头上没有，则检查事件的第一个参数（通常是一个字典）中是否包含 'token' 键。
        3. 解码并验证JWT。
        4. 从JWT中获取用户ID，并查询数据库以验证用户存在性，然后存入 `g.current_user`。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 1. 优先尝试从WebSocket连接时的HTTP请求头中获取token
        #    这通常用于处理 'connect' 事件时的认证。
        if 'Authorization' in request.headers:
            # 格式同样为 'Bearer <token>'
            token = request.headers['Authorization'].split(" ")[1]

        # 2. 如果请求头中没有，则尝试从事件传递的数据中获取
        #    这用于处理 'connect' 之后的所有受保护事件，客户端需要在每个事件的载荷中附带token。
        #    `args[0]` 通常是客户端发送的数据包（dict类型）。
        if not token and args and isinstance(args[0], dict):
            token = args[0].get('token')

        # 如果两种方式都找不到token，则认证失败
        if not token:
            print("Socket.IO Authentication: Token is missing.")
            return  # 终止执行，不调用被装饰的事件处理器

        try:
            # 3. 解码JWT
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            # 4. 验证用户存在，并将其存入g对象，供事件处理器使用
            g.current_user = User.query.get(data['user_id'])
            if not g.current_user:
                 print("Socket.IO Authentication: User not found for token.")
                 return # 终止执行
        except jwt.ExpiredSignatureError:
            print("Socket.IO Authentication: Token has expired.")
            return # 终止执行
        except jwt.InvalidTokenError:
            print("Socket.IO Authentication: Invalid token.")
            return # 终止执行
        except Exception as e:
            # 捕获其他可能的异常
            print(f"Socket.IO Authentication: Token validation error: {e}")
            return # 终止执行

        # 所有验证通过，执行原始的事件处理器函数
        return f(*args, **kwargs)
    return decorated