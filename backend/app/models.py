from app import db
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Database models will be defined here.
# Example:
#
# class User(db.Model):
#     __tablename__ = 'users'
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(64), index=True, unique=True, nullable=False)
#     email = db.Column(db.String(120), index=True, unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False) 

friendships = db.Table('friendships',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('friend_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False) # pending, accepted, rejected
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('requester_id', 'receiver_id', name='_requester_receiver_uc'),)

    def __repr__(self):
        return f'<FriendRequest from {self.requester_id} to {self.receiver_id}: {self.status}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_online = db.Column(db.Boolean, default=False, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True) # Supports IPv6 addresses
    port = db.Column(db.Integer, nullable=True)
    public_key = db.Column(db.Text, nullable=True)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    friends = db.relationship('User',
                              secondary=friendships,
                              primaryjoin=(friendships.c.user_id == id),
                              secondaryjoin=(friendships.c.friend_id == id),
                              backref=db.backref('friend_of', lazy='dynamic'),
                              lazy='dynamic')

    def set_password(self, password):
        # The password salt is generated randomly by bcrypt and is included in the hash
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    def add_friend(self, user):
        if not self.is_friend(user):
            self.friends.append(user)
            user.friends.append(self)

    def remove_friend(self, user):
        if self.is_friend(user):
            self.friends.remove(user)
            user.friends.remove(self)

    def is_friend(self, user):
        return db.session.query(friendships).filter(
            ((friendships.c.user_id == self.id) & (friendships.c.friend_id == user.id)) |
            ((friendships.c.user_id == user.id) & (friendships.c.friend_id == self.id))
        ).count() > 0

    def __repr__(self):
        return f'<User {self.username}>' 