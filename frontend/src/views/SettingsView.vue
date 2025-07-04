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

      <div class="settings-section">
        <h3>个人资料</h3>
        <form @submit.prevent="updateProfile" class="settings-form">
          <div class="form-group">
            <label for="gender">性别</label>
            <select id="gender" v-model="profile.gender" class="bordered-and-shadowed">
              <option value="">未指定</option>
              <option value="男">男</option>
              <option value="女">女</option>
              <option value="其他">其他</option>
            </select>
          </div>
          <div class="form-group">
            <label for="age">年龄</label>
            <input type="number" id="age" v-model.number="profile.age" min="0" class="bordered-and-shadowed">
          </div>
          <div class="form-group">
            <label for="bio">个人简介</label>
            <textarea id="bio" v-model="profile.bio" rows="3" class="bordered-and-shadowed" style="height: auto;"></textarea>
          </div>
          <button type="submit">更新资料</button>
        </form>
      </div>

      <div class="settings-section">
        <h3>设置头像</h3>
        <div class="avatar-uploader">
          <img :src="avatarPreview" alt="当前头像" class="current-avatar bordered-and-shadowed">
          <input type="file" @change="onFileSelected" accept="image/*" ref="fileInput" style="display: none;">
          <div class="avatar-actions">
            <button @click="$refs.fileInput.click()" class="select-btn">选择图片</button>
            <button @click="uploadAvatar" :disabled="!selectedFile" class="upload-btn">上传头像</button>
          </div>
        </div>
      </div>

      <button @click="goBack" class="back-btn">返回</button>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

const DEFAULT_AVATAR = require('@/assets/logo.png'); 

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
      profile: {
        gender: '',
        age: null,
        bio: '',
        avatar_url: ''
      },
      selectedFile: null,
      avatarPreview: DEFAULT_AVATAR
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
    async fetchUserProfile() {
      try {
        const username = localStorage.getItem('username');
        if (username) {
          const { data } = await api.getUserProfile(username);
          this.profile.gender = data.gender || '';
          this.profile.age = data.age;
          this.profile.bio = data.bio || '';
          this.profile.avatar_url = data.avatar_url;
          if (data.avatar_url) {
            this.avatarPreview = data.avatar_url;
          }
        }
      } catch (error) {
        console.error('获取用户资料失败:', error);
        // 不打扰用户，静默处理
      }
    },
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
    async updateProfile() {
      try {
        await api.updateProfile(this.profile);
        alert('个人资料更新成功！');
      } catch (error) {
        alert('个人资料更新失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    onFileSelected(event) {
      const file = event.target.files[0];
      if (file) {
        this.selectedFile = file;
        this.avatarPreview = URL.createObjectURL(file);
      }
    },
    async uploadAvatar() {
      if (!this.selectedFile) return;
      const formData = new FormData();
      formData.append('avatar', this.selectedFile);

      try {
        const { data } = await api.uploadAvatar(formData);
        this.profile.avatar_url = data.avatar_url;
        this.avatarPreview = data.avatar_url; // 更新预览
        this.selectedFile = null; // 重置选择
        alert('头像上传成功！');
      } catch (error) {
        alert('头像上传失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    goBack() {
      this.$router.push('/chat');
    }
  },
  created() {
    this.fetchUserProfile();
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

/* Avatar Uploader Styles */
.avatar-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.current-avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid var(--main-color);
}

.avatar-actions {
  display: flex;
  gap: 10px;
}

.avatar-actions .select-btn {
  background-color: var(--input-focus);
  color: white;
}

.avatar-actions .upload-btn {
  background-color: var(--success-color);
  color: white;
}
</style> 