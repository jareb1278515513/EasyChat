import os
from dotenv import load_dotenv


basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    基础配置类，包含所有环境通用配置
    
    配置项从环境变量获取，如果没有设置则使用默认值
    """
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'  
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')  
    SQLALCHEMY_TRACK_MODIFICATIONS = False  

class TestingConfig(Config):
    """
    测试环境所用配置
    
    继承自Config类，覆盖部分配置项用于测试
    """
    TESTING = True  
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  
    WTF_CSRF_ENABLED = False  