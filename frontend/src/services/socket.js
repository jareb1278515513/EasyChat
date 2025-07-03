/**
 * Socket.IO客户端服务
 * 封装与后端的实时通信功能
 */

import { io } from 'socket.io-client';

// 配置Socket连接URL
// 优先从环境变量VUE_APP_SOCKET_URL获取，否则使用本地开发地址
const URL = process.env.VUE_APP_SOCKET_URL || 'http://localhost:5000';

// 创建Socket实例
// 配置autoConnect为false以便在用户登录后手动连接
const socket = io(URL, {
  autoConnect: false, // 禁用自动连接，等待用户认证后手动连接
  reconnection: true, // 启用自动重连
  reconnectionAttempts: 5, // 最大重连次数
  reconnectionDelay: 1000 // 重连延迟，单位为ms
});

/**
 * 调试模式 - 监听所有Socket事件
 * 仅在开发环境生效
 */
if (process.env.NODE_ENV === 'development') {
  socket.onAny((event, ...args) => {
    console.log(`[Socket.io Debug] received event: ${event}`, args);
  });
}

// 导出Socket实例
export default socket;