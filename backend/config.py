import os
from dotenv import load_dotenv

# __file__ 是当前脚本的文件名。dirname(__file__) 获取该文件所在的目录。
# abspath() 将其转换为绝对路径，得到项目根目录。
basedir = os.path.abspath(os.path.dirname(__file__))

# 从项目根目录下的 .env 文件加载环境变量。
# 这使得我们可以将敏感信息（如SECRET_KEY）存储在.env中，而不是硬编码在代码里。
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """
    基础配置类，定义了所有环境通用的配置。
    其他特定环境的配置类可以继承此类。
    """
    # Flask及其扩展（如Flask-WTF）用于加密和签名的密钥。
    # 在生产环境中，这应该是一个复杂且保密的字符串。
    # os.environ.get() 会从环境变量中读取值，如果未找到，则使用'或'后面的默认值。
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-hard-to-guess-string'
    
    # 数据库连接的URI。
    # 同样优先从环境变量'DATABASE_URL'读取。
    # 如果未设置，则默认使用项目根目录下的一个名为'app.db'的SQLite数据库文件。
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
        
    # 如果设置为True，Flask-SQLAlchemy会追踪对象的修改并发送信号。
    # 这会占用额外的内存，因此除非特别需要，否则建议关闭。
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    """
    专用于测试环境的配置类。
    继承自基础配置，并覆盖部分设置为测试专用值。
    """
    # 开启Flask应用的测试模式。
    # 在测试模式下，错误会直接抛出，而不是被应用的错误处理器捕获。
    TESTING = True
    
    # 在测试中，使用内存中的SQLite数据库。
    # 这比使用文件数据库快得多，且测试结束后数据会自动清除。
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # 在测试环境中通常会禁用CSRF保护，以简化对表单提交的测试。
    WTF_CSRF_ENABLED = False