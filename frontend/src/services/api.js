// API服务模块 - 封装所有与后端API的交互

import axios from 'axios';

// 创建axios实例，配置基础URL和默认请求头
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:5000/api', // 从环境变量获取API地址，默认为本地开发地址
  headers: {
    'Content-Type': 'application/json' // 设置默认请求头为JSON格式
  }
});

/**
 * 请求拦截器 - 在每个请求中自动附加JWT Token
 * 从localStorage获取token并添加到请求头
 */
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => {
  return Promise.reject(error);
});

// 导出API方法集合
export default {
  // 用户认证相关API
  register(userData) {
    return apiClient.post('/register', userData); // 用户注册
  },
  login(credentials) {
    return apiClient.post('/login', credentials); // 用户登录
  },

  // 好友关系管理API
  getFriends() {
    return apiClient.get('/friends'); // 获取好友列表
  },
  sendFriendRequest(username) {
    return apiClient.post('/friend-requests', { username: username }); // 发送好友请求
  },
  getFriendRequests() {
    return apiClient.get('/friend-requests'); // 获取收到的好友请求
  },
  respondToFriendRequest(requestId, action) {
    return apiClient.put(`/friend-requests/${requestId}`, { action: action }); // 响应好友请求
  },
  removeFriend(friendId) {
    return apiClient.delete(`/friends/${friendId}`); // 删除好友
  },

  // 用户信息相关API
  getUserInfo(username) {
    return apiClient.get(`/users/${username}/info`); // 获取用户信息
  },
  updateEmail(email) {
    return apiClient.put('/user/email', { email }); // 更新用户邮箱
  },
  updatePassword(passwords) {
    return apiClient.put('/user/password', passwords); // 更新用户密码
  },

  // 加密相关API
  uploadPublicKey(publicKey) {
    return apiClient.post('/keys', { public_key: publicKey }); // 上传用户公钥
  },
  getPublicKey(username, token) {
    return apiClient.get(`/users/${username}/public_key`, { // 获取其他用户公钥
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
  },

  // 管理员功能API
  adminGetAllUsers() {
    return apiClient.get('/admin/users'); // 获取所有用户
  },
  adminDisconnectUser(username) {
    return apiClient.post(`/admin/users/${username}/disconnect`); // 强制断开用户连接
  },
  adminDeleteUser(username) {
    return apiClient.delete(`/admin/users/${username}`); // 删除用户
  }
};