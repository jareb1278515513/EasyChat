# 安全即时通讯系统 API 文档

本文档定义了安全即时通讯系统后端服务的所有 API 接口。

## 基础 URL

- `http://127.0.0.1:5000/api`

## 认证

部分接口需要认证。客户端在成功登录后会获得一个 JSON Web Token (JWT)。后续请求应在 HTTP `Authorization` 头中携带此令牌。

格式: `Authorization: Bearer <token>`

---

## 一、用户认证 (Authentication)

### 1. 用户注册

- **Endpoint:** `POST /register`
- **描述:** 创建一个新用户账户。
- **请求体 (JSON):**
  ```json
  {
    "username": "someuser",
    "email": "user@example.com",
    "password": "yourpassword"
  }
  ```
- **成功响应 (201):**
  ```json
  {
    "message": "User registered successfully"
  }
  ```
- **错误响应 (400):**
  - 缺少字段: `{"error": "Missing username, email, or password"}`
  - 用户名已存在: `{"error": "Username already exists"}`
  - 邮箱已注册: `{"error": "Email already registered"}`

### 2. 用户登录

- **Endpoint:** `POST /login`
- **描述:** 使用用户名和密码进行认证，成功后返回一个用于后续请求认证的 JWT。
- **请求体 (JSON):**
  ```json
  {
    "username": "someuser",
    "password": "yourpassword"
  }
  ```
- **成功响应 (200):**
  ```json
  {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```
- **错误响应 (401):**
  - 无效凭证: `{"error": "Invalid username or password"}`

---

## 二、通信录管理 (Contacts)

*所有此部分的接口都需要认证。*

### 1. 获取好友列表

- **Endpoint:** `GET /friends`
- **描述:** 获取当前用户的所有好友列表。
- **成功响应 (200):**
  ```json
  [
    {
      "id": 2,
      "username": "friend1",
      "is_online": true,
      "ip_address": "192.168.1.101",
      "port": 5000
    },
    {
      "id": 3,
      "username": "friend2",
      "is_online": false
    }
  ]
  ```

### 2. 添加好友

- **Endpoint:** `POST /friends`
- **描述:** 发送好友请求或添加一个好友。
- **请求体 (JSON):**
  ```json
  {
    "friend_username": "newfriend"
  }
  ```
- **成功响应 (201):**
  ```json
  {
    "message": "Friend added successfully",
    "friend": {
      "id": 4,
      "username": "newfriend"
    }
  }
  ```
- **错误响应 (404):**
  - 用户未找到: `{"error": "User not found"}`

### 3. 删除好友

- **Endpoint:** `DELETE /friends/<int:friend_id>`
- **描述:** 从通信录中删除一个好友。
- **成功响应 (200):**
  ```json
  {
    "message": "Friend removed successfully"
  }
  ```
- **错误响应 (404):**
  - 好友关系未找到: `{"error": "Friend not found in your contact list"}`

---

## 三、功能性接口 (Functional)

### 1. 获取用户公钥

- **Endpoint:** `GET /users/<int:user_id>/public_key`
- **描述:** 当需要进行端到端加密通信时，获取指定用户的公钥。
- **成功响应 (200):**
  ```json
  {
    "user_id": 2,
    "public_key": "----BEGIN PUBLIC KEY-----...----END PUBLIC KEY-----"
  }
  ```
- **错误响应 (404):**
  - 用户未找到: `{"error": "User not found"}`

---

## 四、后台监管 (Admin)

*所有此部分的接口都需要管理员权限认证。*

### 1. 获取所有用户状态

- **Endpoint:** `GET /admin/users`
- **描述:** 获取系统内所有用户的列表及其在线状态。
- **成功响应 (200):**
  ```json
  [
    {
      "id": 1,
      "username": "admin",
      "is_online": true
    },
    {
      "id": 2,
      "username": "user1",
      "is_online": false
    }
  ]
  ```

### 2. 强制用户下线

- **Endpoint:** `POST /admin/users/<int:user_id>/kick`
- **描述:** 强制某个用户下线。
- **成功响应 (200):**
  ```json
  {
    "message": "User user1 has been kicked."
  }
  ```


</rewritten_file> 