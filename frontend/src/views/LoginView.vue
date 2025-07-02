<template>
  <div class="login-container">
    <div class="login-box">
      <h1>EasyChat</h1>
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <input type="text" v-model="username" placeholder="Username" required>
        </div>
        <div class="input-group">
          <input type="password" v-model="password" placeholder="Password" required>
        </div>
        <button type="submit" class="login-button">Login</button>
      </form>
      <p class="register-link">
        Don't have an account? <router-link to="/register">Register</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';
import socket from '@/services/socket';
import { initializePeer } from '@/services/peer';
import { generateRsaKeyPair, exportKeyToPem } from '@/utils/crypto';

export default {
  name: 'LoginView',
  data() {
    return {
      username: '',
      password: '',
    };
  },
  methods: {
    async handleLogin() {
      try {
        const port = process.env.VUE_APP_P2P_PORT;
        const response = await api.login({
          username: this.username,
          password: this.password,
          port: port,
        });
        
        console.log('Login successful:', response.data);
        const token = response.data.token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', this.username);

        // Generate and upload public key
        try {
          console.log('Generating key pair...');
          const keyPair = await generateRsaKeyPair();
          const publicKey = await exportKeyToPem('spki', keyPair.publicKey);
          const privateKey = await exportKeyToPem('pkcs8', keyPair.privateKey);

          localStorage.setItem('privateKey', privateKey);
          await api.uploadPublicKey(publicKey);
          console.log('Public key uploaded successfully.');
        } catch (error) {
          console.error('Key generation or upload failed:', error);
          alert('Could not set up encryption keys. Please try again.');
          return; // Stop if key setup fails
        }

        // Initialize PeerJS connection
        try {
          console.log('Initializing PeerJS with username:', this.username);
          initializePeer(this.username);
        } catch (error) {
          console.error('PeerJS initialization failed:', error);
          alert('Could not set up P2P connection. Please try again.');
          return;
        }

        // Disconnect any existing connection before starting a new one
        if (socket.connected) {
          socket.disconnect();
        }

        // Set auth for subsequent connection attempts
        socket.auth = { token };
        
        // Handle successful connection
        socket.once('connect', () => {
          console.log('Socket connected successfully, sending authentication.');
          // The backend expects an 'authenticate' event after connection
          socket.emit('authenticate', {
            token,
            ip_address: '127.0.0.1', // In a real app, this might be discovered or configured
            port: port
          });
        });
        
        // Now, connect
        socket.connect();

        this.$router.push('/chat');
      } catch (error) {
        console.error('Login failed:', error.response ? error.response.data : error.message);
        alert('Login failed: ' + (error.response ? error.response.data.message : 'Network Error'));
      }
    }
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.login-box {
  background: #fff;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}
h1 {
  margin-bottom: 24px;
  color: #333;
}
.input-group {
  margin-bottom: 20px;
}
input {
  width: 100%;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.login-button {
  width: 100%;
  padding: 12px;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
.login-button:hover {
  background-color: #0056b3;
}
.register-link {
  margin-top: 20px;
}
.register-link a {
  color: #007aff;
  text-decoration: none;
}
</style> 