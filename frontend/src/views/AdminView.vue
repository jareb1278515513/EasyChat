<template>
  <div class="admin-container">
    <h2>管理员面板</h2>
    <div class="controls">
      <button @click="fetchUsers" class="refresh-btn">刷新用户列表</button>
      <button @click="goBack" class="back-btn">返回聊天</button>
    </div>
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
        alert('获取用户列表失败: ' + (error.response?.data?.error || '未知错误'));
      }
    },
    async disconnectUser(username) {
      if (!confirm(`确定要强制 ${username} 下线吗？`)) return;
      try {
        const response = await api.adminDisconnectUser(username);
        alert(response.data.message || `已向 ${username} 发送下线信号。`);
        await this.fetchUsers(); // Refresh list
      } catch (error) {
        alert('操作失败: ' + (error.response?.data?.error || '未知错误'));
      }
    },
    async deleteUser(username) {
      if (!confirm(`确定要永久删除用户 ${username} 吗？此操作不可恢复！`)) return;
      try {
        const response = await api.adminDeleteUser(username);
        alert(response.data.message || `${username} 已被删除。`);
        await this.fetchUsers(); // Refresh list
      } catch (error) {
        alert('删除失败: ' + (error.response?.data?.error || '未知错误'));
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
.admin-container {
  max-width: 900px;
  margin: 20px auto;
  padding: 20px;
  font-family: sans-serif;
}

.controls {
  margin-bottom: 20px;
  display: flex;
  gap: 10px;
}

.refresh-btn, .back-btn {
  padding: 10px 15px;
  border: none;
  border-radius: 5px;
  color: white;
  cursor: pointer;
}

.refresh-btn {
  background-color: #007bff;
}

.refresh-btn:hover {
  background-color: #0056b3;
}

.back-btn {
  background-color: #6c757d;
}

.back-btn:hover {
  background-color: #5a6268;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th, .users-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.users-table th {
  background-color: #f2f2f2;
}

.status {
  padding: 3px 8px;
  border-radius: 12px;
  color: white;
  font-size: 0.8em;
}

.online {
  background-color: #28a745;
}

.offline {
  background-color: #dc3545;
}

.actions {
  display: flex;
  gap: 5px;
}

.action-btn {
  padding: 5px 10px;
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
}

.disconnect-btn {
  background-color: #ffc107;
}

.delete-btn {
  background-color: #dc3545;
}

.action-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
</style> 