<template>
  <div class="settings-container">
    <h2>设置</h2>

    <div class="settings-section">
      <h3>更改邮箱</h3>
      <form @submit.prevent="changeEmail">
        <div class="form-group">
          <label for="new-email">新邮箱</label>
          <input type="email" id="new-email" v-model="newEmail" @input="validateEmail" required>
          <p v-if="emailError" class="error-text">{{ emailError }}</p>
        </div>
        <button type="submit" :disabled="!isEmailFormValid">更新邮箱</button>
      </form>
    </div>

    <div class="settings-section">
      <h3>更改密码</h3>
      <form @submit.prevent="changePassword">
        <div class="form-group">
          <label for="current-password">当前密码</label>
          <input type="password" id="current-password" v-model="currentPassword" required>
        </div>
        <div class="form-group">
          <label for="new-password">新密码</label>
          <input type="password" id="new-password" v-model="newPassword" @input="evaluatePassword" required>
           <div v-if="newPassword.length > 0" class="password-strength-meter">
            <div class="strength-bar" :style="barStyle"></div>
            <p class="strength-text">{{ strengthText }}</p>
          </div>
        </div>
        <div class="form-group">
          <label for="confirm-password">确认新密码</label>
          <input type="password" id="confirm-password" v-model="confirmPassword" required>
        </div>
        <button type="submit" :disabled="!isPasswordFormValid">更新密码</button>
      </form>
    </div>
     <button @click="goBack">返回</button>
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
.settings-container {
  max-width: 500px;
  margin: 50px auto;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

h2, h3 {
  text-align: center;
  color: #333;
}

.settings-section {
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input[type="email"],
input[type="password"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
}

button:hover {
  background-color: #0056b3;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

button:disabled:hover {
  background-color: #ccc;
}

button[type="submit"] {
    background-color: #28a745;
}
button[type="submit"]:hover {
    background-color: #218838;
}

.error-text {
  color: #e74c3c;
  font-size: 0.8rem;
  margin-top: 5px;
}

.password-strength-meter {
  width: 100%;
  height: 20px;
  background-color: #eee;
  border-radius: 5px;
  overflow: hidden;
  position: relative;
  margin-top: 5px;
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

</style> 