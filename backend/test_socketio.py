import socketio
import time
import jwt
import threading

# --- Configuration ---
BASE_URL = 'http://10.21.206.207:5000'
SECRET_KEY = 'a-hard-to-guess-string' 
USER_A_ID = 1
USER_A_USERNAME = 'alice'
USER_B_ID = 2
USER_B_USERNAME = 'bob'

# --- JWT Token Generation ---
def generate_token(user_id):
    """Generates a JWT token for a user."""
    payload = {'user_id': user_id}
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# --- Client Class ---
class UserClient:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.sio = socketio.Client()
        self.token = generate_token(user_id)
        self.is_connected = False
        self.setup_handlers()

    def setup_handlers(self):
        @self.sio.event
        def connect():
            print(f"[{self.username}] Connection established.")
            self.sio.emit('authenticate', {'token': self.token})
            print(f"[{self.username}] Sent authentication.")
            self.is_connected = True

        @self.sio.event
        def disconnect():
            print(f"[{self.username}] Disconnected from server.")
            self.is_connected = False

        @self.sio.on('new_message')
        def on_new_message(data):
            print(f"[{self.username}] Received message: {data}")

        @self.sio.on('friend_status_update')
        def on_friend_status_update(data):
            print(f"[{self.username}] Received friend status update: {data}")

        @self.sio.on('error')
        def on_error(data):
            print(f"[{self.username}] Received error: {data}")

    def connect(self):
        self.sio.connect(BASE_URL)

    def disconnect(self):
        if self.is_connected:
            self.sio.disconnect()
    
    def wait(self):
        self.sio.wait()

    def send_message(self, recipient_username, message):
        if not self.is_connected:
            print(f"[{self.username}] Cannot send message, not connected.")
            return
        
        print(f"[{self.username}] Sending message to {recipient_username}.")
        self.sio.emit('private_message', {
            'to': recipient_username,
            'message': message,
            'token': self.token
        })

# --- Main Execution ---
if __name__ == '__main__':
    # Create clients for Alice and Bob
    alice_client = UserClient(USER_A_ID, USER_A_USERNAME)
    bob_client = UserClient(USER_B_ID, USER_B_USERNAME)

    try:
        # Connect Bob first so he is ready to receive messages
        bob_thread = threading.Thread(target=bob_client.connect)
        bob_thread.start()
        time.sleep(2) # Wait for Bob to connect and authenticate

        # Connect Alice, Bob should receive a status update
        alice_client.connect()
        time.sleep(2) # Wait for Alice to connect and authenticate

        # Alice sends a message to Bob
        alice_client.send_message(USER_B_USERNAME, "Hello, Bob! This is Alice.")
        
        # Keep the script running to allow Bob to receive the message
        print("\nClients are running. Press Ctrl+C to exit.")
        
        # We can wait on one of the clients' threads or just sleep
        time.sleep(5) # Wait for a bit to see the message exchange


    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("\nDisconnecting clients. Bob should receive a status update about Alice.")
        alice_client.disconnect()
        bob_client.disconnect()
        time.sleep(2) # Allow time for disconnect events to be processed

        # It's good practice to join threads, though the program is exiting.
        # bob_thread.join() 