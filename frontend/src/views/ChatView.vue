<template>
  <div class="chat-container">
    <div class="sidebar">
      <div class="current-user-info">
        <img :src="currentUserAvatar || defaultAvatar" alt="My Avatar" class="avatar">
        <h4>{{ currentUser }}</h4>
      </div>
      
      <!-- Friend Requests Section -->
      <div v-if="friendRequests.length > 0" class="friend-requests bordered-and-shadowed">
        <h4>好友请求</h4>
        <ul>
          <li v-for="req in friendRequests" :key="req.id" class="friend-request-item">
            <span class="requester-name" @click="showFriendProfile(req.requester_username)" title="查看对方资料">{{ req.requester_username }}</span>
            <div class="actions">
              <button @click="respondToRequest(req.id, 'accept')" class="accept-btn">✓</button>
              <button @click="respondToRequest(req.id, 'reject')" class="reject-btn">×</button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Friends List Section -->
      <div class="friends-header">
        <h3>好友列表</h3>
        <button @click="fetchFriends" class="refresh-btn" title="刷新好友列表">🔄</button>
      </div>
      <div class="add-friend-form">
        <input type="text" v-model="newFriendUsername" @keyup.enter="sendRequest" placeholder="发送好友请求" class="bordered-and-shadowed">
        <button @click="sendRequest">+</button>
      </div>
      <ul class="friends-list">
        <li v-for="friend in friends" :key="friend.id" 
            @click="selectRecipient(friend.username)"
            :class="{ active: friend.username === currentRecipient }"
            class="bordered-and-shadowed">
          <img :src="friend.avatar_url || defaultAvatar" alt="Friend Avatar" class="avatar">
          <div class="friend-info">
            {{ friend.username }}
            <span :class="['status-dot', friend.is_online ? 'online' : 'offline']"></span>
            <span v-if="friend.hasNewMessages" class="new-message-indicator"></span>
          </div>
          <button @click.stop="removeFriend(friend.id)" class="remove-friend-btn">×</button>
        </li>
      </ul>

      <button v-if="isAdmin" @click="goToAdmin" class="admin-button">管理面板</button>
      <button @click="goToSettings" class="settings-button">设置</button>
      <button @click="logout" class="logout-button">登出</button>
    </div>
    <div class="chat-window">
      <div class="chat-header bordered-and-shadowed" v-if="currentRecipient">
        <span>正在与 <strong>{{ currentRecipient }}</strong> 聊天</span>
        <button @click="showFriendProfile(currentRecipient)" class="info-btn" title="查看好友信息">ℹ️</button>
      </div>
      <div class="messages-area bordered-and-shadowed">
        <div v-if="!currentRecipient" class="welcome-message">
          <p>选择一位好友开始聊天</p>
        </div>
        <div v-else class="messages-list">
          <div v-for="(msg, index) in messages[currentRecipient]" :key="index" :class="['message-wrapper', msg.from === currentUser ? 'sent' : 'received']">
            <img :src="msg.avatar_url || defaultAvatar" alt="Sender Avatar" class="avatar message-avatar">
            <div class="message-content">
              <span class="sender-name">{{ msg.from }}</span>
              <div :class="['message', msg.from === currentUser ? 'sent-bubble' : 'received-bubble']">
            <template v-if="msg.type === 'steganography_image'">
                  <img :src="msg.imageUrl" alt="隐写图片" class="chat-image" @click="revealMessage(msg.imageUrl)">
              <button @click="revealMessage(msg.imageUrl)" class="reveal-btn">显示隐藏信息</button>
            </template>
            <template v-else>
              {{ msg.message }}
            </template>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="message-input" v-if="currentRecipient">
        <div v-if="selectedImageFile" class="image-preview">
          <img :src="imagePreviewUrl" alt="预览">
          <button @click="clearSelectedImage" class="clear-preview-btn">×</button>
        </div>
        <input type="file" ref="imageInput" @change="handleImageSelected" accept="image/*" style="display: none;">
        <button @click="triggerImageUpload" class="upload-btn" title="发送图片">🖼️</button>
        
        <!-- Emoji Picker Button and Component -->
        <div class="emoji-picker-container">
          <button @click="toggleEmojiPicker" class="upload-btn" title="选择表情">😃</button>
          <emoji-picker v-if="showEmojiPicker" @emoji-click="onEmojiClick" class="emoji-picker"></emoji-picker>
        </div>
        
        <input type="text" v-model="newMessage" @keyup.enter="sendMessage" :placeholder="imagePreviewUrl ? '输入要隐藏在图片中的消息...' : '输入消息...'" class="bordered-and-shadowed">
        <button @click="sendMessage">发送</button>
      </div>
    </div>

    <!-- Friend Profile Modal -->
    <div v-if="showProfileModal" class="modal-overlay" @click.self="closeProfileModal">
      <div class="modal-content bordered-and-shadowed">
        <h3>{{ friendProfile.username }} 的资料</h3>
        <div class="profile-details">
          <p><strong>性别:</strong> {{ friendProfile.gender || '未指定' }}</p>
          <p><strong>年龄:</strong> {{ friendProfile.age || '未指定' }}</p>
          <p><strong>简介:</strong></p>
          <p class="bio">{{ friendProfile.bio || '这个人很懒，什么也没留下~' }}</p>
        </div>
        <button @click="closeProfileModal" class="close-modal-btn">关闭</button>
      </div>
    </div>

  </div>
</template>

<script>
import 'emoji-picker-element'; // 导入 emoji-picker 组件
import socket from '@/services/socket';
import api from '@/services/api';
import * as crypto from '@/utils/crypto';
import * as steganography from '@/utils/steganography';
import { getPeer, destroyPeer, encodeUsernameForPeerId, decodeUsernameFromPeerId } from '@/services/peer';

const DEFAULT_AVATAR = require('@/assets/logo.png');

// Store for active PeerJS data connections, and symmetric keys for each chat session.
const dataConnections = {};
const symmetricKeys = {};

export default {
  name: 'ChatView',
  data() {
    return {
      friends: [],
      friendRequests: [],
      messages: {},
      newMessage: '',
      currentRecipient: null,
      newFriendUsername: '',
      statusInterval: null,
      currentUser: '',
      currentUserAvatar: null,
      defaultAvatar: DEFAULT_AVATAR,
      selectedImageFile: null,
      imagePreviewUrl: null,
      isAdmin: false,
      showEmojiPicker: false, // 控制 emoji 选择器的显示状态
      showProfileModal: false, // 控制好友资料模态框的显示
      friendProfile: null // 存储正在查看的好友资料
    };
  },
  methods: {
    async fetchCurrentUserInfo() {
      try {
        const { data } = await api.getUserProfile(this.currentUser);
        this.currentUserAvatar = data.avatar_url;
      } catch (error) {
        console.error("无法获取当前用户信息:", error);
      }
    },
    initializePeer() {
      const peer = getPeer();
      if (peer) {
        peer.on('connection', (conn) => {
          const recipientUsername = decodeUsernameFromPeerId(conn.peer);
          console.log(`收到来自 ${recipientUsername} 的传入连接`);
          this.setupConnectionHandlers(conn, recipientUsername);
        });
        peer.on('error', (err) => {
          console.error('发生全局对等端错误:', err);
          if (err.type === 'peer-unavailable') {
            alert(`无法连接到 ${this.currentRecipient}。对方可能已离线或无法访问。`);
          }
        });
      } else {
        alert("P2P服务不可用，请重新登录。");
        this.$router.push('/');
      }
    },
    checkIfAdmin() {
      const username = localStorage.getItem('username');
      if (username === 'admin') {
        this.isAdmin = true;
      }
    },
    goToAdmin() {
      this.$router.push('/admin');
    },
    goToSettings() {
      this.$router.push('/settings');
    },
    // --- PeerJS Connection Management ---
    selectRecipient(username) {
      this.currentRecipient = username;
      if (!this.messages[username]) {
        this.messages[username] = [];
      }
      const friend = this.friends.find(f => f.username === username);
      if (friend) {
        friend.hasNewMessages = false;
      }
      
      // New, more robust connection logic
      if (!dataConnections[username]) {
        console.log(`No connection to ${username} found. Attempting to connect.`);
        const peer = getPeer();
        if (peer) {
          const encodedUsername = encodeUsernameForPeerId(username);
          const conn = peer.connect(encodedUsername, { reliable: true });
          this.setupConnectionHandlers(conn, username);
        } else {
          alert("P2P服务不可用，请重新登录。");
        }
      } else if (!dataConnections[username].open) {
        console.log(`与 ${username} 的连接已存在但尚未打开，请等待。`);
      } else {
        console.log(`与 ${username} 的连接已打开。`);
        if (!symmetricKeys[username]) {
          console.log(`连接已打开但缺少对称密钥，重新发起密钥交换。`);
          this.performKeyExchange(username, dataConnections[username]);
        }
      }
    },

    setupConnectionHandlers(conn, recipientUsername) {
      // Make this function idempotent by cleaning up old listeners
      conn.off('data');
      conn.off('open');
      conn.off('close');
      conn.off('error');
      
      dataConnections[recipientUsername] = conn;
      
      conn.on('data', (data) => {
        this.handleNewP2PMessage({ from: recipientUsername, rawMessage: data });
      });

      conn.on('open', () => {
        console.log(`与 ${recipientUsername} 的数据连接已打开。准备进行密钥交换...`);

        // To prevent race conditions where both peers try to initiate key exchange,
        // we use a simple convention: the peer with the lexicographically smaller username
        // is responsible for initiating the exchange.
        const amIInitiator = this.currentUser < recipientUsername;

        if (amIInitiator && !symmetricKeys[recipientUsername]) {
          console.log(`我 (${this.currentUser}) 的用户名较小，将发起与 ${recipientUsername} 的密钥交换。`);
          this.performKeyExchange(recipientUsername, conn);
        } else if (!amIInitiator) {
          console.log(`我 (${this.currentUser}) 的用户名较大，将等待 ${recipientUsername} 发起密钥交换。`);
        } else if (symmetricKeys[recipientUsername]) {
          console.log(`已存在与 ${recipientUsername} 的密钥，无需再次交换。`);
        }
      });

      conn.on('close', () => {
        console.log(`与 ${recipientUsername} 的连接已关闭。`);
        delete dataConnections[recipientUsername];
        delete symmetricKeys[recipientUsername];
      });

      conn.on('error', (err) => {
        console.error(`与 ${recipientUsername} 的连接发生错误:`, err);
      });
    },

    // --- E2EE and Messaging ---
    async performKeyExchange(recipientUsername, conn) {
      try {
        console.log(`正在与 ${recipientUsername} 开始密钥交换...`);
        // 1. Generate our own AES key
        const aesKey = await crypto.generateSymmetricKey();
        symmetricKeys[recipientUsername] = aesKey;

        // 2. Get recipient's public key from server
        const { data } = await api.getPublicKey(recipientUsername);
        const friendPublicKey = await crypto.importPublicKey(data.public_key);

        // 3. Encrypt our AES key with their public key
        const exportedKey = await window.crypto.subtle.exportKey('raw', aesKey);
        const encryptedKey = await crypto.encryptWithPublicKey(friendPublicKey, exportedKey);

        // 4. Send the encrypted key as a JSON string
        conn.send(JSON.stringify({ type: 'key_exchange', payload: Array.from(new Uint8Array(encryptedKey)) }));
        console.log(`已向 ${recipientUsername} 发送加密的AES密钥。`);

      } catch (error) {
        console.error(`与 ${recipientUsername} 的密钥交换失败:`, error);
        alert(`无法与 ${recipientUsername} 建立安全连接。`);
        // Clean up on failure
        delete symmetricKeys[recipientUsername];
        if (conn) conn.close();
      }
    },

    async handleNewP2PMessage({ from, rawMessage }) {
      const recipientUsername = from;

      let message;
      try {
        message = JSON.parse(rawMessage);
      } catch (error) {
        console.error("无法解析传入的 P2P 消息:", rawMessage, error);
        return;
      }

      if (message.type === 'key_exchange') {
        try {
          console.log(`收到来自 ${recipientUsername} 的密钥交换请求。`);
          const privateKeyPem = localStorage.getItem('privateKey');
          if (!privateKeyPem) throw new Error("无法加载私钥。");
          
          const privateKey = await crypto.importPrivateKey(privateKeyPem);
          const encryptedKey = new Uint8Array(message.payload).buffer;
          const decryptedKey = await crypto.decryptWithPrivateKey(privateKey, encryptedKey);
          
          symmetricKeys[recipientUsername] = await window.crypto.subtle.importKey(
            'raw', 
            decryptedKey, 
            { name: 'AES-GCM', length: 256 }, 
            true, 
            ['encrypt', 'decrypt']
          );
          console.log(`已与 ${recipientUsername} 建立安全通道。`);
        } catch (error) {
          console.error(`处理来自 ${recipientUsername} 的密钥交换时出错:`, error);
          alert(`无法与 ${recipientUsername} 建立安全连接。`);
        }
        return;
      }

      const key = symmetricKeys[recipientUsername];
      if (!key) {
        console.warn(`收到来自 ${recipientUsername} 的消息，但没有对称密钥。忽略此消息。`);
        return;
      }

      if (message.type === 'steganography_image') {
        if (!this.messages[recipientUsername]) this.messages[recipientUsername] = [];
        this.messages[recipientUsername].push({
          from: recipientUsername,
          type: 'steganography_image',
          imageUrl: message.payload,
          avatar_url: this.friends.find(f => f.username === recipientUsername)?.avatar_url || this.defaultAvatar
        });
        
        if (this.currentRecipient !== recipientUsername) {
          const friend = this.friends.find(f => f.username === recipientUsername);
          if (friend) {
            friend.hasNewMessages = true;
          }
        }
        return;
      }

      if (message.type === 'chat_message') {
        try {
          const { iv, ciphertext } = message;
          const plaintext = await crypto.decryptSymmetric(key, new Uint8Array(ciphertext).buffer, new Uint8Array(iv));
          
          const messageToStore = {
            from: recipientUsername,
            message: plaintext,
            avatar_url: this.friends.find(f => f.username === recipientUsername)?.avatar_url || this.defaultAvatar,
          };

          if (!this.messages[recipientUsername]) {
            this.$set(this.messages, recipientUsername, []);
          }
          this.messages[recipientUsername].push(messageToStore);

          if (this.currentRecipient !== recipientUsername) {
            const friend = this.friends.find(f => f.username === recipientUsername);
            if (friend) {
              friend.hasNewMessages = true;
            }
          }
        } catch (error) {
          console.error(`解密来自 ${recipientUsername} 的消息时出错:`, error);
        }
      }
    },

    // --- Message Sending ---
    async sendMessage() {
      if (!this.newMessage.trim() && !this.selectedImageFile) return;
      if (!this.currentRecipient) return;

      if (this.selectedImageFile) {
        const conn = dataConnections[this.currentRecipient];
        if (!conn || !conn.open) {
          alert('无法发送图片：安全连接尚未建立。');
          return;
        }
        try {
          const imageDataUrl = await steganography.hideMessage(this.selectedImageFile, this.newMessage);
          
          conn.send(JSON.stringify({
            type: 'steganography_image',
            payload: imageDataUrl
          }));

          if (!this.messages[this.currentRecipient]) this.messages[this.currentRecipient] = [];
          this.messages[this.currentRecipient].push({
            from: this.currentUser,
            type: 'steganography_image',
            imageUrl: imageDataUrl,
            avatar_url: this.currentUserAvatar
          });
          
          this.clearSelectedImage();
          this.newMessage = '';

        } catch (error) {
          console.error('信息隐藏或发送失败:', error);
          alert('发送图片失败：' + error.message);
        }
        return;
      }
      
      // Standard P2P message sending
      const conn = dataConnections[this.currentRecipient];
      if (conn && conn.open) {
        const key = symmetricKeys[this.currentRecipient];
        if (!key) {
          alert("错误：无法发送消息。与此用户的安全连接尚未建立。");
          return;
        }
        try {
          const { iv, ciphertext } = await crypto.encryptSymmetric(key, this.newMessage);
          
          conn.send(JSON.stringify({
            type: 'chat_message',
            iv: Array.from(iv),
            ciphertext: Array.from(new Uint8Array(ciphertext))
          }));

          if (!this.messages[this.currentRecipient]) this.messages[this.currentRecipient] = [];
          this.messages[this.currentRecipient].push({ from: this.currentUser, message: this.newMessage, avatar_url: this.currentUserAvatar });
          this.newMessage = '';
        } catch (error) {
          console.error('发送消息失败:', error);
          alert('发送安全消息失败。');
        }
      } else {
        alert('安全连接尚未建立，无法发送消息。');
      }
    },

    // --- UI and Data Fetching ---
    logout() {
      console.log('正在登出...');
      destroyPeer();
      if (socket.connected) socket.disconnect();
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      localStorage.removeItem('privateKey');
      this.$router.push('/');
    },

    fetchFriends() {
      api.getFriends()
        .then(response => {
          const newFriends = response.data;
          // Preserve new message indicators
          newFriends.forEach(newFriend => {
            const oldFriend = this.friends.find(f => f.id === newFriend.id);
            if (oldFriend) {
              newFriend.hasNewMessages = oldFriend.hasNewMessages;
            } else {
              newFriend.hasNewMessages = false; // Initialize for new friends
            }
          });
          this.friends = newFriends;
        })
        .catch(error => console.error('获取好友列表时出错:', error));
    },

    fetchFriendRequests() {
      api.getFriendRequests()
        .then(response => {
          this.friendRequests = response.data;
        })
        .catch(error => console.error('获取好友请求时出错:', error));
    },
    
    sendRequest() {
      if (!this.newFriendUsername.trim()) return;
      api.sendFriendRequest(this.newFriendUsername)
        .then(() => {
          alert('好友请求已发送。');
          this.newFriendUsername = '';
        })
        .catch(error => alert('发送请求失败: ' + (error.response?.data?.message || error.message)));
    },

    respondToRequest(requestId, action) {
      api.respondToFriendRequest(requestId, action)
        .then(() => {
          alert(`请求已${action === 'accept' ? '接受' : '拒绝'}。`);
          this.fetchFriendRequests();
          this.fetchFriends();
        })
        .catch(error => alert('响应请求失败: ' + (error.response?.data?.message || error.message)));
    },
    
    removeFriend(friendId) {
      if (confirm('您确定要删除这位好友吗？')) {
        api.removeFriend(friendId)
          .then(() => {
            alert('好友已删除。');
            this.fetchFriends();
          })
          .catch(error => alert('删除好友失败: ' + (error.response?.data?.message || error.message)));
      }
    },

    triggerImageUpload() {
      this.$refs.imageInput.click();
    },

    handleImageSelected(event) {
      const file = event.target.files[0];
      if (file && file.type.startsWith('image/')) {
        this.selectedImageFile = file;
        this.imagePreviewUrl = URL.createObjectURL(file);
      } else {
        this.clearSelectedImage();
      }
    },

    clearSelectedImage() {
      this.selectedImageFile = null;
      if (this.imagePreviewUrl) {
        URL.revokeObjectURL(this.imagePreviewUrl);
      }
      this.imagePreviewUrl = null;
      this.$refs.imageInput.value = ''; // Reset file input
    },
    
    async revealMessage(imageUrl) {
      try {
        const hiddenMessage = await steganography.extractMessage(imageUrl);
        if (hiddenMessage) {
          alert(`图片中的隐藏信息: \n\n${hiddenMessage}`);
        } else {
          alert('此图片中未发现隐藏信息。');
        }
      } catch (error) {
        console.error('提取信息时出错:', error);
        alert('提取信息失败：' + error.message);
      }
    },
    // --- Emoji Picker Methods ---
    toggleEmojiPicker() {
      this.showEmojiPicker = !this.showEmojiPicker;
    },
    onEmojiClick(event) {
      this.newMessage += event.detail.unicode;
      this.showEmojiPicker = false; // 选择后自动关闭
    },
    // --- Profile Modal ---
    async showFriendProfile(username) {
      try {
        const { data } = await api.getUserProfile(username);
        this.friendProfile = data;
        this.showProfileModal = true;
      } catch (error) {
        alert('获取好友资料失败: ' + (error.response?.data?.error || '未知错误'));
      }
    },
    closeProfileModal() {
      this.showProfileModal = false;
      this.friendProfile = null;
    },
  },
  created() {
    this.currentUser = localStorage.getItem('username') || '用户';
    this.fetchCurrentUserInfo();
    this.checkIfAdmin();
    this.initializePeer();
    this.fetchFriends();
    this.fetchFriendRequests();

    // Listen for new friend requests
    socket.on('new_friend_request', (request) => {
      console.log('New friend request received:', request);
      this.friendRequests.unshift(request); // Add to the top of the list
      alert(`您收到了来自 ${request.requester_username} 的好友请求！`);
    });

    this.statusInterval = setInterval(this.fetchFriends, 10000);
  },
  beforeUnmount() {
    // Clean up socket listeners
    socket.off('new_friend_request');

    if (this.statusInterval) {
      clearInterval(this.statusInterval);
    }
    // Note: PeerJS connection is destroyed on logout, not just component unmount
  },
  mounted() {
    // We moved most logic to created() to ensure socket listeners are set up early.
    // mounted() can be used for DOM-specific manipulations if needed later.
  }
};
</script>

<style scoped>
/* 主题色定义 */
.chat-container {
  --input-focus: #2d8cf0;
  --font-color: #323232;
  --font-color-sub: #666;
  --bg-color: beige;
  --main-color: black;
  --base-bg: lightblue;
  --container-bg: #f0f2f5;
  --danger-color: #e74c3c;
  --success-color: #2ecc71;

  display: flex;
  height: 100vh;
  background-color: var(--container-bg);
  font-family: 'Helvetica Neue', sans-serif;
}

/* 共享样式类 */
.bordered-and-shadowed {
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background-color: var(--base-bg);
  border-right: 2px solid var(--main-color);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.current-user-info {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 0 10px;
}

.current-user-info h4, .friends-header h3, .friend-requests h4 {
  font-size: 22px;
  font-weight: 900;
  color: var(--font-color);
  text-align: center;
  margin: 0;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--main-color);
}

.friends-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.add-friend-form {
  display: flex;
  gap: 10px;
}

.add-friend-form input {
  flex-grow: 1;
}

/* 列表区域 */
.friends-list, .friend-requests ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
  overflow-y: auto;
  overflow-x: hidden; /* 防止水平溢出 */
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.friend-request-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
}

.requester-name {
  cursor: pointer;
  font-weight: 600;
  transition: color 0.2s;
}

.requester-name:hover {
  color: var(--input-focus, #2d8cf0);
}

.friend-request-item .actions {
  display: flex;
  gap: 8px; /* 为接受/拒绝按钮之间增加间距 */
}

.friends-list li {
  padding: 10px 15px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
}

.friends-list li:hover {
  transform: translate(2px, 2px);
  box-shadow: 2px 2px var(--main-color);
}

.friends-list li.active {
  background-color: var(--input-focus);
  color: white;
  box-shadow: 0 0 var(--main-color);
  transform: translate(4px, 4px);
}

.friend-info {
  flex-grow: 1;
  position: relative; /* For positioning the indicator */
}

/* 聊天窗口 */
.chat-window {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  gap: 20px;
}

.messages-area {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  text-align: center;
}

.welcome-message p {
  font-size: 1.5rem;
  color: #777;
  font-weight: 300;
}

.messages-list {
  display: flex;
  flex-direction: column;
}

.message-wrapper {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
  max-width: 85%;
}

.message-wrapper.sent {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.received {
  align-self: flex-start;
}

.message-avatar {
  width: 35px;
  height: 35px;
  margin: 0 10px;
  flex-shrink: 0; /* 防止头像被压缩 */
}

.message-content {
  display: flex;
  flex-direction: column;
}

.sender-name {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 4px;
}

.message-wrapper.sent .sender-name {
  align-self: flex-end;
}

.message-wrapper.received .sender-name {
  align-self: flex-start;
}

.message {
  padding: 10px 15px;
  max-width: fit-content;
  border-radius: 15px; /* 更圆润的聊天气泡 */
}
.sent-bubble {
  background-color: #dcf8c6;
  border-top-right-radius: 0;
}
.received-bubble {
  background-color: white;
  border-top-left-radius: 0;
}

/* 通用输入框和按钮样式 */
input[type="text"] {
  height: 45px;
  font-size: 16px;
  font-weight: 600;
  color: var(--font-color);
  padding: 5px 15px;
  outline: none;
  box-sizing: border-box;
}

input[type="text"]:focus {
  border: 2px solid var(--input-focus);
}

button {
  height: 45px;
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
  font-size: 16px;
  font-weight: 600;
  color: var(--font-color);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

button:active {
  box-shadow: 0px 0px var(--main-color);
  transform: translate(4px, 4px);
}

.logout-button, .settings-button, .admin-button {
  width: 100%;
}
.admin-button { background-color: #ffc107; }
.logout-button { background-color: var(--danger-color); }

.message-input {
  display: flex;
  gap: 10px;
  position: relative; /* For positioning the preview */
}
.message-input input { flex-grow: 1; }
.message-input button { width: 100px; }
.upload-btn { width: 50px; }

/* 其他小组件 */
.status-dot {
  height: 10px;
  width: 10px;
  background-color: #bbb;
  border-radius: 50%;
  display: inline-block;
  margin-left: 8px;
  border: 1px solid #333;
}

.status-dot.online {
  background-color: var(--success-color, #2ecc71);
}

.status-dot.offline {
  background-color: #ccc;
}

/* In-chat image styles */
.chat-image {
  max-width: 200px;
  max-height: 200px;
  border-radius: 5px;
  border: 2px solid var(--main-color);
  cursor: pointer;
  display: block;
  margin-top: 5px;
}

.message .reveal-btn {
  height: auto;
  padding: 5px 10px;
  font-size: 12px;
  margin-top: 10px;
}

/* Image Preview Styles */
.image-preview {
  position: absolute;
  bottom: 100%; /* Position above the input bar */
  left: 50px; /* Align with the text input area */
  margin-bottom: 10px;
  background: var(--bg-color);
  padding: 8px;
  border-radius: 5px;
  border: 2px solid var(--main-color);
  box-shadow: 4px 4px var(--main-color);
  z-index: 10;
}

.image-preview img {
  max-width: 80px;
  max-height: 80px;
  display: block;
  border-radius: 3px;
}

.clear-preview-btn {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 24px;
  height: 24px;
  font-size: 14px;
  line-height: 24px;
  text-align: center;
  padding: 0;
  color: white;
  background-color: var(--danger-color);
  border-radius: 50%;
  border: 2px solid var(--main-color);
}

/* Emoji Styles */
.emoji-picker-container {
  position: relative;
}

.emoji-picker {
  position: absolute;
  bottom: 50px; /* 定位到输入框上方 */
  right: 0;
  z-index: 1000;
}

/* Chat Header Styles */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  margin-bottom: 10px;
  background-color: #f5f5f5;
}

.info-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  font-weight: bold;
}

/* Profile Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.modal-content {
  background: var(--base-bg, lightblue);
  padding: 25px;
  border-radius: 5px;
  width: 90%;
  max-width: 400px;
  text-align: center;
}

.modal-content h3 {
  margin-top: 0;
  border-bottom: 2px solid var(--main-color, black);
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.profile-details {
  text-align: left;
  margin-bottom: 20px;
}

.profile-details p {
  margin: 10px 0;
}

.profile-details .bio {
  background-color: var(--bg-color, beige);
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  min-height: 50px;
  white-space: pre-wrap; /* Preserve line breaks */
}

.close-modal-btn {
  padding: 10px 20px;
  border: none;
  background-color: #4CAF50;
  color: white;
  border-radius: 20px;
  cursor: pointer;
}

/* Avatar Styles */
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid var(--main-color);
  margin-right: 10px; /* 为头像右侧增加间距 */
}

.new-message-indicator {
  position: absolute;
  right: 15px; /* Increased from 5px to create more space */
  top: 50%;
  transform: translateY(-50%);
  width: 10px; /* Matched to status-dot size */
  height: 10px; /* Matched to status-dot size */
  background-color: var(--danger-color, #e74c3c);
  border-radius: 50%;
  border: 1px solid #333; /* Matched to status-dot border */
}

</style> 