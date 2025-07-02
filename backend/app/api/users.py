from flask import request, jsonify, current_app, g
from app.api import bp
from app.models import User
from app import db
import jwt
from datetime import datetime, timedelta, timezone
from app.api.auth import token_required

@bp.route('/ping')
def ping():
    return "Pong!"

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Missing username, email, or password'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.query.filter_by(username=username).first()

    if user is None or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Update user's IP and port on login
    user.ip_address = request.remote_addr
    port = data.get('port')
    if port:
        user.port = port
    db.session.commit()

    # Create the token
    token = jwt.encode(
        {
            'user_id': user.id,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24) # Token expires in 24 hours
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

    return jsonify({'token': token})

@bp.route('/keys', methods=['POST'])
@token_required
def upload_key():
    """Allows an authenticated user to upload their public key."""
    data = request.get_json()
    if not data or 'public_key' not in data:
        return jsonify({'error': 'Missing public_key in request body'}), 400
    
    user = g.current_user
    user.public_key = data['public_key']
    db.session.commit()
    
    return jsonify({'message': 'Public key updated successfully'}), 200

@bp.route('/users/<string:username>/public_key', methods=['GET'])
@token_required
def get_public_key(username):
    """Retrieves the public key for a given user."""
    user = User.query.filter_by(username=username).first_or_404()
    if not user.public_key:
        return jsonify({'error': 'User has not uploaded a public key'}), 404
        
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'public_key': user.public_key
    }) 