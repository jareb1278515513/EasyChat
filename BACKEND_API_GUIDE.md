# 后端 API 指南 (V2)

本文档详细介绍了 EasyChat 后端提供的 RESTful API 和 WebSocket 事件，旨在为前端开发提供清晰、准确的接口规范。

**基础 URL**: 所有 API 的基础路径为 `/api`。

**认证方式**: 大多数需要用户登录的 API 均采用 JWT (JSON Web Token) 进行认证。客户端在登录成功后会获得一个 Token，后续请求需在 HTTP Header 中加入 `Authorization` 字段，格式为 `Bearer <Your_JWT_Token>`。

---

## **第一部分：RESTful API**

### **1. 基础接口**

#### **1.1. 服务器状态检查**

*   **功能**: 检查服务器是否正在运行。
*   **Endpoint**: `/ping`
*   **方法**: `GET`
*   **认证**: 无需
*   **请求**: 无
*   **成功响应 (200 OK)**:
    *   **内容**: `Pong!` (纯文本)

---

### **2. 用户与认证 (User & Auth)**

#### **2.1. 用户注册**

*   **功能**: 创建一个新用户账户。
*   **Endpoint**: `/register`
*   **方法**: `POST`
*   **认证**: 无需
*   **请求体 (JSON)**:
    ```json
    {
      "username": "new_user",
      "email": "user@example.com",
      "password": "your_secure_password"
    }
    ```
*   **成功响应 (201 Created)**:
    ```json
    {
      "message": "User registered successfully"
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: 请求体格式错误、缺少字段，或用户名/邮箱已存在。

#### **2.2. 用户登录**

*   **功能**: 认证用户凭证，成功后返回 JWT。
*   **Endpoint**: `/login`
*   **方法**: `POST`
*   **认证**: 无需
*   **请求体 (JSON)**:
    ```json
    {
      "username": "existing_user",
      "password": "your_password",
      "port": 5000 
    }
    ```
    *   `port`: 客户端用于 P2P 通信的监听端口。
*   **成功响应 (200 OK)**:
    ```json
    {
      "token": "a.very.long.jwt.token.string"
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: 请求体格式错误或缺少字段。
    *   `401 Unauthorized`: 用户名或密码无效。

#### **2.3. 上传公钥**

*   **功能**: 上传用户的 RSA 公钥，用于后续的端到端加密密钥协商。
*   **Endpoint**: `/keys`
*   **方法**: `POST`
*   **认证**: **需要** (`token_required`)
*   **请求体 (JSON)**:
    ```json
    {
      "public_key": "-----BEGIN PUBLIC KEY-----\nMIICIj...\n-----END PUBLIC KEY-----"
    }
    ```
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Public key updated successfully"
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: 请求体中缺少 `public_key`。

#### **2.4. 获取用户公钥**

*   **功能**: 获取指定用户的公钥。
*   **Endpoint**: `/users/<username>/public_key`
*   **方法**: `GET`
*   **认证**: **需要** (`token_required`)
*   **路径参数**:
    *   `username`: 目标用户的用户名。
*   **成功响应 (200 OK)**:
    ```json
    {
      "user_id": 2,
      "username": "friend_user",
      "public_key": "-----BEGIN PUBLIC KEY-----\nMIICIj...\n-----END PUBLIC KEY-----"
    }
    ```
*   **错误响应**:
    *   `404 Not Found`: 用户不存在，或该用户尚未上传公钥。

---

### **3. 好友管理 (Friends)**

所有好友管理相关的 API 均需要认证。

#### **3.1. 获取好友列表**

*   **功能**: 获取当前登录用户的所有好友。
*   **Endpoint**: `/friends`
*   **方法**: `GET`
*   **认证**: **需要** (`token_required`)
*   **成功响应 (200 OK)**:
    ```json
    [
      {
        "id": 2,
        "username": "alice",
        "is_online": true,
        "ip_address": "192.168.1.10",
        "port": 5000
      },
      {
        "id": 3,
        "username": "bob",
        "is_online": false,
        "ip_address": null,
        "port": null
      }
    ]
    ```

#### **3.2. 发送好友请求**

*   **功能**: 向另一个用户发送好友请求。
*   **Endpoint**: `/friend-requests`
*   **方法**: `POST`
*   **认证**: **需要** (`token_required`)
*   **请求体 (JSON)**:
    ```json
    {
      "username": "user_to_add"
    }
    ```
*   **成功响应 (201 Created)**:
    *   同时会向接收方（`user_to_add`）通过 WebSocket 发送一个 `new_friend_request` 事件。
    ```json
    {
      "message": "Friend request sent successfully"
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: 不能添加自己、已是好友、或已有待处理的请求。
    *   `404 Not Found`: 目标用户不存在。

#### **3.3. 获取收到的好友请求**

*   **功能**: 获取所有发送给当前用户的、状态为"待处理"的好友请求。
*   **Endpoint**: `/friend-requests`
*   **方法**: `GET`
*   **认证**: **需要** (`token_required`)
*   **成功响应 (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "requester_id": 4,
        "requester_username": "charlie",
        "timestamp": "2023-10-27T10:00:00"
      }
    ]
    ```

#### **3.4. 响应好友请求**

*   **功能**: 接受或拒绝一个好友请求。
*   **Endpoint**: `/friend-requests/<request_id>`
*   **方法**: `PUT`
*   **认证**: **需要** (`token_required`)
*   **路径参数**:
    *   `request_id`: 目标好友请求的 ID。
*   **请求体 (JSON)**:
    ```json
    {
      "action": "accept" 
    }
    ```
    *   `action`: 必须是 `"accept"` 或 `"reject"`。
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Friend request accepted successfully."
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: `action` 无效，或请求已被处理。
    *   `403 Forbidden`: 无权响应此请求。
    *   `404 Not Found`: 请求 ID 不存在。

#### **3.5. 删除好友**

*   **功能**: 解除与某个用户的好友关系（双向）。
*   **Endpoint**: `/friends/<friend_id>`
*   **方法**: `DELETE`
*   **认证**: **需要** (`token_required`)
*   **路径参数**:
    *   `friend_id`: 目标好友的用户 ID。
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Friend removed successfully"
    }
    ```
*   **错误响应**:
    *   `400 Bad Request`: 对方不是你的好友。
    *   `404 Not Found`: 目标用户 ID 不存在。

---

### **4. 用户信息查询 (Online Status)**

#### **4.1. 获取指定用户信息**

*   **功能**: 获取指定用户的在线状态和连接信息。
*   **Endpoint**: `/users/<username>/info`
*   **方法**: `GET`
*   **认证**: **需要** (`token_required`)
*   **访问限制**: 只能查询自己或好友的信息。
*   **成功响应 (200 OK)**:
    *   如果用户在线且是好友:
        ```json
        {
          "username": "alice",
          "is_online": true,
          "ip_address": "192.168.1.10",
          "port": 5000
        }
        ```
    *   如果用户离线:
        ```json
        {
          "username": "alice",
          "is_online": false
        }
        ```
*   **错误响应**:
    *   `403 Forbidden`: 目标用户不是你的好友。
    *   `404 Not Found`: 用户不存在。

---

### **5. 管理员接口 (Admin)**

所有管理员接口都需要**管理员权限**认证。

#### **5.1. 获取所有用户列表**

*   **功能**: 获取系统内所有用户的列表和状态。
*   **Endpoint**: `/admin/users`
*   **方法**: `GET`
*   **认证**: **需要** (`admin_required`)
*   **成功响应 (200 OK)**:
    ```json
    [
      {
        "id": 1,
        "username": "admin",
        "email": "admin@app.com",
        "is_online": true,
        "ip_address": "127.0.0.1",
        "is_admin": true
      },
      {
        "id": 2,
        "username": "alice",
        "email": "alice@app.com",
        "is_online": false,
        "ip_address": null,
        "is_admin": false
      }
    ]
    ```

#### **5.2. 强制用户下线**

*   **功能**: 强制断开指定用户的 WebSocket 连接。
*   **Endpoint**: `/admin/users/<username>/disconnect`
*   **方法**: `POST`
*   **认证**: **需要** (`admin_required`)
*   **路径参数**:
    *   `username`: 目标用户的用户名。
*   **成功响应 (200 OK)**:
    ```json
    {
      "message": "Disconnect signal sent to alice."
    }
    ```
*   **错误响应**:
    *   `404 Not Found`: 目标用户不存在。
    *   `500 Internal Server Error`: 数据库状态与 Socket 会话不一致（该接口会自动修复数据库状态）。

---

## **第二部分：WebSocket 事件**

客户端通过 Socket.IO 与服务器进行实时通信。

### **客户端 -> 服务器 (Client Emits)**

#### `authenticate`

*   **功能**: 在 WebSocket 连接建立后，客户端必须立即发送此事件进行身份验证。
*   **数据**:
    ```json
    {
      "token": "your.jwt.token",
      "ip_address": "192.168.1.10",
      "port": 5000
    }
    ```
    *   `token`: 从登录接口获取的 JWT。
    *   `ip_address`, `port`: 客户端用于 P2P 通信的 IP 和端口。

#### `webrtc_signal`

*   **功能**: 用于在两个客户端之间中继（转发）WebRTC 信令（如 `offer`, `answer`, `ICE candidates`）。
*   **数据**:
    ```json
    {
      "to": "recipient_username",
      "signal": { ... } 
    }
    ```
    *   `to`: 接收信令的用户名。
    *   `signal`: 具体的 WebRTC 信令对象。

### **服务器 -> 客户端 (Server Emits)**

#### `new_friend_request`

*   **功能**: 当有新的好友请求时，服务器向接收方发送此事件。
*   **触发**: 其他用户调用 `POST /friend-requests`。
*   **数据**:
    ```json
    {
      "id": 1,
      "requester_id": 4,
      "requester_username": "charlie",
      "timestamp": "2023-10-27T10:00:00Z"
    }
    ```

#### `friend_status_update`

*   **功能**: 当好友上线或下线时，服务器向其所有在线好友广播此事件。
*   **触发**: 用户 `authenticate` 成功或 `disconnect`。
*   **数据 (上线时)**:
    ```json
    {
      "username": "alice",
      "is_online": true,
      "ip_address": "192.168.1.10",
      "port": 5000
    }
    ```
*   **数据 (下线时)**:
    ```json
    {
      "username": "alice",
      "is_online": false
    }
    ```

#### `webrtc_signal`

*   **功能**: 将从一个客户端收到的 WebRTC 信令转发给目标客户端。
*   **触发**: 其他客户端发送 `webrtc_signal` 事件。
*   **数据**:
    ```json
    {
      "from": "sender_username",
      "signal": { ... }
    }
    ```
    *   `from`: 发送信令的用户名。
    *   `signal`: 具体的 WebRTC 信令对象。

</rewritten_file> 