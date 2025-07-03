from app import db
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

"""
该文件定义了应用中所有的数据库模型。
每个类代表数据库中的一张表。
"""

# 定义 'friendships' 多对多关联表。
# 这张表不作为独立的模型类，因为它只包含外键，用于连接 'users' 表自身，
# 以此来表示用户之间的好友关系。
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class FriendRequest(db.Model):
    """好友请求模型，代表一个用户向另一个用户发送的好友请求。"""
    __tablename__ = 'friend_requests'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 发送请求的用户ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)   # 接收请求的用户ID
    status = db.Column(db.String(20), default='pending', nullable=False)  # 请求状态: 'pending', 'accepted', 'rejected'
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 请求发送的时间戳

    # 定义一个联合唯一约束，确保同一个用户不能向另一个用户发送重复的未处理请求。
    __table_args__ = (db.UniqueConstraint('requester_id', 'receiver_id', name='_requester_receiver_uc'),)

    def __repr__(self):
        # 定义对象的字符串表示形式，方便调试。
        return f'<FriendRequest from {self.requester_id} to {self.receiver_id}: {self.status}>'

class User(db.Model):
    """用户模型，代表应用中的一个用户。"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  # 用户唯一ID
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)  # 用户名，唯一且有索引
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)    # 邮箱，唯一且有索引
    password_hash = db.Column(db.String(128), nullable=False)  # 存储加盐哈希后的密码，而非明文
    is_online = db.Column(db.Boolean, default=False, nullable=False)  # 标记用户是否在线
    ip_address = db.Column(db.String(45), nullable=True)  # 用户登录时的IP地址，用于P2P连接
    port = db.Column(db.Integer, nullable=True)  # 用户客户端监听的端口，用于P2P连接
    public_key = db.Column(db.Text, nullable=True)  # 存储用户的RSA公钥
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # 标记用户是否为管理员

    # --- 个人资料字段 ---
    gender = db.Column(db.String(10), nullable=True)  # 性别
    age = db.Column(db.Integer, nullable=True)  # 年龄
    bio = db.Column(db.String(200), nullable=True) # 个人简介
    avatar_url = db.Column(db.String(255), nullable=True) # 头像文件的相对路径

    # --- 关系定义 ---
    # 定义用户与好友的多对多关系
    friends = db.relationship('User',
                              secondary=friendships,  # 指定关联表
                              primaryjoin=(friendships.c.user_id == id),  # 定义主连接条件
                              secondaryjoin=(friendships.c.friend_id == id), # 定义次连接条件
                              backref=db.backref('friend_of', lazy='dynamic'), # 定义反向引用
                              lazy='dynamic') # 设置为动态加载，返回查询对象而非直接加载所有好友

    # 定义与好友请求的一对多关系（作为发送者）
    # 当一个用户被删除时，其发送的所有好友请求也会被一并删除 (cascade)
    sent_friend_requests = db.relationship('FriendRequest',
                                           foreign_keys='FriendRequest.requester_id',
                                           backref='requester',
                                           lazy='dynamic',
                                           cascade='all, delete-orphan')
    
    # 定义与好友请求的一对多关系（作为接收者）
    # 当一个用户被删除时，其收到的所有好友请求也会被一并删除 (cascade)
    received_friend_requests = db.relationship('FriendRequest',
                                               foreign_keys='FriendRequest.receiver_id',
                                               backref='receiver',
                                               lazy='dynamic',
                                               cascade='all, delete-orphan')

    def set_password(self, password):
        """使用bcrypt对明文密码进行哈希处理并存储。"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """验证输入的密码是否与存储的哈希密码匹配。"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def add_friend(self, user):
        """添加一个好友。这是一个双向操作。"""
        if not self.is_friend(user):
            self.friends.append(user)
            user.friends.append(self)

    def remove_friend(self, user):
        """移除一个好友。这也是一个双向操作。"""
        if self.is_friend(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def is_friend(self, user):
        """检查目标用户是否已经是当前用户的好友。"""
        return db.session.query(friendships).filter(
            ((friendships.c.user_id == self.id) & (friendships.c.friend_id == user.id)) |
            ((friendships.c.user_id == user.id) & (friendships.c.friend_id == self.id))
        ).count() > 0

    def __repr__(self):
        # 定义对象的字符串表示形式，方便调试。
        return f'<User {self.username}>'