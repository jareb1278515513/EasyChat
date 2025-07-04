import axios from 'axios';

// 从环境变量读取后端的基地址，如果未设置，则默认为本地开发地址
const API_BASE_URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 添加请求拦截器，在每个请求中附加 Token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

export default {
  register(userData) {
    return apiClient.post('/register', userData);
  },
  login(credentials) {
    return apiClient.post('/login', credentials);
  },
  getFriends() {
    return apiClient.get('/friends');
  },
  sendFriendRequest(username) {
    return apiClient.post('/friend-requests', { username: username });
  },
  getFriendRequests() {
    return apiClient.get('/friend-requests');
  },
  respondToFriendRequest(requestId, action) {
    return apiClient.put(`/friend-requests/${requestId}`, { action: action });
  },
  removeFriend(friendId) {
    return apiClient.delete(`/friends/${friendId}`);
  },
  getUserInfo(username) {
    return apiClient.get(`/users/${username}/info`);
  },
  uploadPublicKey(publicKey) {
    return apiClient.post('/keys', { public_key: publicKey });
  },
  getPublicKey(username, token) {
    return apiClient.get(`/users/${username}/public_key`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  },
  updateEmail(email) {
    return apiClient.put('/user/email', { email });
  },
  updatePassword(passwords) {
    return apiClient.put('/user/password', passwords);
  },
  updateProfile(profileData) {
    return apiClient.put('/user/profile', profileData);
  },
  getUserProfile(username) {
    return apiClient.get(`/users/${username}/profile`);
  },
  uploadAvatar(formData) {
    return apiClient.post('/user/avatar', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
  // Admin functions
  adminGetAllUsers() {
    return apiClient.get('/admin/users');
  },
  adminDisconnectUser(username) {
    return apiClient.post(`/admin/users/${username}/disconnect`);
  },
  adminDeleteUser(username) {
    return apiClient.delete(`/admin/users/${username}`);
  },
  // We can add other API calls here later
}; 