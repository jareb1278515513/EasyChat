<template>
  <div class="register-container">
    <div class="register-box">
      <h1>Create Account</h1>
      <form @submit.prevent="handleRegister">
        <div class="input-group">
          <input type="text" v-model="username" placeholder="Username" required>
        </div>
        <div class="input-group">
          <input type="email" v-model="email" placeholder="Email" required>
        </div>
        <div class="input-group">
          <input type="password" v-model="password" placeholder="Password" required>
        </div>
        <button type="submit" class="register-button">Register</button>
      </form>
      <p class="login-link">
        Already have an account? <router-link to="/login">Login</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'RegisterView',
  data() {
    return {
      username: '',
      email: '',
      password: ''
    };
  },
  methods: {
    async handleRegister() {
      try {
        const response = await api.register({
          username: this.username,
          email: this.email,
          password: this.password
        });
        console.log('Registration successful:', response.data);
        alert('Registration successful! Please login.');
        this.$router.push('/login');
      } catch (error) {
        console.error('Registration failed:', error.response ? error.response.data : error.message);
        alert('Registration failed: ' + (error.response ? error.response.data.message : error.message));
      }
    }
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f2f5;
}
.register-box {
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
.register-button {
  width: 100%;
  padding: 12px;
  background-color: #007aff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
.register-button:hover {
  background-color: #0056b3;
}
.login-link {
  margin-top: 20px;
}
.login-link a {
  color: #007aff;
  text-decoration: none;
}
</style> 