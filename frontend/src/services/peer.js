/**
 * PeerJS服务模块
 * 封装WebRTC点对点连接功能，用于直接用户间通信
 */

import Peer from 'peerjs';

// 全局Peer实例和ID
let peer = null;
let myPeerId = null;

/**
 * 初始化PeerJS连接
 * @param {string} username - 用作Peer ID的用户名
 * @returns {Peer} 返回Peer实例
 */
const initializePeer = (username) => {
  // 如果已有连接则先销毁
  if (peer && !peer.destroyed) {
    console.warn("Peer connection already exists. Destroying old one.");
    peer.destroy();
  }

  // 使用用户名作为Peer ID
  myPeerId = username;

  // 创建新的Peer实例
  peer = new Peer(myPeerId, {
    // 使用公共PeerJS服务器(开发环境)
    // 生产环境应部署私有PeerServer
    host: '0.peerjs.com',
    port: 443,
    path: '/',
    secure: true,
    debug: process.env.NODE_ENV === 'development' ? 2 : 0 // 开发环境开启详细日志
  });

  // 连接成功回调
  peer.on('open', (id) => {
    console.log('PeerJS connection established. My peer ID is: ' + id);
  });

  // 错误处理
  peer.on('error', (err) => {
    console.error('PeerJS error:', err);
  });

  // 断开连接处理
  peer.on('disconnected', () => {
    console.log('PeerJS disconnected. PeerJS will attempt to reconnect automatically.');
  });

  return peer;
};

/**
 * 获取当前Peer实例
 * @returns {Peer|null} 
 */
const getPeer = () => peer;

/**
 * 获取当前Peer ID
 * @returns {string|null} 
 */
const getPeerId = () => myPeerId;

/**
 * 销毁Peer连接
 */
const destroyPeer = () => {
  if (peer) {
    peer.destroy();
    peer = null;
    myPeerId = null;
    console.log('PeerJS connection destroyed.');
  }
};

// 导出Peer服务接口
export { initializePeer, getPeer, getPeerId, destroyPeer };