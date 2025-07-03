import { io } from 'socket.io-client';

// 重用为API配置的环境变量来设置Socket.io的连接地址
// 这样可以确保API请求和WebSocket连接都指向同一个后端
const URL = process.env.VUE_APP_API_BASE_URL || 'http://localhost:5000';

const socket = io(URL, {
  autoConnect: false, // 我们将手动连接
});

// 用于调试，监听所有事件
socket.onAny((event, ...args) => {
  console.log(`[Socket.io] received event: ${event}`, args);
});

export default socket; 