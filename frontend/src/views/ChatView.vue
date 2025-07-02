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

// Simple in-memory store for peer connections
const peerConnections = {};
// Store for symmetric keys for each chat session
const symmetricKeys = {};

export default {
  name: 'ChatView',
  data() {
    return {
      friends: [],
      friendRequests: [],
      messages: {}, // Changed to an object to store messages per recipient
      newMessage: '',
      currentRecipient: null,
      newFriendUsername: '',
      statusInterval: null,
      currentUser: '',
    };
  },
  methods: {
    selectRecipient(username) {
      this.currentRecipient = username;
      if (!this.messages[username]) {
        this.messages[username] = [];
      }
      const friend = this.friends.find(f => f.username === username);
      if (friend) {
        friend.hasNewMessages = false;
      }
      this.initPeerConnection(username);
    },

    async initPeerConnection(username, isInitiator = true) {
      // Fetch user info to get IP and Port for P2P connection
      try {
        const response = await api.getUserInfo(username);
        if (!response.data.is_online) {
          alert(`${username} is offline.`);
          return;
        }
        // NOTE: In a real-world scenario, you would use the returned IP address.
        // For development on localhost, STUN servers will handle IP discovery.
        // const { ip_address, port } = response.data;
      } catch (error) {
        alert(`Could not fetch info for ${username}. You might not be friends.`);
        return;
      }

      if (peerConnections[username] && ['new', 'connecting', 'connected'].includes(peerConnections[username].connectionState)) {
        console.log(`Connection to ${username} already exists or is in progress. State: ${peerConnections[username].connectionState}`);
        return;
      }
      console.log(`Initializing P2P connection to ${username} as ${isInitiator ? 'initiator' : 'receiver'}`);
      
      const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
      peerConnections[username] = pc;

      pc.onicecandidate = (event) => {
        if (event.candidate) {
          socket.emit('webrtc_signal', { to: username, signal: { type: 'candidate', candidate: event.candidate } });
        }
      };

      pc.onconnectionstatechange = () => {
        console.log(`Connection state with ${username} changed to: ${pc.connectionState}`);
      };

      const setupDataChannelHandlers = (dc) => {
        dc.onopen = async () => {
          console.log(`Data channel with ${username} is open!`);
          if (isInitiator) {
            // Initiator performs the key exchange
            try {
              console.log(`Starting key exchange with ${username}`);
              const { data: { public_key: friendPublicKeyPem } } = await api.getPublicKey(username);
              const friendPublicKey = await crypto.importPublicKey(friendPublicKeyPem);
              const symmetricKey = await crypto.generateSymmetricKey();
              symmetricKeys[username] = symmetricKey; // Store for this session

              const exportedSymmetricKey = await window.crypto.subtle.exportKey('raw', symmetricKey);
              const encryptedSymmetricKey = await crypto.encryptWithPublicKey(friendPublicKey, exportedSymmetricKey);
              
              // Send the encrypted key, marking it as a special key-exchange message
              dc.send(JSON.stringify({ type: 'key_exchange', payload: Array.from(new Uint8Array(encryptedSymmetricKey)) }));
              console.log('Sent encrypted symmetric key.');
            } catch (err) {
              console.error('Key exchange failed:', err);
              alert('Could not establish a secure connection.');
            }
          }
        };
        dc.onmessage = (e) => this.handleNewP2PMessage({ from: username, rawMessage: e.data });
        dc.onclose = () => console.log(`Data channel with ${username} has closed.`);
        dc.onerror = (error) => console.error(`Data channel error with ${username}:`, error);
      };

      if (isInitiator) {
        const dataChannel = pc.createDataChannel('chat');
        pc.dataChannel = dataChannel; // Assign immediately
        setupDataChannelHandlers(dataChannel);
        
        pc.createOffer()
          .then(offer => pc.setLocalDescription(offer))
          .then(() => {
            socket.emit('webrtc_signal', { to: username, signal: { type: 'offer', sdp: pc.localDescription } });
          });
      } else {
        pc.ondatachannel = (event) => {
          const dataChannel = event.channel;
          pc.dataChannel = dataChannel; // Assign immediately
          setupDataChannelHandlers(dataChannel);
        };
      }
    },

    async handleNewP2PMessage(data) {
      const { from, rawMessage } = data;
      const message = JSON.parse(rawMessage);

      // Handle key exchange
      if (message.type === 'key_exchange') {
        try {
          console.log(`Received encrypted symmetric key from ${from}.`);
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
      
      // Handle regular chat messages
      const symmetricKey = symmetricKeys[from];
      if (!symmetricKey) {
        console.warn(`No symmetric key found for ${from}. Ignoring message.`);
        return;
      }
      
      try {
        const { iv, ciphertext } = message;
        const plaintext = await crypto.decryptSymmetric(symmetricKey, new Uint8Array(ciphertext).buffer, new Uint8Array(iv));

        if (!this.messages[from]) {
          this.messages[from] = [];
        }
        this.messages[from].push({ from, message: plaintext });

        if (from !== this.currentRecipient) {
          const friend = this.friends.find(f => f.username === from);
          if (friend) {
            friend.hasNewMessages = true;
          }
        }
      } catch (err) {
        console.error('Failed to decrypt message:', err);
      }
    },

    async sendMessage() {
      if (!this.newMessage || !this.currentRecipient) return;
      const pc = peerConnections[this.currentRecipient];
      const symmetricKey = symmetricKeys[this.currentRecipient];

      if (pc && pc.dataChannel && pc.dataChannel.readyState === 'open' && symmetricKey) {
        try {
          const { iv, ciphertext } = await crypto.encryptSymmetric(symmetricKey, this.newMessage);
          pc.dataChannel.send(JSON.stringify({
            iv: Array.from(iv),
            ciphertext: Array.from(new Uint8Array(ciphertext))
          }));
          
          this.messages[this.currentRecipient].push({ from: 'me', message: this.newMessage });
          this.newMessage = '';
        } catch (err) {
          console.error('Failed to encrypt and send message:', err);
          alert('Failed to send secure message.');
        }
      } else {
        alert('Secure P2P connection not established yet.');
      }
    },

    handleWebRTCSignal(data) {
        const { from, signal } = data;
        let pc = peerConnections[from];

        if (!pc) {
            this.initPeerConnection(from, false); // This is the receiver
            pc = peerConnections[from];
        }

        if (signal.type === 'offer') {
            pc.setRemoteDescription(new RTCSessionDescription(signal.sdp))
              .then(() => pc.createAnswer())
              .then(answer => pc.setLocalDescription(answer))
              .then(() => {
                  socket.emit('webrtc_signal', {
                      to: from,
                      signal: { type: 'answer', sdp: pc.localDescription }
                  });
              });
        } else if (signal.type === 'answer') {
            pc.setRemoteDescription(new RTCSessionDescription(signal.sdp));
        } else if (signal.type === 'candidate') {
            pc.addIceCandidate(new RTCIceCandidate(signal.candidate));
        }
    },

    async sendRequest() {
      if (!this.newFriendUsername) return;
      try {
        const response = await api.sendFriendRequest(this.newFriendUsername);
        alert(response.data.message);
        this.newFriendUsername = '';
      } catch (error) {
        alert(error.response?.data?.error || 'Failed to send friend request');
      }
    },
    async removeFriend(friendId) {
      if (!confirm('Are you sure you want to remove this friend?')) return;
      try {
        await api.removeFriend(friendId);
        this.fetchFriends(); // Refresh friend list
        if (this.currentRecipient === this.friends.find(f => f.id === friendId)?.username) {
            this.currentRecipient = null; // Deselect if the removed friend was active
        }
      } catch (error) {
        alert(error.response?.data?.error || 'Failed to remove friend');
      }
    },
    async respondToRequest(requestId, action) {
      try {
        await api.respondToFriendRequest(requestId, action);
        this.fetchFriendRequests(); // Refresh requests
        if (action === 'accept') {
          this.fetchFriends(); // Refresh friends list
        }
      } catch (error) {
        alert(error.response?.data?.error || `Failed to ${action} request`);
      }
    },
    logout() {
      localStorage.clear();
      socket.disconnect();
      this.$router.push('/login');
    },
    handleNewMessage(data) {
      // Show message only if it's from the currently selected friend
      if (data.from === this.currentRecipient) {
        this.messages[this.currentRecipient].push(data);
      } else {
        // Optional: Add a notification for messages from other friends
        console.log(`Received message from ${data.from}, but not in active chat.`);
      }
    },
    handleFriendStatusUpdate(data) {
      const friend = this.friends.find(f => f.username === data.username);
      if (friend) {
        friend.is_online = data.is_online;
        if (data.is_online) {
          friend.ip_address = data.ip_address;
          friend.port = data.port;
        }
      }
    },
    handleNewFriendRequest(data) {
      // Avoid adding duplicates if the list was already fetched
      if (!this.friendRequests.some(req => req.id === data.id)) {
        this.friendRequests.unshift(data); // Add to the top of the list
      }
      alert(`You have a new friend request from ${data.requester_username}!`);
    },
    async fetchFriends() {
      try {
        const response = await api.getFriends();
        this.friends = response.data;
      } catch (error) {
        console.error('Failed to fetch friends:', error);
        // If auth fails (e.g., token expired), redirect to login
        if (error.response && error.response.status === 401) {
          this.logout();
        }
      }
    },
    async fetchFriendRequests() {
      try {
        const response = await api.getFriendRequests();
        this.friendRequests = response.data;
      } catch (error) {
        console.error('Failed to fetch friend requests:', error);
      }
    }
  },
  mounted() {
    this.currentUser = localStorage.getItem('username') || 'User';
    this.fetchFriends();
    this.fetchFriendRequests();
    
    // Set up polling for friend status
    this.statusInterval = setInterval(this.fetchFriends, 60000); // 60000ms = 1 minute

    socket.on('new_message', this.handleNewMessage);
    socket.on('friend_status_update', this.handleFriendStatusUpdate);
    socket.on('new_friend_request', this.handleNewFriendRequest);
    socket.on('webrtc_signal', this.handleWebRTCSignal);
  },
  beforeUnmount() {
    // Clean up the interval when the component is destroyed
    clearInterval(this.statusInterval);

    // Clean up listeners to prevent memory leaks
    socket.off('new_message', this.handleNewMessage);
    socket.off('friend_status_update', this.handleFriendStatusUpdate);
    socket.off('new_friend_request', this.handleNewFriendRequest);
    socket.off('webrtc_signal', this.handleWebRTCSignal);

    // Close all peer connections
    for (const user in peerConnections) {
      peerConnections[user].close();
      delete peerConnections[user];
    }
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