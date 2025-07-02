from functools import wraps
from flask import request, g, current_app
import jwt
from app.models import User
# Remove direct call to create_app
# from app import create_app

# Get the app instance to access config
# app = create_app()

def token_required_socket(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # In Flask-SocketIO, the token might be passed in the connection headers
        # or as part of the message payload. We'll check headers first.
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            # If not in headers, maybe it was sent in the 'authenticate' event data
            # The first argument to a SocketIO event handler is the data payload.
            if args and isinstance(args[0], dict):
                token = args[0].get('token')

        if not token:
            # Cannot emit here, as we are not in a request context with a sid.
            # We will just return, and the client will not get an ack.
            print("Authentication token is missing.")
            return

        try:
            # Use current_app to access config
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            g.current_user = User.query.get(data['user_id'])
            if not g.current_user:
                 print("User not found for token.")
                 return
        except jwt.ExpiredSignatureError:
            print("Token has expired.")
            return
        except jwt.InvalidTokenError:
            print("Invalid token.")
            return
        except Exception as e:
            print(f"An error occurred during token validation: {e}")
            return

        return f(*args, **kwargs)
    return decorated 