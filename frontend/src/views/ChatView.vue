<template>
  <div class="chat-container">
    <div class="sidebar">
      <div class="current-user-info">
        <h4>Welcome, {{ currentUser }}</h4>
      </div>
      
      <!-- Friend Requests Section -->
      <div class="friend-requests" v-if="friendRequests.length > 0">
        <h4>Friend Requests</h4>
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
        <h3>Friends</h3>
        <button @click="fetchFriends" class="refresh-btn" title="Refresh friends list">🔄</button>
      </div>
      <div class="add-friend-form">
        <input type="text" v-model="newFriendUsername" @keyup.enter="sendRequest" placeholder="Send friend request">
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

      <button @click="logout" class="logout-button">Logout</button>
    </div>
    <div class="chat-window">
      <div class="messages-area">
        <div v-if="!currentRecipient">Select a friend to start chatting</div>
        <div v-else>
          <div v-for="(msg, index) in messages[currentRecipient]" :key="index" class="message">
            <strong>{{ msg.from }}:</strong> {{ msg.message }}
          </div>
        </div>
      </div>
      <div class="message-input" v-if="currentRecipient">
        <input type="text" v-model="newMessage" @keyup.enter="sendMessage" placeholder="Type a message...">
        <button @click="sendMessage">Send</button>
      </div>
    </div>
  </div>
</template>

<script>
import socket from '@/services/socket';
import api from '@/services/api';
import * as crypto from '@/utils/crypto';
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
      
      if (!dataConnections[username] || !dataConnections[username].open) {
        console.log(`Attempting to connect to peer: ${username}`);
        const peer = getPeer();
        if (peer) {
          const conn = peer.connect(username, { reliable: true });
          this.setupConnectionHandlers(conn);
        } else {
          alert("P2P service is not available. Please re-login.");
        }
      } else {
        console.log(`Connection to ${username} already exists.`);
      }
    },

    setupConnectionHandlers(conn) {
      // This handler is used for both incoming and outgoing connections
      dataConnections[conn.peer] = conn;
      
      conn.on('data', (data) => {
        this.handleNewP2PMessage({ from: conn.peer, rawMessage: data });
      });

      conn.on('open', () => {
        console.log(`Data connection with ${conn.peer} is now open.`);
        // The initiator of the connection is responsible for starting the key exchange
        if (this.currentRecipient === conn.peer) {
          this.performKeyExchange(conn.peer, conn);
        }
      });

      conn.on('close', () => {
        console.log(`Connection with ${conn.peer} has closed.`);
        delete dataConnections[conn.peer];
        delete symmetricKeys[conn.peer];
      });

      conn.on('error', (err) => {
        console.error(`Connection error with ${conn.peer}:`, err);
      });
    },

    // --- E2EE and Messaging ---
    async performKeyExchange(username, conn) {
      try {
        console.log(`Starting key exchange with ${username}`);
        const { data: { public_key: friendPublicKeyPem } } = await api.getPublicKey(username);
        const friendPublicKey = await crypto.importPublicKey(friendPublicKeyPem);
        const symmetricKey = await crypto.generateSymmetricKey();
        symmetricKeys[username] = symmetricKey;

        const exportedSymmetricKey = await window.crypto.subtle.exportKey('raw', symmetricKey);
        const encryptedSymmetricKey = await crypto.encryptWithPublicKey(friendPublicKey, exportedSymmetricKey);
        
        conn.send(JSON.stringify({ type: 'key_exchange', payload: Array.from(new Uint8Array(encryptedSymmetricKey)) }));
        console.log(`Sent encrypted symmetric key to ${username}.`);
      } catch (err) {
        console.error('Key exchange failed:', err);
        alert('Could not establish a secure connection.');
        if (conn) conn.close();
      }
    },

    async handleNewP2PMessage(data) {
      const { from, rawMessage } = data;
      const message = typeof rawMessage === 'string' ? JSON.parse(rawMessage) : rawMessage;

      if (message.type === 'key_exchange') {
        try {
          console.log(`Received key exchange request from ${from}.`);
          const privateKeyPem = localStorage.getItem('privateKey');
          const privateKey = await crypto.importPrivateKey(privateKeyPem);
          const encryptedKey = new Uint8Array(message.payload).buffer;
          const decryptedKey = await crypto.decryptWithPrivateKey(privateKey, encryptedKey);
          symmetricKeys[from] = await window.crypto.subtle.importKey('raw', decryptedKey, { name: 'AES-GCM' }, true, ['encrypt', 'decrypt']);
          console.log(`Successfully established symmetric key with ${from}.`);
          alert(`Secure channel with ${from} established!`);
        } catch (err) {
          console.error('Failed to process key exchange:', err);
        }
        return;
      }
      
      if (message.type === 'chat_message') {
        const symmetricKey = symmetricKeys[from];
        if (!symmetricKey) return console.warn(`No symmetric key for ${from}.`);
        
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
          console.error('Failed to decrypt message:', err);
        }
      }
    },

    async sendMessage() {
      if (!this.newMessage.trim() || !this.currentRecipient) return;
      
      const conn = dataConnections[this.currentRecipient];
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
          console.error('Failed to send message:', error);
          alert('Failed to send secure message.');
        }
      } else {
        alert('Secure connection is not established. Cannot send message.');
      }
    },

    // --- UI and Data Fetching ---
    logout() {
      console.log('Logging out...');
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
        .catch(error => console.error('Error fetching friends list:', error));
    },

    fetchFriendRequests() {
      api.getFriendRequests()
        .then(response => {
          this.friendRequests = response.data;
        })
        .catch(error => console.error('Error fetching friend requests:', error));
    },
    
    sendRequest() {
      if (!this.newFriendUsername.trim()) return;
      api.sendFriendRequest(this.newFriendUsername)
        .then(() => {
          alert('Friend request sent.');
          this.newFriendUsername = '';
        })
        .catch(error => alert('Error sending request: ' + (error.response?.data?.message || error.message)));
    },

    respondToRequest(requestId, action) {
      api.respondToFriendRequest(requestId, action)
        .then(() => {
          alert(`Request ${action}ed.`);
          this.fetchFriendRequests();
          this.fetchFriends();
        })
        .catch(error => alert('Error responding to request: ' + (error.response?.data?.message || error.message)));
    },
    
    removeFriend(friendId) {
      if (confirm('Are you sure you want to remove this friend?')) {
        api.removeFriend(friendId)
          .then(() => {
            alert('Friend removed.');
            this.fetchFriends();
          })
          .catch(error => alert('Error removing friend: ' + (error.response?.data?.message || error.message)));
      }
    }
  },
  mounted() {
    this.currentUser = localStorage.getItem('username') || 'User';
    this.fetchFriends();
    this.fetchFriendRequests();
    this.statusInterval = setInterval(this.fetchFriends, 10000);

    const peer = getPeer();
    if (peer) {
      peer.on('connection', (conn) => {
        console.log(`Incoming connection from ${conn.peer}`);
        this.setupConnectionHandlers(conn);
      });
      peer.on('error', (err) => {
        console.error('A global peer error occurred:', err);
        if (err.type === 'peer-unavailable') {
          alert(`Could not connect to ${this.currentRecipient}. They may be offline or unreachable.`);
        }
      });
    } else {
      alert("P2P service is not available. Please re-login.");
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
}
.message-input input {
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
</style> 