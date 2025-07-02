import { io } from 'socket.io-client';

// 从环境变量读取后端地址，如果未设置则使用默认值
const URL = process.env.VUE_APP_SOCKET_URL || 'http://localhost:5000';

const socket = io(URL, {
  autoConnect: false, // 我们将手动连接
});

// 用于调试，监听所有事件
socket.onAny((event, ...args) => {
  console.log(`[Socket.io] received event: ${event}`, args);
});

export default socket; 