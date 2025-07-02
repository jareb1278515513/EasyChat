<template>
  <div class="chat-container">
    <div class="sidebar">
      <div class="current-user-info">
        <h4>欢迎, {{ currentUser }}</h4>
      </div>
      
      <!-- Friend Requests Section -->
      <div class="friend-requests" v-if="friendRequests.length > 0">
        <h4>好友请求</h4>
        <ul>
          <li v-for="req in friendRequests" :key="req.id" class="friend-request-item">
            <span>{{ req.requester_username }}</span>
            <div class="actions">
              <button @click="respondToRequest(req.id, 'accept')" class="accept-btn">✓</button>
              <button @click="respondToRequest(req.id, 'reject')" class="reject-btn">×</button>
            </div>
          </li>
        </ul>
      </div>

      <!-- Friends List Section -->
      <div class="friends-header">
        <h3>好友</h3>
        <button @click="fetchFriends" class="refresh-btn" title="刷新好友列表">🔄</button>
      </div>
      <div class="add-friend-form">
        <input type="text" v-model="newFriendUsername" @keyup.enter="sendRequest" placeholder="发送好友请求">
        <button @click="sendRequest">+</button>
      </div>
      <ul class="friends-list">
        <li v-for="friend in friends" :key="friend.id" 
            @click="selectRecipient(friend.username)"
            :class="{ active: friend.username === currentRecipient }">
          <div class="friend-info">
            {{ friend.username }}
            <span :class="['status', friend.is_online ? 'online' : 'offline']"></span>
            <span v-if="friend.hasNewMessages" class="new-message-indicator"></span>
          </div>
          <button @click.stop="removeFriend(friend.id)" class="remove-friend-btn">×</button>
        </li>
      </ul>

      <button @click="logout" class="logout-button">登出</button>
    </div>
    <div class="chat-window">
      <div class="messages-area">
        <div v-if="!currentRecipient">选择一位好友开始聊天</div>
        <div v-else>
          <div v-for="(msg, index) in messages[currentRecipient]" :key="index" class="message">
            <strong>{{ msg.from }}:</strong>
            <template v-if="msg.type === 'steganography_image'">
              <img :src="msg.imageUrl" alt="Steganography Image" class="chat-image" @click="revealMessage(msg.imageUrl)">
              <button @click="revealMessage(msg.imageUrl)" class="reveal-btn">显示隐藏信息</button>
            </template>
            <template v-else>
              {{ msg.message }}
            </template>
          </div>
        </div>
      </div>
      <div class="message-input" v-if="currentRecipient">
        <div v-if="selectedImageFile" class="image-preview">
          <img :src="imagePreviewUrl" alt="Preview">
          <button @click="clearSelectedImage" class="clear-preview-btn">×</button>
        </div>
        <input type="file" ref="imageInput" @change="handleImageSelected" accept="image/*" style="display: none;">
        <button @click="triggerImageUpload" class="upload-btn" title="发送图片">🖼️</button>
        <input type="text" v-model="newMessage" @keyup.enter="sendMessage" :placeholder="imagePreviewUrl ? '输入要隐藏在图片中的消息...' : '输入消息...'">
        <button @click="sendMessage">发送</button>
      </div>
    </div>
  </div>
</template>

<script>
import socket from '@/services/socket';
import api from '@/services/api';
import * as crypto from '@/utils/crypto';
import * as steganography from '@/utils/steganography';
import { getPeer, destroyPeer } from '@/services/peer';

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
      selectedImageFile: null,
      imagePreviewUrl: null,
    };
  },
  methods: {
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
          const conn = peer.connect(username, { reliable: true });
          this.setupConnectionHandlers(conn);
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

    setupConnectionHandlers(conn) {
      // Make this function idempotent by cleaning up old listeners
      conn.off('data');
      conn.off('open');
      conn.off('close');
      conn.off('error');
      
      dataConnections[conn.peer] = conn;
      
      conn.on('data', (data) => {
        this.handleNewP2PMessage({ from: conn.peer, rawMessage: data });
      });

      conn.on('open', () => {
        console.log(`与 ${conn.peer} 的数据连接已打开。`);
        // The initiator of the connection is responsible for starting the key exchange
        if (this.currentRecipient === conn.peer && !symmetricKeys[conn.peer]) {
          this.performKeyExchange(conn.peer, conn);
        }
      });

      conn.on('close', () => {
        console.log(`与 ${conn.peer} 的连接已关闭。`);
        delete dataConnections[conn.peer];
        delete symmetricKeys[conn.peer];
      });

      conn.on('error', (err) => {
        console.error(`与 ${conn.peer} 的连接发生错误:`, err);
      });
    },

    // --- E2EE and Messaging ---
    async performKeyExchange(username, conn) {
      try {
        console.log(`正在与 ${username} 开始密钥交换`);
        const { data: { public_key: friendPublicKeyPem } } = await api.getPublicKey(username);
        const friendPublicKey = await crypto.importPublicKey(friendPublicKeyPem);
        const symmetricKey = await crypto.generateSymmetricKey();
        symmetricKeys[username] = symmetricKey;

        const exportedSymmetricKey = await window.crypto.subtle.exportKey('raw', symmetricKey);
        const encryptedSymmetricKey = await crypto.encryptWithPublicKey(friendPublicKey, exportedSymmetricKey);
        
        conn.send(JSON.stringify({ type: 'key_exchange', payload: Array.from(new Uint8Array(encryptedSymmetricKey)) }));
        console.log(`已将加密的对称密钥发送给 ${username}。`);
      } catch (err) {
        console.error('密钥交换失败:', err);
        alert('无法建立安全连接。');
        if (conn) conn.close();
      }
    },

    async handleNewP2PMessage(data) {
      const { from, rawMessage } = data;
      const message = typeof rawMessage === 'string' ? JSON.parse(rawMessage) : rawMessage;

      if (message.type === 'steganography_image') {
        if (!this.messages[from]) this.messages[from] = [];
        this.messages[from].push({
          from,
          type: 'steganography_image',
          imageUrl: message.payload,
        });
        return;
      }

      if (message.type === 'key_exchange') {
        try {
          console.log(`收到来自 ${from} 的密钥交换请求。`);
          const privateKeyPem = localStorage.getItem('privateKey');
          const privateKey = await crypto.importPrivateKey(privateKeyPem);
          const encryptedKey = new Uint8Array(message.payload).buffer;
          const decryptedKey = await crypto.decryptWithPrivateKey(privateKey, encryptedKey);
          symmetricKeys[from] = await window.crypto.subtle.importKey('raw', decryptedKey, { name: 'AES-GCM' }, true, ['encrypt', 'decrypt']);
          console.log(`与 ${from} 成功建立对称密钥。`);
          alert(`与 ${from} 的安全信道已建立！`);
        } catch (err) {
          console.error('处理密钥交换失败:', err);
        }
        return;
      }
      
      if (message.type === 'chat_message') {
        const symmetricKey = symmetricKeys[from];
        if (!symmetricKey) return console.warn(`没有找到 ${from} 的对称密钥。`);
        
        try {
          const { iv, ciphertext } = message;
          const plaintext = await crypto.decryptSymmetric(symmetricKey, new Uint8Array(ciphertext).buffer, new Uint8Array(iv));

          if (!this.messages[from]) this.messages[from] = [];
          this.messages[from].push({ from, message: plaintext });

          if (from !== this.currentRecipient) {
            const friend = this.friends.find(f => f.username === from);
            if (friend) friend.hasNewMessages = true;
          }
        } catch (err) {
          console.error('解密消息失败:', err);
        }
      }
    },

    async sendMessage() {
      if (!this.newMessage.trim() && !this.selectedImageFile) return;
      if (!this.currentRecipient) return;

      const conn = dataConnections[this.currentRecipient];

      if (this.selectedImageFile) {
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
            imageUrl: imageDataUrl
          });
          
          this.clearSelectedImage();
          this.newMessage = '';

        } catch (error) {
          console.error('信息隐藏或发送失败:', error);
          alert('发送图片失败: ' + error.message);
        }
        return;
      }
      
      const symmetricKey = symmetricKeys[this.currentRecipient];

      if (conn && conn.open && symmetricKey) {
        try {
          const { iv, ciphertext } = await crypto.encryptSymmetric(symmetricKey, this.newMessage);
          
          conn.send(JSON.stringify({
            type: 'chat_message',
            iv: Array.from(iv),
            ciphertext: Array.from(new Uint8Array(ciphertext))
          }));

          if (!this.messages[this.currentRecipient]) this.messages[this.currentRecipient] = [];
          this.messages[this.currentRecipient].push({ from: this.currentUser, message: this.newMessage });
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
        .catch(error => alert('发送请求时出错: ' + (error.response?.data?.message || error.message)));
    },

    respondToRequest(requestId, action) {
      api.respondToFriendRequest(requestId, action)
        .then(() => {
          alert(`请求已${action === 'accept' ? '接受' : '拒绝'}。`);
          this.fetchFriendRequests();
          this.fetchFriends();
        })
        .catch(error => alert('响应请求时出错: ' + (error.response?.data?.message || error.message)));
    },
    
    removeFriend(friendId) {
      if (confirm('您确定要删除这位好友吗？')) {
        api.removeFriend(friendId)
          .then(() => {
            alert('好友已删除。');
            this.fetchFriends();
          })
          .catch(error => alert('删除好友时出错: ' + (error.response?.data?.message || error.message)));
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
        alert('提取信息失败: ' + error.message);
      }
    },
  },
  mounted() {
    this.currentUser = localStorage.getItem('username') || '用户';
    this.fetchFriends();
    this.fetchFriendRequests();
    this.statusInterval = setInterval(this.fetchFriends, 10000);

    const peer = getPeer();
    if (peer) {
      peer.on('connection', (conn) => {
        console.log(`收到来自 ${conn.peer} 的传入连接`);
        this.setupConnectionHandlers(conn);
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
  beforeUnmount() {
    clearInterval(this.statusInterval);
    // Note: PeerJS connection is destroyed on logout, not just component unmount
  }
};
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  font-family: Arial, sans-serif;
}
.current-user-info {
  padding: 10px;
  text-align: center;
  border-bottom: 1px solid #ddd;
  background-color: #e9e9e9;
}
.sidebar {
  width: 250px;
  background-color: #f4f4f4;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
  padding: 10px;
}
.sidebar h3 {
  text-align: center;
}
.friends-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}
.refresh-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}
.sidebar ul {
  list-style: none;
  padding: 0;
  flex-grow: 1;
}
.sidebar li {
  padding: 15px;
  cursor: pointer;
  border-bottom: 1px solid #ddd;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sidebar li.active {
  background-color: #007aff;
  color: white;
}
.status {
  height: 10px;
  width: 10px;
  border-radius: 50%;
  display: inline-block;
}
.status.online {
  background-color: #4cd964;
}
.status.offline {
  background-color: #ccc;
}
.logout-button {
  padding: 10px;
  background-color: #ff3b30;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.logout-button:hover {
  background-color: #c50000;
}
.chat-window {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}
.messages-area {
  flex-grow: 1;
  padding: 20px;
  overflow-y: auto;
  border-bottom: 1px solid #ddd;
}
.message {
  margin-bottom: 10px;
}
.message-input {
  display: flex;
  padding: 10px;
  align-items: center;
  position: relative;
}
.message-input input[type="text"] {
  flex-grow: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.message-input button {
  padding: 10px 15px;
  margin-left: 10px;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.friend-info {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-grow: 1;
}
.remove-friend-btn {
    background: none;
    border: none;
    color: #ff3b30;
    cursor: pointer;
    font-size: 18px;
    padding: 0 5px;
    display: none; /* Hidden by default */
}
.sidebar li:hover .remove-friend-btn {
    display: block; /* Show on hover */
}
.add-friend-form {
    display: flex;
    padding: 10px;
    gap: 5px;
}
.add-friend-form input {
    flex-grow: 1;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
}
.add-friend-form button {
    padding: 0 12px;
    background-color: #4cd964;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}
.friend-requests {
  padding: 10px;
  border-bottom: 1px solid #ccc;
  margin-bottom: 10px;
}
.friend-requests h4 {
  margin-top: 0;
  text-align: center;
}
.friend-requests ul {
  list-style: none;
  padding: 0;
}
.friend-request-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}
.actions .accept-btn {
  color: #4cd964;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: bold;
}
.actions .reject-btn {
  color: #ff3b30;
  background: none;
  border: none;
  cursor: pointer;
  font-weight: bold;
}
.friends-list {
    flex-grow: 1;
    list-style: none;
    padding: 0;
}
.new-message-indicator {
  width: 10px;
  height: 10px;
  background-color: #ff3b30;
  border-radius: 50%;
  margin-left: auto;
  margin-right: 10px;
}
.upload-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  margin-right: 10px;
}
.image-preview {
  position: absolute;
  bottom: 100%;
  left: 10px;
  background: #fff;
  border: 1px solid #ccc;
  padding: 5px;
  border-radius: 4px;
  box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
}
.image-preview img {
  max-width: 100px;
  max-height: 100px;
  display: block;
}
.clear-preview-btn {
  position: absolute;
  top: -10px;
  right: -10px;
  background: #ff3b30;
  color: white;
  border: none;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  cursor: pointer;
}
.chat-image {
  max-width: 300px;
  max-height: 300px;
  border-radius: 4px;
  cursor: pointer;
}
.message .reveal-btn {
  margin-top: 5px;
}
</style> 