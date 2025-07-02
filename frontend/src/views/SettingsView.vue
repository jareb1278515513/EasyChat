<template>
  <div class="page-container">
    <div class="settings-container">
      <h2>设置</h2>

      <div class="settings-section">
        <h3>更改邮箱</h3>
        <form @submit.prevent="changeEmail" class="settings-form">
          <div class="form-group">
            <label for="new-email">新邮箱</label>
            <input type="email" id="new-email" v-model="newEmail" @input="validateEmail" required class="bordered-and-shadowed">
            <p v-if="emailError" class="error-text">{{ emailError }}</p>
          </div>
          <button type="submit" :disabled="!isEmailFormValid">更新邮箱</button>
        </form>
      </div>

      <div class="settings-section">
        <h3>更改密码</h3>
        <form @submit.prevent="changePassword" class="settings-form">
          <div class="form-group">
            <label for="current-password">当前密码</label>
            <input type="password" id="current-password" v-model="currentPassword" required class="bordered-and-shadowed">
          </div>
          <div class="form-group">
            <label for="new-password">新密码</label>
            <input type="password" id="new-password" v-model="newPassword" @input="evaluatePassword" required class="bordered-and-shadowed">
            <div v-if="newPassword.length > 0" class="password-strength-meter">
              <div class="strength-bar" :style="barStyle"></div>
              <p class="strength-text">{{ strengthText }}</p>
            </div>
          </div>
          <div class="form-group">
            <label for="confirm-password">确认新密码</label>
            <input type="password" id="confirm-password" v-model="confirmPassword" required class="bordered-and-shadowed">
          </div>
          <button type="submit" :disabled="!isPasswordFormValid">更新密码</button>
        </form>
      </div>
      <button @click="goBack" class="back-btn">返回</button>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'SettingsView',
  data() {
    return {
      newEmail: '',
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
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
    isEmailFormValid() {
      return this.newEmail && !this.emailError;
    },
    isPasswordFormValid() {
      return this.currentPassword && this.newPassword && this.newPassword === this.confirmPassword && this.passwordStrength >= 3;
    }
  },
  methods: {
    validateEmail() {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!this.newEmail) {
        this.emailError = '邮箱不能为空';
      } else if (!emailRegex.test(this.newEmail)) {
        this.emailError = '请输入有效的邮箱格式';
      } else {
        this.emailError = '';
      }
    },
    evaluatePassword() {
      let score = 0;
      if (!this.newPassword) {
        this.passwordStrength = 0;
        return;
      }
      if (this.newPassword.length >= 8) score++;
      if (this.newPassword.length >= 12) score++;
      if (/[a-z]/.test(this.newPassword) && /[A-Z]/.test(this.newPassword)) score++;
      if (/\d/.test(this.newPassword)) score++;
      if (/[^a-zA-Z0-9]/.test(this.newPassword)) score++;
      this.passwordStrength = score > 5 ? 5 : score;
    },
    async changeEmail() {
      this.validateEmail();
      if (!this.isEmailFormValid) {
        alert('请输入有效的邮箱地址。');
        return;
      }
      try {
        await api.updateEmail(this.newEmail);
        alert('邮箱更新成功！');
        this.newEmail = '';
      } catch (error) {
        alert('邮箱更新失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    async changePassword() {
      if (!this.isPasswordFormValid) {
        if (this.newPassword !== this.confirmPassword) {
          alert('新密码和确认密码不匹配');
        } else if (this.passwordStrength < 3) {
          alert('新密码强度太弱，请使用更强的密码。');
        } else {
          alert('请填写所有密码字段。');
        }
        return;
      }
      try {
        await api.updatePassword({
          current_password: this.currentPassword,
          new_password: this.newPassword
        });
        alert('密码更新成功！');
        this.currentPassword = '';
        this.newPassword = '';
        this.confirmPassword = '';
      } catch (error) {
        alert('密码更新失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    goBack() {
      this.$router.push('/chat');
    }
  }
};
</script>

<style scoped>
/* Theme Variables */
.settings-container {
  --input-focus: #2d8cf0;
  --font-color: #323232;
  --font-color-sub: #666;
  --bg-color: beige;
  --main-color: black;
  --base-bg: lightblue;
  --container-bg: #f0f2f5;
  --danger-color: #e74c3c;
  --success-color: #2ecc71;
}

/* Shared Styles */
.bordered-and-shadowed {
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
  width: 100%;
  height: 45px;
  font-size: 16px;
  font-weight: 600;
  color: var(--font-color);
  padding: 5px 15px;
  outline: none;
  box-sizing: border-box;
}
.bordered-and-shadowed:focus {
  border: 2px solid var(--input-focus);
}

.page-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--container-bg);
  padding: 20px;
  box-sizing: border-box;
}

.settings-container {
  width: 100%;
  max-width: 500px;
  padding: 25px;
  background: var(--base-bg);
  border-radius: 5px;
  border: 2px solid var(--main-color);
  box-shadow: 4px 4px var(--main-color);
  font-family: 'Helvetica Neue', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

h2 {
  color: var(--font-color);
  font-weight: 900;
  font-size: 24px;
  text-align: center;
  margin: 0 0 15px 0;
}

h3 {
  font-weight: 900;
  color: var(--font-color);
  text-align: center;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid var(--main-color);
}

.settings-section {
  padding: 20px;
  border: 2px solid var(--main-color);
  border-radius: 5px;
  background: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

label {
  font-weight: 600;
  color: var(--font-color);
}

button {
  width: 100%;
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

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

button[type="submit"] {
  background-color: var(--success-color);
  color: white;
}
.back-btn {
  background-color: var(--font-color-sub);
  color: white;
}

.error-text {
  color: var(--danger-color);
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
  font-weight: bold;
  mix-blend-mode: difference;
  color: white;
}
</style> 