from app import create_app, socketio
from app import models  # 确保模型被注册到SQLAlchemy

# 创建Flask应用实例
# create_app()会初始化所有扩展和蓝图
app = create_app()

if __name__ == '__main__':
    """
    应用入口点 - 直接执行时运行
    
    使用SocketIO运行开发服务器:
    - 监听所有网络接口(0.0.0.0)，校园网范围内设备可以访问
    - 使用默认端口5000
    - 启用调试模式
    
    """
    socketio.run(
        app,
        host='0.0.0.0',  
        port=5000,       
        debug=True       
    )