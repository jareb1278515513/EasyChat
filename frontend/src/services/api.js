import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000/api',
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
  // We can add other API calls here later
}; 