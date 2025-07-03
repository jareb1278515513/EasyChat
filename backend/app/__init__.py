from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

# 在全局作用域创建扩展实例，但尚未绑定到任何特定的Flask app。
# 这种模式允许我们在不同的应用实例（如生产、测试）中使用这些扩展。
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config_class=Config):
    """
    应用工厂函数。
    遵循这个模式可以方便地创建不同配置下的应用实例，尤其利于测试。
    """
    # 创建一个Flask应用实例
    app = Flask(__name__)
    # 从配置对象中加载应用的配置
    app.config.from_object(config_class)

    # 初始化Flask-CORS，允许所有来源对/api/下的所有路由进行跨域访问。
    # 这对于前后端分离的应用是必需的。
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 将之前创建的扩展实例与当前的app实例进行绑定
    db.init_app(app)
    migrate.init_app(app, db)
    # 初始化SocketIO，允许所有来源的跨域连接
    socketio.init_app(app, cors_allowed_origins="*")

    # 导入并注册API蓝图
    # 蓝图有助于将应用模块化，使代码结构更清晰
    from app.api import bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # 在应用初始化之后导入socket事件处理模块，以避免循环依赖问题。
    # socket_events模块需要使用已经初始化完成的socketio实例。
    from app import socket_events

    # 一个简单的根路由，用于检查后端服务是否正在运行
    @app.route('/')
    def index():
        return "Backend Server is running."

    # 返回配置和初始化完成的应用实例
    return app 