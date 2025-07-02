import unittest
import json
from app import create_app, db
from app.models import User
from config import TestingConfig
from unittest.mock import patch

# 用户模型相关测试用例
class UserModelCase(unittest.TestCase):
    def setUp(self):
        """
        设置测试环境。
        """
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """
        清理测试环境。
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """测试密码哈希和验证功能"""
        u = User(username='susan', email='susan@example.com')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))  # 错误密码应返回False
        self.assertTrue(u.check_password('cat'))   # 正确密码应返回True

    def test_registration(self):
        """测试用户注册接口"""
        # 测试用例1：注册成功
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

        # 测试用例2：用户名重复
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

        # 测试用例3：缺少密码
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
        """测试用户登录接口."""
        # 首先注册一个用户作为测试对象
        self.client.post(
            '/api/register',
            data=json.dumps({
                'username': 'testloginuser',
                'email': 'login@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )

        # 测试用例1：登录成功
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

        # 测试用例2：密码错误
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

        # 测试用例3：用户不存在
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
        """测试整个好友请求和管理的工作流程."""
        # 设置：创建用户并登录
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

        # 登录用户1以获取令牌
        response = self.client.post('/api/login', data=json.dumps({'username': 'john', 'password': 'cat'}), content_type='application/json')
        token1 = response.get_json()['token']
        headers1 = {'Authorization': f'Bearer {token1}'}

        # 登录用户2以获取令牌
        response = self.client.post('/api/login', data=json.dumps({'username': 'susan', 'password': 'dog'}), content_type='application/json')
        token2 = response.get_json()['token']
        headers2 = {'Authorization': f'Bearer {token2}'}
        
        # 测试好友请求流程
        # 测试用例1：用户1向用户2发送好友请求
        with patch('app.api.friends.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/friend-requests',
                headers=headers1,
                data=json.dumps({'username': 'susan'}),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 201)
            self.assertIn('Friend request sent successfully', response.get_data(as_text=True))
            mock_emit.assert_called_once() # 验证WebSocket通知已发送

        # 测试用例2：用户2获取她的好友请求
        response = self.client.get('/api/friend-requests', headers=headers2)
        self.assertEqual(response.status_code, 200)
        requests = response.get_json()
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]['requester_username'], 'john')
        request_id = requests[0]['id']

        # 测试用例3：用户2接受好友请求
        response = self.client.put(
            f'/api/friend-requests/{request_id}',
            headers=headers2,
            data=json.dumps({'action': 'accept'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Friend request accepted successfully', response.get_data(as_text=True))

        # 测试用例4：验证他们现在是朋友
        # 检查用户1的朋友列表
        response = self.client.get('/api/friends', headers=headers1)
        self.assertEqual(response.status_code, 200)
        friends_list1 = response.get_json()
        self.assertEqual(len(friends_list1), 1)
        self.assertEqual(friends_list1[0]['username'], 'susan')
        # 检查用户2的朋友列表
        response = self.client.get('/api/friends', headers=headers2)
        self.assertEqual(response.status_code, 200)
        friends_list2 = response.get_json()
        self.assertEqual(len(friends_list2), 1)
        self.assertEqual(friends_list2[0]['username'], 'john')

        # --- 测试移除好友 ---
        # 测试用例5：用户1移除用户2为好友
        friend_to_remove_id = User.query.filter_by(username='susan').first().id
        response = self.client.delete(f'/api/friends/{friend_to_remove_id}', headers=headers1)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Friend removed successfully', response.get_data(as_text=True))

        # 验证用户2不再用户1的好友列表中
        response = self.client.get('/api/friends', headers=headers1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 0)

    def test_online_user_info_api(self):
        """测试获取在线用户信息的API."""
        # 1. 创建两个用户
        u1 = User(username='user1', email='user1@example.com')
        u1.set_password('pw1')
        u2 = User(username='user2', email='user2@example.com')
        u2.set_password('pw2')
        db.session.add_all([u1, u2])
        db.session.commit()

        # 2. 登录user1以获取令牌并设置在线状态
        response = self.client.post('/api/login', data=json.dumps({'username': 'user1', 'password': 'pw1'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        
        # 模拟user1登录后在线
        user1 = User.query.filter_by(username='user1').first()
        user1.is_online = True
        user1.ip_address = '127.0.0.1'
        user1.port = 5000
        db.session.commit()

        # 3. 登录user2以获取令牌
        response = self.client.post('/api/login', data=json.dumps({'username': 'user2', 'password': 'pw2'}), content_type='application/json')
        token2 = response.get_json()['token']
        headers2 = {'Authorization': f'Bearer {token2}'}

        # 4. 作为user2，尝试获取user1的信息，应被拒绝
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 403)
        self.assertIn('Access denied', response.get_data(as_text=True))

        # 5. 将user1和user2互加为好友
        u1.add_friend(u2)
        db.session.commit()

        # 6. 作为user2，再次尝试获取user1的信息，现在应成功
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['is_online'])
        self.assertEqual(data['ip_address'], '127.0.0.1')
        self.assertEqual(data['port'], 5000)

        # 7. 模拟user1断开连接
        user1.is_online = False
        user1.ip_address = None
        user1.port = None
        db.session.commit()

        # 8. 作为user2，获取user1的信息，应显示为离线
        response = self.client.get('/api/users/user1/info', headers=headers2)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertFalse(data['is_online'])

    def test_public_key_api(self):
        """测试公钥上传和检索的API."""
        # 创建一个用户并登录以获取令牌
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
        
        # 测试用例1：上传公钥
        public_key_data = "----BEGIN PUBLIC KEY----\\nFAKE_KEY_CONTENT\\n----END PUBLIC KEY----"
        upload_resp = self.client.post(
            '/api/keys',
            headers=headers,
            data=json.dumps({'public_key': public_key_data}),
            content_type='application/json'
        )
        self.assertEqual(upload_resp.status_code, 200)
        self.assertIn('Public key updated successfully', upload_resp.get_data(as_text=True))

        # 测试用例2：通过用户名检索公钥
        get_key_resp = self.client.get(f'/api/users/key_user/public_key', headers=headers)
        self.assertEqual(get_key_resp.status_code, 200)
        key_data = get_key_resp.get_json()
        self.assertEqual(key_data['username'], 'key_user')
        self.assertEqual(key_data['public_key'], public_key_data)

        # 测试用例3：尝试检索未上传公钥的用户的公钥
        u2 = User(username='nokey_user', email='nokey@example.com')
        u2.set_password('pass')
        db.session.add(u2)
        db.session.commit()
        get_key_resp_fail = self.client.get(f'/api/users/nokey_user/public_key', headers=headers)
        self.assertEqual(get_key_resp_fail.status_code, 404)
        self.assertIn('User has not uploaded a public key', get_key_resp_fail.get_data(as_text=True))

    def test_admin_api(self):
        """测试仅限管理员的API端点."""
        # 创建用户：一个管理员，一个普通用户
        admin_user = User(username='admin', email='admin@example.com', is_admin=True)
        admin_user.set_password('adminpass')
        reg_user = User(username='regular', email='regular@example.com')
        reg_user.set_password('regpass')
        db.session.add_all([admin_user, reg_user])
        db.session.commit()

        # 以普通用户身份登录
        login_resp_reg = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'regular', 'password': 'regpass'}),
            content_type='application/json'
        )
        reg_token = login_resp_reg.get_json()['token']
        reg_headers = {'Authorization': f'Bearer {reg_token}'}

        # 测试用例1：普通用户尝试访问管理员路由
        response_reg = self.client.get('/api/admin/users', headers=reg_headers)
        self.assertEqual(response_reg.status_code, 403)
        self.assertIn('Administrator access required', response_reg.get_data(as_text=True))

        # 以管理员身份登录
        login_resp_admin = self.client.post(
            '/api/login',
            data=json.dumps({'username': 'admin', 'password': 'adminpass'}),
            content_type='application/json'
        )
        admin_token = login_resp_admin.get_json()['token']
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 测试用例2：管理员成功访问管理员路由
        response_admin = self.client.get('/api/admin/users', headers=admin_headers)
        self.assertEqual(response_admin.status_code, 200)
        user_list = response_admin.get_json()
        self.assertIsInstance(user_list, list)
        # 数据库中将包含其他测试的用户，因此我们只检查存在性
        usernames = [u['username'] for u in user_list]
        self.assertIn('admin', usernames)
        self.assertIn('regular', usernames)

        # 测试强制断开连接
        reg_user_db = User.query.filter_by(username='regular').first()
        reg_user_db.is_online = True
        db.session.commit()

        with patch('app.api.admin.get_sid_by_username', return_value='fake_sid') as mock_get_sid:
            with patch('app.api.admin.socketio') as mock_socketio:
                
                # 测试用例3：管理员成功断开在线用户
                response = self.client.post(
                    '/api/admin/users/regular/disconnect',
                    headers=admin_headers
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn('Disconnect signal sent', response.get_data(as_text=True))
                
                mock_get_sid.assert_called_once_with('regular')
                mock_socketio.disconnect.assert_called_once_with('fake_sid')

        # 测试用例4：尝试断开离线用户
        reg_user_db.is_online = False
        db.session.commit()
        response = self.client.post('/api/admin/users/regular/disconnect', headers=admin_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn('User is already offline', response.get_data(as_text=True))

if __name__ == '__main__':
    unittest.main(verbosity=2)