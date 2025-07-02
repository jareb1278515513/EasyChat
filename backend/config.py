import os
from dotenv import load_dotenv

# 获取项目根目录路径
basedir = os.path.abspath(os.path.dirname(__file__))
# 从.env文件加载环境变量
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    基础配置类，包含所有环境通用配置
    
    配置项从环境变量获取，如果没有设置则使用默认值
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'  # Flask应用密钥
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')  # 数据库连接URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 为了节省资源，禁用SQLAlchemy事件系统

class TestingConfig(Config):
    """
    测试环境所用配置
    
    继承自Config类，覆盖部分配置项用于测试
    """
    TESTING = True  # 启用测试模式
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # 使用内存数据库提高测试速度
    WTF_CSRF_ENABLED = False  # 禁用CSRF保护，方便表单测试