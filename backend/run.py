from app import create_app, socketio
from app import models  # 确保在应用启动时能识别到数据库模型

# 通过应用工厂模式创建Flask应用实例
# create_app()函数会负责初始化所有必要的扩展和API蓝图
app = create_app()

# 当该脚本被直接执行时，启动开发服务器
if __name__ == '__main__':
    """
    应用的主入口点。
    
    使用 Flask-SocketIO 提供的 run 方法来启动服务器，
    这样可以同时支持标准的HTTP请求和WebSocket连接。
    
    - host='0.0.0.0' 让服务器监听在所有可用的网络接口上，
      使得局域网内的其他设备也可以访问。
    - port=5000 是服务监听的端口号。
    - debug=True 开启调试模式，当代码有变动时服务器会自动重启，
      并在出错时提供详细的错误页面。
    """
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True
    )