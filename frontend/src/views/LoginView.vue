<template>
  <div class="container">
    <form class="form" @submit.prevent="handleLogin">
      <div class="title">欢迎使用EasyChat!
        <span>登录以继续</span>
      </div>
      <input class="input" type="text" v-model="username" placeholder="用户名" required>
      <input class="input" type="password" v-model="password" placeholder="密码" required>
      <button class="button-confirm">登录 →</button>
      <p class="register-link">
        还没有账户？ <router-link to="/register">立即注册</router-link>
      </p>
    </form>
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
        
        console.log('登录成功:', response.data);
        const token = response.data.token;
        localStorage.setItem('token', token);
        localStorage.setItem('username', this.username);

        // Generate and upload public key
        try {
          console.log('正在生成密钥对...');
          const keyPair = await generateRsaKeyPair();
          const publicKey = await exportKeyToPem('spki', keyPair.publicKey);
          const privateKey = await exportKeyToPem('pkcs8', keyPair.privateKey);

          localStorage.setItem('privateKey', privateKey);
          await api.uploadPublicKey(publicKey);
          console.log('公钥上传成功。');
        } catch (error) {
          console.error('密钥生成或上传失败:', error);
          alert('无法设置加密密钥，请重试。');
          return;
        }

        // Initialize PeerJS connection
        try {
          console.log('正在使用用户名初始化 PeerJS:', this.username);
          initializePeer(this.username);
        } catch (error) {
          console.error('PeerJS 初始化失败:', error);
          alert('无法建立P2P连接，请重试。');
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
          console.log('Socket 连接成功，正在发送认证信息。');
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
        console.error('登录失败:', error.response ? error.response.data : error.message);
        alert('登录失败：' + (error.response?.data?.message || '网络错误'));
      }
    }
  }
};
</script>

<style scoped>
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}

.form {
  --input-focus: #2d8cf0;
  --font-color: #323232;
  --font-color-sub: #666;
  --bg-color: beige;
  --main-color: black;
  padding: 25px;
  background: lightblue;
  display: flex;
  flex-direction: column;
  align-items: center; /* Centered form elements */
  justify-content: center;
  gap: 20px;
  border-radius: 5px;
  border: 2px solid var(--main-color);
  box-shadow: 4px 4px var(--main-color);
  width: 100%;
  max-width: 400px; /* Increased width */
}

.title {
  color: var(--font-color);
  font-weight: 900;
  font-size: 24px; /* Larger title */
  margin-bottom: 25px;
  text-align: center;
}

.title span {
  color: var(--font-color-sub);
  font-weight: 600;
  font-size: 17px;
}

.input {
  width: 100%; /* Full width */
  height: 45px; /* Taller input */
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
  font-size: 16px;
  font-weight: 600;
  color: var(--font-color);
  padding: 5px 15px;
  outline: none;
  box-sizing: border-box;
}

.input::placeholder {
  color: var(--font-color-sub);
  opacity: 0.8;
}

.input:focus {
  border: 2px solid var(--input-focus);
}

.button-confirm {
  margin: 30px auto 0 auto;
  width: 150px;
  height: 45px;
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
  font-size: 18px;
  font-weight: 600;
  color: var(--font-color);
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}

.button-confirm:active {
  box-shadow: 0px 0px var(--main-color);
  transform: translate(4px, 4px);
}

.register-link {
  margin-top: 20px;
  color: var(--font-color-sub);
  font-size: 0.9rem;
}

.register-link a {
  color: #2d8cf0;
  text-decoration: none;
  font-weight: 600;
}
</style> 