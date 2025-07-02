import unittest
import json
from app import create_app, db
from app.models import User
from config import TestingConfig
from unittest.mock import patch

class UserModelCase(unittest.TestCase):
    def setUp(self):
        """
        Set up a test environment.
        This method is called before each test function.
        """
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """
        Clean up the test environment.
        This method is called after each test function.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """Test password hashing and verification."""
        u = User(username='susan', email='susan@example.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_registration(self):
        """Test user registration endpoint."""
        # Test Case 1: Successful Registration
        response = self.client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testuser1',
                'email': 'testuser1@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('User registered successfully', response.get_data(as_text=True))

        # Test Case 2: Duplicate Username
        response = self.client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testuser1',
                'email': 'another@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Username already exists', response.get_data(as_text=True))

        # Test Case 3: Missing Password
        response = self.client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testuser2',
                'email': 'testuser2@example.com'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Missing username, email, or password', response.get_data(as_text=True))

    def test_login(self):
        """Test user login endpoint."""
        # First, register a user to have a test subject
        self.client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testloginuser',
                'email': 'login@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        # Test Case 1: Successful Login
        response = self.client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testloginuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        json_response = response.get_json()
        self.assertIn('token', json_response)

        # Test Case 2: Wrong Password
        response = self.client.post(
            '/api/login',
            data=json.dumps({
                'username': 'testloginuser',
                'password': 'wrongpassword'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid username or password', response.get_data(as_text=True))

        # Test Case 3: Non-existent User
        response = self.client.post(
            '/api/login',
            data=json.dumps({
                'username': 'nosuchuser',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn('Invalid username or password', response.get_data(as_text=True))

    def test_friends_api(self):
        """Test the full friend request and management workflow."""
        # --- Setup: Create users and log in ---
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='david', email='david@example.com')
        u1.set_password('cat')
        u2.set_password('dog')
        u3.set_password('pass')
        u2.is_online = True
        u2.ip_address = '192.168.1.100'
        u2.port = 8888
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # Login user 1 to get a token
        response = self.client.post('/api/login', data=json.dumps({'username': 'john', 'password': 'cat'}), content_type='application/json')
        token1 = response.get_json()['token']
        headers1 = {'Authorization': f'Bearer {token1}'}

        # Login user 2 to get a token
        response = self.client.post('/api/login', data=json.dumps({'username': 'susan', 'password': 'dog'}), content_type='application/json')
        token2 = response.get_json()['token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # --- Test Friend Request Flow ---
        # Test Case 1: John sends a friend request to Susan
        with patch('app.api.friends.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/friend-requests',
                headers=headers1,
                data=json.dumps({'username': 'susan'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            self.assertIn('Friend request sent successfully', response.get_data(as_text=True))
            mock_emit.assert_called_once() # Verify WebSocket notification was sent

        # Test Case 2: Susan gets her friend requests
        response = self.client.get('/api/friend-requests', headers=headers2)
        self.assertEqual(response.status_code, 200)
        requests = response.get_json()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['requester_username'], 'john')
        request_id = requests[0]['id']

        # Test Case 3: Susan accepts the friend request
        response = self.client.put(
            f'/api/friend-requests/{request_id}',
            headers=headers2,
            data=json.dumps({'action': 'accept'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Friend request accepted successfully', response.get_data(as_text=True))

        # Test Case 4: Verify they are now friends
        # Check John's friends
        response = self.client.get('/api/friends', headers=headers1)
        self.assertEqual(response.status_code, 200)
        friends_list1 = response.get_json()
        self.assertEqual(len(friends_list1), 1)
        self.assertEqual(friends_list1[0]['username'], 'susan')
        # Check Susan's friends
        response = self.client.get('/api/friends', headers=headers2)
        self.assertEqual(response.status_code, 200)
        friends_list2 = response.get_json()
        self.assertEqual(len(friends_list2), 1)
        self.assertEqual(friends_list2[0]['username'], 'john')

        # --- Test Remove Friend ---
        # Test Case 5: John removes Susan as a friend
        friend_to_remove_id = User.query.filter_by(username='susan').first().id
        response = self.client.delete(f'/api/friends/{friend_to_remove_id}', headers=headers1)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Friend removed successfully', response.get_data(as_text=True))

        # Verify Susan is no longer in John's friend list
        response = self.client.get('/api/friends', headers=headers1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 0)

    def test_online_user_info_api(self):
        """Test the API for getting online user information."""
        # 1. Create two users
        u1 = User(username='user1', email='user1@example.com')
        u1.set_password('pw1')
        u2 = User(username='user2', email='user2@example.com')
        u2.set_password('pw2')
        db.session.add_all([u1, u2])
        db.session.commit()

        # 2. Login as user1 to get a token and set online status
        response = self.client.post('/api/login', data=json.dumps({'username': 'user1', 'password': 'pw1'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # Simulate user1 being online after login
        user1 = User.query.filter_by(username='user1').first()
        user1.is_online = True
        user1.ip_address = '127.0.0.1'
        user1.port = 5000
        db.session.commit()

        # 3. Login as user2 to get a token
        response = self.client.post('/api/login', data=json.dumps({'username': 'user2', 'password': 'pw2'}), content_type='application/json')
        token2 = response.get_json()['token']
        headers2 = {'Authorization': f'Bearer {token2}'}

        # 4. As user2, try to get user1's info (should be denied)
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Access denied', response.get_data(as_text=True))

        # 5. Add user1 and user2 as friends
        u1.add_friend(u2)
        db.session.commit()

        # 6. As user2, try to get user1's info again (should succeed now)
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['is_online'])
        self.assertEqual(data['ip_address'], '127.0.0.1')
        self.assertEqual(data['port'], 5000)

        # 7. Simulate user1 disconnecting
        user1.is_online = False
        user1.ip_address = None
        user1.port = None
        db.session.commit()

        # 8. As user2, get user1's info (should show offline)
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['is_online'])

    def test_public_key_api(self):
        """Test the public key upload and retrieval API."""
        # Create a user and log them in to get a token
        u1 = User(username='key_user', email='key@example.com')
        u1.set_password('secret')
        db.session.add(u1)
        db.session.commit()

        login_resp = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'key_user', 'password': 'secret'}),
            content_type='application/json'
        )
        token = login_resp.get_json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Test Case 1: Upload a public key
        public_key_data = "----BEGIN PUBLIC KEY----\\nFAKE_KEY_CONTENT\\n----END PUBLIC KEY----"
        upload_resp = self.client.post(
            '/api/keys',
            headers=headers,
            data=json.dumps({'public_key': public_key_data}),
            content_type='application/json'
        )
        self.assertEqual(upload_resp.status_code, 200)
        self.assertIn('Public key updated successfully', upload_resp.get_data(as_text=True))

        # Test Case 2: Retrieve the public key by username
        get_key_resp = self.client.get(f'/api/users/key_user/public_key', headers=headers)
        self.assertEqual(get_key_resp.status_code, 200)
        key_data = get_key_resp.get_json()
        self.assertEqual(key_data['username'], 'key_user')
        self.assertEqual(key_data['public_key'], public_key_data)

        # Test Case 3: Try to retrieve key for a user who hasn't uploaded one
        u2 = User(username='nokey_user', email='nokey@example.com')
        u2.set_password('pass')
        db.session.add(u2)
        db.session.commit()
        get_key_resp_fail = self.client.get(f'/api/users/nokey_user/public_key', headers=headers)
        self.assertEqual(get_key_resp_fail.status_code, 404)
        self.assertIn('User has not uploaded a public key', get_key_resp_fail.get_data(as_text=True))

    def test_admin_api(self):
        """Test admin-only API endpoints."""
        # Create users: one admin, one regular
        admin_user = User(username='admin', email='admin@example.com', is_admin=True)
        admin_user.set_password('adminpass')
        reg_user = User(username='regular', email='regular@example.com')
        reg_user.set_password('regpass')
        db.session.add_all([admin_user, reg_user])
        db.session.commit()

        # --- Login as regular user ---
        login_resp_reg = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'regular', 'password': 'regpass'}),
            content_type='application/json'
        )
        reg_token = login_resp_reg.get_json()['token']
        reg_headers = {'Authorization': f'Bearer {reg_token}'}

        # Test Case 1: Regular user tries to access admin route
        response_reg = self.client.get('/api/admin/users', headers=reg_headers)
        self.assertEqual(response_reg.status_code, 403)
        self.assertIn('Administrator access required', response_reg.get_data(as_text=True))

        # --- Login as admin user ---
        login_resp_admin = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'admin', 'password': 'adminpass'}),
            content_type='application/json'
        )
        admin_token = login_resp_admin.get_json()['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # Test Case 2: Admin user successfully accesses admin route
        response_admin = self.client.get('/api/admin/users', headers=admin_headers)
        self.assertEqual(response_admin.status_code, 200)
        user_list = response_admin.get_json()
        self.assertIsInstance(user_list, list)
        # The database will contain users from other tests as well, so we check for presence
        usernames = [u['username'] for u in user_list]
        self.assertIn('admin', usernames)
        self.assertIn('regular', usernames)

        # --- Test Force Disconnect ---
        # To test this properly, we need to simulate a user being online.
        # We can't make a real socket connection here, but we can fake the state.
        reg_user_db = User.query.filter_by(username='regular').first()
        reg_user_db.is_online = True
        db.session.commit()

        # We need to mock the socketio and get_sid_by_username functions
        # as they won't work correctly without a live socketio server.
        with patch('app.api.admin.get_sid_by_username', return_value='fake_sid') as mock_get_sid:
            with patch('app.api.admin.socketio') as mock_socketio:
                
                # Test Case 3: Admin successfully disconnects an online user
                response = self.client.post(
                    '/api/admin/users/regular/disconnect',
                    headers=admin_headers
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn('Disconnect signal sent', response.get_data(as_text=True))
                
                # Verify that our mocked functions were called
                mock_get_sid.assert_called_once_with('regular')
                mock_socketio.disconnect.assert_called_once_with('fake_sid')

        # Test Case 4: Try to disconnect an offline user
        reg_user_db.is_online = False
        db.session.commit()
        response = self.client.post('/api/admin/users/regular/disconnect', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('User is already offline', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main(verbosity=2) 