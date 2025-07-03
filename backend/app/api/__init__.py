# 从 flask 库中导入 Blueprint 类，用于创建蓝图
from flask import Blueprint

# 创建一个名为 'api' 的蓝图实例。
# 'api' 是蓝图的名称，通常用于在url_for中引用端点。
# __name__ 是模块的名称，Flask用它来定位蓝图的资源。
bp = Blueprint('api', __name__)

# 在文件末尾导入API模块（如 users.py, friends.py 等）。
# 这样做是为了将这些文件中定义的路由注册到上面创建的蓝图(bp)上。
# 这是一种避免循环导入的常见Flask模式，因为这些被导入的模块自身也需要从 app.api 导入 bp。
from app.api import users, friends, admin, online 