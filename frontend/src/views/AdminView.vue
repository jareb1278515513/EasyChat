<template>
  <div class="page-container">
    <div class="admin-container">
      <h2>管理员面板</h2>
      <div class="controls">
        <button @click="fetchUsers" class="refresh-btn">刷新用户列表</button>
        <button @click="goBack" class="back-btn">返回聊天</button>
      </div>
      <div class="table-wrapper bordered-and-shadowed">
        <table class="users-table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>邮箱</th>
              <th>在线状态</th>
              <th>管理员</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.username }}</td>
              <td>{{ user.email }}</td>
              <td>
                <span :class="['status', user.is_online ? 'online' : 'offline']">
                  {{ user.is_online ? '在线' : '离线' }}
                </span>
              </td>
              <td>{{ user.is_admin ? '是' : '否' }}</td>
              <td class="actions">
                <button @click="disconnectUser(user.username)" 
                        :disabled="user.username === currentUser"
                        class="action-btn disconnect-btn">
                  强制下线
                </button>
                <button @click="deleteUser(user.username)" 
                        :disabled="user.username === currentUser"
                        class="action-btn delete-btn">
                  删除用户
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import api from '@/services/api';

export default {
  name: 'AdminView',
  data() {
    return {
      users: [],
      currentUser: localStorage.getItem('username') 
    };
  },
  methods: {
    async fetchUsers() {
      try {
        const response = await api.adminGetAllUsers();
        this.users = response.data;
      } catch (error) {
        alert('获取用户列表失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    async disconnectUser(username) {
      if (!confirm(`确定要强制 ${username} 下线吗？`)) return;
      try {
        const response = await api.adminDisconnectUser(username);
        alert(response.data.message || `已向 ${username} 发送下线信号。`);
        await this.fetchUsers(); // Refresh list
      } catch (error) {
        alert('操作失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    async deleteUser(username) {
      if (!confirm(`确定要永久删除用户 ${username} 吗？此操作不可恢复！`)) return;
      try {
        const response = await api.adminDeleteUser(username);
        alert(response.data.message || `${username} 已被删除。`);
        await this.fetchUsers(); // Refresh list
      } catch (error) {
        alert('删除失败：' + (error.response?.data?.error || '未知错误'));
      }
    },
    goBack() {
      this.$router.push('/chat');
    }
  },
  created() {
    this.fetchUsers();
  }
};
</script>

<style scoped>
/* Theme Variables */
.admin-container {
  --input-focus: #2d8cf0;
  --font-color: #323232;
  --font-color-sub: #666;
  --bg-color: beige;
  --main-color: black;
  --base-bg: lightblue;
  --container-bg: #f0f2f5;
  --danger-color: #e74c3c;
  --warning-color: #f1c40f;
  --success-color: #2ecc71;
}

.bordered-and-shadowed {
  border-radius: 5px;
  border: 2px solid var(--main-color);
  background-color: var(--bg-color);
  box-shadow: 4px 4px var(--main-color);
}

.page-container {
  display: flex;
  justify-content: center;
  align-items: flex-start; /* Align to top */
  min-height: 100vh;
  padding: 40px;
  background-color: var(--container-bg);
  box-sizing: border-box;
}

.admin-container {
  width: 100%;
  max-width: 1000px;
  padding: 25px;
  background: var(--base-bg);
  border-radius: 5px;
  border: 2px solid var(--main-color);
  box-shadow: 4px 4px var(--main-color);
  font-family: 'Helvetica Neue', sans-serif;
}

h2 {
  color: var(--font-color);
  font-weight: 900;
  font-size: 24px;
  text-align: center;
  margin-bottom: 25px;
  border-bottom: 2px solid var(--main-color);
  padding-bottom: 15px;
}

.controls {
  margin-bottom: 25px;
  display: flex;
  gap: 15px;
}

button {
  height: 45px;
  padding: 0 20px;
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

.refresh-btn { background-color: var(--input-focus); color: white; }
.back-btn { background-color: var(--font-color-sub); color: white; }
.disconnect-btn { background-color: var(--warning-color); }
.delete-btn { background-color: var(--danger-color); color: white; }
.action-btn { height: auto; padding: 5px 10px; font-size: 14px; }


.table-wrapper {
  padding: 10px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  background-color: white;
}

.users-table th, .users-table td {
  border: 2px solid var(--main-color);
  padding: 12px 15px;
  text-align: left;
  color: var(--font-color);
}

.users-table th {
  font-weight: 900;
  background-color: var(--bg-color);
}

.status {
  padding: 3px 8px;
  border-radius: 12px;
  color: white;
  font-size: 0.8em;
  font-weight: bold;
  text-align: center;
}

.online { background-color: var(--success-color); }
.offline { background-color: var(--font-color-sub); }

.actions {
  display: flex;
  gap: 10px;
}
</style> 