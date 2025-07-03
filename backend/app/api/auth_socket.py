from functools import wraps
from flask import request, g, current_app
import jwt
from app.models import User

def token_required_socket(f):
    """WebSocket专用的JWT认证装饰器
    与HTTP版区别:
        1. 支持从headers或事件数据获取token
        2. 错误处理通过打印日志而非返回HTTP响应
        3. 无法主动通知客户端认证失败
    认证流程:
        1. 检查Authorization头
        2. 检查事件数据中的token字段
        3. 解码并验证JWT
        4. 验证用户存在性
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        
        if not token and args and isinstance(args[0], dict):
            token = args[0].get('token')

        if not token:
            print("Authentication token is missing.")
            return  

        try:
            
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            
            g.current_user = User.query.get(data['user_id'])
            if not g.current_user:
                 print("User not found for token.")
                 return
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return
        except Exception as e:
            print(f"Token validation error: {e}")
            return

        return f(*args, **kwargs)
    return decorated