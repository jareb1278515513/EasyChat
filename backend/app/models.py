from app import db
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

"""
数据库模型定义文件
包含用户、好友关系等核心数据模型
"""

# 好友关系多对多关联表
friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class FriendRequest(db.Model):
    """好友请求模型"""
    __tablename__ = 'friend_requests'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 请求者ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)   # 接收者ID
    status = db.Column(db.String(20), default='pending', nullable=False)  # 状态: pending(待处理), accepted(已接受), rejected(已拒绝)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)  # 创建时间

    # unique约束: 防止重复的好友请求
    __table_args__ = (db.UniqueConstraint('requester_id', 'receiver_id', name='_requester_receiver_uc'),)

    def __repr__(self):
        return f'<FriendRequest from {self.requester_id} to {self.receiver_id}: {self.status}>'

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)  # 用户名
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)    # 邮箱
    password_hash = db.Column(db.String(128), nullable=False)  # 密码哈希值
    is_online = db.Column(db.Boolean, default=False, nullable=False)  # 在线状态
    ip_address = db.Column(db.String(45), nullable=True)  # IP地址(支持IPv6)
    port = db.Column(db.Integer, nullable=True)  # 端口号(用于P2P通信)
    public_key = db.Column(db.Text, nullable=True)  # 用户公钥(用于加密通信)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)  # 是否是管理员

    # 新增的个人信息字段
    gender = db.Column(db.String(10), nullable=True)  # 性别
    age = db.Column(db.Integer, nullable=True)  # 年龄
    bio = db.Column(db.String(200), nullable=True) # 个人简介

    # 好友关系(多对多)
    friends = db.relationship('User',
                              secondary=friendships,
                              primaryjoin=(friendships.c.user_id == id),
                              secondaryjoin=(friendships.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'),
                              lazy='dynamic')

    # 级联删除好友请求
    sent_friend_requests = db.relationship('FriendRequest',
                                           foreign_keys='FriendRequest.requester_id',
                                           backref='requester',
                                           lazy='dynamic',
                                           cascade='all, delete-orphan')
    
    received_friend_requests = db.relationship('FriendRequest',
                                               foreign_keys='FriendRequest.receiver_id',
                                               backref='receiver',
                                               lazy='dynamic',
                                               cascade='all, delete-orphan')

    def set_password(self, password):
        """设置密码(自动生成salt并哈希)"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def add_friend(self, user):
        """添加好友(双向关系)"""
        if not self.is_friend(user):
            self.friends.append(user)
            user.friends.append(self)

    def remove_friend(self, user):
        """移除好友(双向关系)"""
        if self.is_friend(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def is_friend(self, user):
        """检查是否已经是好友"""
        return db.session.query(friendships).filter(
            ((friendships.c.user_id == self.id) & (friendships.c.friend_id == user.id)) |
            ((friendships.c.user_id == user.id) & (friendships.c.friend_id == self.id))
        ).count() > 0

    def __repr__(self):
        return f'<User {self.username}>'