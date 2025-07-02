# EasyChat 后端 API 使用指南

本文档为 EasyChat 的后端服务提供详细的 API 和 WebSocket 事件说明，旨在为前端开发提供支持。

---

## 1. 启动后端服务

在进行任何测试或开发之前，请确保后端服务正在运行。

1.  打开一个新的终端。
2.  导航到项目的 `backend` 目录。
3.  激活 Python 虚拟环境：
    ```bash
    # Windows
    .\venv\Scripts\activate
    ```
4.  运行 Flask 应用：
    ```bash
    python run.py
    ```
    服务器默认在 `http://127.0.0.1:5000` 上运行。

---

## 2. 认证机制

本应用的 API 使用 **JWT (JSON Web Token)**进行认证。

-   成功登录后，客户端会收到一个 `token`。
-   对于所有需要认证的 API 请求，客户端必须在 HTTP 请求头中包含 `Authorization` 字段。
-   格式为：`Authorization: Bearer <your_jwt_token>`

---

## 3. HTTP API 接口

API 的基地址为 `http://localhost:5000/api`。

### 3.1 用户与认证

#### 3.1.1 注册新用户
-   **URL**: `/register`
-   **Method**: `POST`
-   **Description**: 创建一个新用户账户。
-   **Request Body** (`application/json`):
    ```json
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123"
    }
    ```
-   **Success Response** (`201 CREATED`):
    ```json
    { "message": "User registered successfully" }
    ```
-   **Error Responses** (`400 BAD REQUEST`):
    ```json
    { "error": "Missing username, email, or password" }
    { "error": "Username already exists" }
    { "error": "Email already registered" }
    ```

#### 3.1.2 用户登录
-   **URL**: `/login`
-   **Method**: `POST`
-   **Description**: 用户登录以获取认证令牌。服务器会根据请求来源更新用户的IP地址。
-   **Request Body** (`application/json`):
    ```json
    {
        "username": "testuser",
        "password": "password123"
    }
    ```
-   **Success Response** (`200 OK`):
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2Vy..."
    }
    ```
-   **Error Response** (`401 UNAUTHORIZED`):
    ```json
    { "error": "Invalid username or password" }
    ```

#### 3.1.3 上传/更新公钥
-   **URL**: `/keys`
-   **Method**: `POST`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 允许已认证用户上传自己的公钥，用于端到端加密。
-   **Request Body** (`application/json`):
    ```json
    {
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIB..."
    }
    ```
-   **Success Response** (`200 OK`):
    ```json
    { "message": "Public key updated successfully" }
    ```

#### 3.1.4 获取指定用户的公钥
-   **URL**: `/users/<username>/public_key`
-   **Method**: `GET`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 获取指定用户的公钥。
-   **Success Response** (`200 OK`):
    ```json
    {
        "user_id": 2,
        "username": "bob",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIIB..."
    }
    ```
-   **Error Response** (`404 NOT FOUND`):
    ```json
    { "error": "User has not uploaded a public key" }
    ```

### 3.2 好友管理

#### 3.2.1 获取好友列表
-   **URL**: `/friends`
-   **Method**: `GET`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 获取当前用户的所有好友及其在线状态。
-   **Success Response** (`200 OK`):
    ```json
    [
        {
            "id": 2,
            "username": "friend1",
            "is_online": true,
            "ip_address": "192.168.1.100",
            "port": 8888
        }
    ]
    ```

#### 3.2.2 发送好友请求
-   **URL**: `/friend-requests`
-   **Method**: `POST`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 向另一位用户发送好友请求。成功后会通过 WebSocket 向接收方发送 `new_friend_request` 事件。
-   **Request Body** (`application/json`):
    ```json
    { "username": "receiver_username" }
    ```
-   **Success Response** (`201 CREATED`):
    ```json
    { "message": "Friend request sent successfully" }
    ```

#### 3.2.3 获取收到的好友请求
-   **URL**: `/friend-requests`
-   **Method**: `GET`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 获取所有发送给当前用户的、状态为"待处理"的好友请求。
-   **Success Response** (`200 OK`):
    ```json
    [
        {
            "id": 1,
            "requester_id": 3,
            "requester_username": "some_user",
            "timestamp": "2023-10-27T10:00:00"
        }
    ]
    ```

#### 3.2.4 响应好友请求
-   **URL**: `/friend-requests/<request_id>`
-   **Method**: `PUT`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 接受或拒绝一个好友请求。
-   **Request Body** (`application/json`):
    ```json
    { "action": "accept" }
    ```
    > `action` 的值可以是 `accept` 或 `reject`.
-   **Success Response** (`200 OK`):
    ```json
    { "message": "Friend request accepted successfully." }
    ```

#### 3.2.5 删除好友
-   **URL**: `/friends/<friend_id>`
-   **Method**: `DELETE`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 解除与一位用户的好友关系。
-   **Success Response** (`200 OK`):
    ```json
    { "message": "Friend removed successfully" }
    ```

### 3.3 在线状态

#### 3.3.1 获取好友在线信息
-   **URL**: `/users/<username>/info`
-   **Method**: `GET`
-   **Authorization**: `Bearer Token` **必需**.
-   **Description**: 获取指定好友的在线状态、IP地址和端口号。出于隐私考虑，此信息仅对好友开放。
-   **Success Response** (`200 OK`):
    ```json
    {
        "username": "friend_username",
        "is_online": true,
        "ip_address": "127.0.0.1",
        "port": 8888
    }
    ```
-   **Error Response** (`403 FORBIDDEN`):
    ```json
    { "error": "Access denied: you can only view info for your friends." }
    ```

---

## 4. WebSocket 实时事件

WebSocket 服务器地址为 `http://localhost:5000`。

### 4.1 认证连接
-   **Event**: `authenticate`
-   **Direction**: `Client -> Server`
-   **Description**: 在 WebSocket 连接建立后，客户端必须立即发送此事件进行认证，以开始接收实时更新。
-   **Payload**:
    ```javascript
    {
        "token": "your_jwt_token",
        "ip_address": "192.168.1.101", // 可选, 用于P2P
        "port": 9999 // 可选, 用于P2P
    }
    ```
-   **Server Action**:
    -   验证 `token`, 将用户 `is_online` 状态设置为 `True`, 并记录其 IP 和端口。
    -   向该用户的所有在线好友广播 `friend_status_update` 事件。

### 4.2 WebRTC 信令转发
-   **Event**: `webrtc_signal`
-   **Direction**: `Client -> Server -> Client`
-   **Description**: 用于在两个客户端之间透明地转发 WebRTC 信令（如 offer, answer, ICE candidates），以建立 P2P 连接。
-   **Payload (Client -> Server)**:
    ```javascript
    {
        "to": "recipient_username",
        "signal": { ... } // 具体的 WebRTC 信令对象
    }
    ```
-   **Payload (Server -> Client)**:
     ```javascript
    {
        "from": "sender_username",
        "signal": { ... } // 具体的 WebRTC 信令对象
    }
    ```

### 4.3 好友状态更新
-   **Event**: `friend_status_update`
-   **Direction**: `Server -> Client`
-   **Description**: 当您的好友上线或下线时，服务器会发送此事件。
-   **Payload**:
    ```javascript
    // 上线
    { "username": "friend_username", "is_online": true, "ip_address": "127.0.0.1", "port": 8888 }
    // 下线
    { "username": "friend_username", "is_online": false }
    ```

### 4.4 收到新的好友请求
-   **Event**: `new_friend_request`
-   **Direction**: `Server -> Client`
-   **Description**: 当有其他用户向您发送好友请求时，服务器会发送此事件。
-   **Payload**:
    ```javascript
    {
        "id": 1,
        "requester_id": 3,
        "requester_username": "some_user",
        "timestamp": "2023-10-27T10:00:00Z"
    }
    ```

### 4.5 断开连接
-   **Event**: `disconnect`
-   **Direction**: `Implicit` (由客户端关闭连接触发)
-   **Description**: 当客户端断开 WebSocket 连接时自动触发。
-   **Server Action**:
    -   将用户 `is_online` 状态设置为 `False`, 并清空 IP 和端口。
    -   向该用户的好友广播 `friend_status_update` 事件。

### 4.6 (已弃用) 私聊消息
-   **Event**: `private_message`
-   **Description**: 此事件已弃用。新的消息系统应通过 WebRTC 实现端到端(P2P)的安全通信。

---
## 5. 管理员专用接口

### 5.1 获取所有用户信息
-   **URL**: `/admin/users`
-   **Method**: `GET`
-   **Authorization**: `Bearer Token` **必需** (且用户必须是管理员).
-   **Description**: 获取系统中所有用户的列表及其状态。

### 5.2 强制用户下线
-   **URL**: `/admin/users/<username>/disconnect`
-   **Method**: `POST`
-   **Authorization**: `Bearer Token` **必需** (且用户必须是管理员).
-   **Description**: 强制指定用户断开 WebSocket 连接。

---
## 6. 使用 Postman 进行功能测试

本节将指导您如何使用 Postman 测试一个完整的业务场景：**用户 `user2` 获取其好友 `user1` 的在线 IP 和端口**。

### 前提
确保后端服务正在运行。

### 步骤 1: 注册两个测试用户
如果测试用户不存在，请先注册他们。
- **请求**: `POST http://localhost:5000/api/register`
- **Body**:
    ```json
    { "username": "user1", "email": "user1@example.com", "password": "pw1" }
    ```
- **请求**: `POST http://localhost:5000/api/register`
- **Body**:
    ```json
    { "username": "user2", "email": "user2@example.com", "password": "pw2" }
    ```

### 步骤 2: 登录并保存 Token
为两个用户登录，并将其返回的 `token` 保存为 Postman 的环境变量，方便后续使用。
1.  **user1 登录**: 发送 `POST http://localhost:5000/api/login` 请求，Body 为 `{"username": "user1", "password": "pw1"}`。在 Postman 的 `Tests` 标签页中添加以下脚本，将 token 保存到名为 `token1` 的变量中：
    ```javascript
    pm.environment.set("token1", pm.response.json().token);
    ```
2.  **user2 登录**: 发送 `POST http://localhost:5000/api/login` 请求，Body 为 `{"username": "user2", "password": "pw2"}`。同样，在 `Tests` 标签页中添加脚本，保存为 `token2`：
    ```javascript
    pm.environment.set("token2", pm.response.json().token);
    ```

### 步骤 3: 模拟 user1 上线
此步骤需要使用 Postman 的 WebSocket 功能来模拟客户端连接和认证。
1.  在 Postman 中，新建一个 WebSocket 请求。
2.  **输入服务器 URL**: `ws://localhost:5000/socket.io/?EIO=4&transport=websocket`
3.  点击 **Connect**。连接成功后，您会从服务器收到一条类似 `0{"sid":"..."...}` 的消息。
4.  **发送认证事件**: 在下方的消息输入框中，发送以下内容以认证 `user1` 并上报其IP和端口。Postman 会自动将 `{{token1}}` 替换为您保存的环境变量。
    ```
    42["authenticate",{"token":"{{token1}}","ip_address":"192.168.1.101","port":9999}]
    ```
    > **注意**: `42` 是 Socket.IO 协议的一部分，用于表示发送一个事件。请确保完整复制。
5.  此时，服务器已将 `user1` 标记为在线，并记录了其 IP 和端口。您可以保持此 WebSocket 连接，或直接断开。

### 步骤 4: 建立好友关系
`user2` 还不能直接获取 `user1` 的信息，他们需要先成为好友。
1.  **user1 发送好友请求给 user2**:
    -   **Method**: `POST`
    -   **URL**: `http://localhost:5000/api/friend-requests`
    -   **Headers**: `Authorization: Bearer {{token1}}`
    -   **Body** (raw, JSON): `{ "username": "user2" }`
2.  **user2 查询收到的好友请求**:
    -   **Method**: `GET`
    -   **URL**: `http://localhost:5000/api/friend-requests`
    -   **Headers**: `Authorization: Bearer {{token2}}`
    -   从返回的 JSON 数组中找到来自 `user1` 的请求，并将其 `id` 复制下来。为了方便，可以在 `Tests` 标签页中添加以下脚本，自动将其保存为 `request_id`：
      ```javascript
      // 假设只收到了一个请求
      pm.environment.set("request_id", pm.response.json()[0].id);
      ```
3.  **user2 接受好友请求**:
    -   **Method**: `PUT`
    -   **URL**: `http://localhost:5000/api/friend-requests/{{request_id}}`
    -   **Headers**: `Authorization: Bearer {{token2}}`
    -   **Body** (raw, JSON): `{ "action": "accept" }`

### 步骤 5: 获取好友在线信息
现在 `user1` 和 `user2` 已是好友，`user2` 可以成功获取 `user1` 的信息。
- **请求**:
    -   **Method**: `GET`
    -   **URL**: `http://localhost:5000/api/users/user1/info`
    -   **Headers**: `Authorization: Bearer {{token2}}`
- **预期成功响应** (`200 OK`):
    ```json
    {
        "username": "user1",
        "is_online": true,
        "ip_address": "192.168.1.101",
        "port": 9999
    }
    ```
通过以上步骤，您就完成了一个完整的跨 HTTP 和 WebSocket 的功能测试。 