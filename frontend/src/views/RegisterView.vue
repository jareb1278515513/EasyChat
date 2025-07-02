<template>
  <div class="container">
    <form class="form" @submit.prevent="handleRegister">
      <div class="title">创建您的账户
        <span>开启安全通讯之旅</span>
      </div>
      <input class="input" type="text" v-model="username" placeholder="用户名" required>
      
      <div class="input-group">
        <input class="input" type="email" v-model="email" @input="validateEmail" placeholder="邮箱" required>
        <p v-if="emailError" class="error-text">{{ emailError }}</p>
      </div>

      <div class="input-group">
        <input class="input" type="password" v-model="password" @input="evaluatePassword" placeholder="密码" required>
        <div v-if="password.length > 0" class="password-strength-meter">
          <div class="strength-bar" :style="barStyle"></div>
          <p class="strength-text">{{ strengthText }}</p>
        </div>
      </div>

      <button class="button-confirm" :disabled="!isFormValid">注册 →</button>
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
      password: '',
      emailError: '',
      passwordStrength: 0,
    };
  },
  computed: {
    strengthText() {
      const strengths = ['', '非常弱', '弱', '中等', '强', '非常强'];
      return strengths[this.passwordStrength];
    },
    barStyle() {
      const colors = ['#ccc', '#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#27ae60'];
      const width = this.passwordStrength * 20;
      return {
        backgroundColor: colors[this.passwordStrength],
        width: `${width}%`
      };
    },
    isFormValid() {
      return this.email && !this.emailError && this.passwordStrength >= 3;
    }
  },
  methods: {
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!this.email) {
        this.emailError = '邮箱不能为空';
      } else if (!emailRegex.test(this.email)) {
        this.emailError = '请输入有效的邮箱格式';
      } else {
        this.emailError = '';
      }
    },
    evaluatePassword() {
      let score = 0;
      if (!this.password) {
        this.passwordStrength = 0;
        return;
      }
      // 长度
      if (this.password.length >= 8) score++;
      if (this.password.length >= 12) score++;
      // 包含不同类型的字符
      if (/[a-z]/.test(this.password) && /[A-Z]/.test(this.password)) score++;
      if (/\d/.test(this.password)) score++;
      if (/[^a-zA-Z0-9]/.test(this.password)) score++;
      
      this.passwordStrength = score > 5 ? 5 : score;
    },
    async handleRegister() {
      this.validateEmail(); // Final check on submit
      if (!this.isFormValid) {
        alert('请检查表单输入，确保邮箱格式正确且密码强度足够。');
        return;
      }

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
        alert('注册失败: ' + (error.response ? error.response.data.error : '网络错误'));
      }
    }
  }
};
</script>

<style scoped>
/* ... existing styles ... */
.input-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.error-text {
  color: #e74c3c;
  font-size: 0.8rem;
  margin: 0;
  padding-left: 5px;
}

.password-strength-meter {
  width: 100%;
  height: 20px;
  background-color: #eee;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
}

.strength-bar {
  height: 100%;
  transition: width 0.3s ease, background-color 0.3s ease;
}

.strength-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin: 0;
  font-size: 0.8rem;
  color: #333;
  font-weight: bold;
  mix-blend-mode: difference;
  color: white;
}

.button-confirm:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}
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