from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*")

    from app.api import bp as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Import socket events after app initialization to avoid circular dependencies
    from app import socket_events

    @app.route('/')
    def index():
        return "Backend Server is running."

    return app 