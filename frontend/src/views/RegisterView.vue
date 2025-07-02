<template>
  <div class="container">
    <form class="form" @submit.prevent="handleRegister">
      <div class="title">创建您的账户
        <span>开启安全通讯之旅</span>
      </div>
      <input class="input" type="text" v-model="username" placeholder="用户名" required>
      <input class="input" type="email" v-model="email" placeholder="邮箱" required>
      <input class="input" type="password" v-model="password" placeholder="密码" required>
      <button class="button-confirm">注册 →</button>
      <p class="register-link">
        已有账户？ <router-link to="/login">立即登录</router-link>
      </p>
    </form>
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
        console.log('注册成功:', response.data);
        alert('注册成功！请登录。');
        this.$router.push('/login');
      } catch (error) {
        console.error('注册失败:', error.response ? error.response.data : error.message);
        alert('注册失败: ' + (error.response ? error.response.data.message : '网络错误'));
      }
    }
  }
};
</script>

<style scoped>
/* Copied from LoginView.vue to ensure consistent styling */
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