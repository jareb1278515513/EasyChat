# EasyChat 后端服务使用指南

本文档将指导您如何启动 EasyChat 的后端服务，并使用 Postman 工具来测试其各项核心功能，包括 REST API 和 WebSocket 实时服务。

---

## 1. 启动后端服务

在进行任何测试之前，请确保后端服务正在运行。

1.  **打开终端**：启动一个新的终端或命令行工具。

2.  **进入 `backend` 目录**：
    ```powershell
    cd D:\课程讲义、作业\大型程序设计实践\EasyChat\backend
    ```

3.  **激活 Python 虚拟环境**：这一步至关重要，它能确保我们使用正确的依赖环境。
    ```powershell
    .\venv\Scripts\Activate.ps1
    ```
    成功后，您会看到命令行提示符前面出现 `(venv)` 标志。

4.  **运行启动脚本**：
    ```powershell
    python run.py
    ```

服务成功启动后，您会看到类似以下的输出，请**保持此终端窗口不要关闭**，服务会一直在此运行并打印实时日志。
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
 ...
```

---

## 2. 使用 Postman 测试功能

**重要提示**：对于所有需要认证的 API，您必须在请求的 `Headers` 中添加一个 `Authorization` 键，其值为 `Bearer <your_token>`（注意 `Bearer` 和 token 之间的空格）。

### A. 用户认证 (REST API)

#### 注册新用户
- **Method**: `POST`
- **URL**: `http://127.0.0.1:5000/api/register`
- **Body**: `raw` -> `JSON`
- **Payload**:
  ```json
  {
      "username": "alice",
      "email": "alice@example.com",
      "password": "password123"
  }
  ```
- **预期响应**: `201 Created`

#### 用户登录
- **Method**: `POST`
- **URL**: `http://127.0.0.1:5000/api/login`
- **Body**: `raw` -> `JSON`
- **Payload**:
  ```json
  {
      "username": "alice",
      "password": "password123"
  }
  ```
- **预期响应**: `200 OK`，并在响应体中返回一个 JSON 对象，包含 `token`。**请复制并妥善保管这个 `token`**，后续的认证请求都需要它。

### B. 好友管理 (REST API)
*需要认证*

#### 添加好友
- **Method**: `POST`
- **URL**: `http://127.0.0.1:5000/api/friends`
- **Headers**: `Authorization: Bearer <your_token>`
- **Body**: `raw` -> `JSON`
- **Payload**:
  ```json
  {
      "friend_username": "bob"
  }
  ```

#### 查看好友列表
- **Method**: `GET`
- **URL**: `http://127.0.0.1:5000/api/friends`
- **Headers**: `Authorization: Bearer <your_token>`

#### 删除好友
- **Method**: `DELETE`
- **URL**: `http://127.0.0.1:5000/api/friends/<friend_id>` (请将 `<friend_id>` 替换为实际的好友用户ID)
- **Headers**: `Authorization: Bearer <your_token>`

### C. 公钥管理 (REST API)
*需要认证*

#### 上传公钥
- **Method**: `POST`
- **URL**: `http://127.0.0.1:5000/api/keys`
- **Headers**: `Authorization: Bearer <your_token>`
- **Body**: `raw` -> `JSON`
- **Payload**:
  ```json
  {
      "public_key": "----BEGIN PUBLIC KEY---- ...your_key_content... ----END PUBLIC KEY----"
  }
  ```

#### 获取指定用户的公钥
- **Method**: `GET`
- **URL**: `http://127.0.0.1:5000/api/users/<username>/public_key` (请将 `<username>` 替换为目标用户的用户名)
- **Headers**: `Authorization: Bearer <your_token>`

### D. 实时功能 (WebSocket)

1.  **创建 WebSocket 连接**
    - 在 Postman 中，点击 **New** -> **WebSocket Request**。
    - 在 URL 栏输入: `ws://127.0.0.1:5000/socket.io/?EIO=4&transport=websocket`
    - 点击 **Connect**。

2.  **发送认证事件**
    - 连接成功后，在下面的 **Message** 输入框中，我们需要手动发送认证事件。Socket.IO 的消息格式为 `事件类型代码["事件名", {数据}]`。
    - 输入以下内容，并将 `<your_token>` 替换为您登录后获取的 Token：
      ```
      42["authenticate", {"token": "<your_token>"}]
      ```
    - 点击 **Send** 发送。

3.  **测试好友上下线通知**
    - 打开**两个** WebSocket 标签页，一个模拟 **Bob**，一个模拟 **Alice**。
    - **先连接并认证 Bob**。
    - 然后再**连接并认证 Alice**。
    - 认证 Alice 成功后，切换回 **Bob 的标签页**，您应该会在消息窗口看到一条来自服务器的 `friend_status_update` 新消息，通知您 Alice 已上线。

4.  **测试私信**
    - 在 Alice 的标签页，发送 `private_message` 事件给 Bob。
    - 消息格式:
      ```
      42["private_message", {"to": "bob", "message": "Hello from Postman!", "token": "<alice_token>"}]
      ```
    - 切换到 Bob 的标签页，您应该会看到一条 `new_message` 新消息。

### E. 管理员功能 (REST API)
*需要管理员权限的 Token*

#### 获取所有用户列表
- **Method**: `GET`
- **URL**: `http://127.0.0.1:5000/api/admin/users`
- **Headers**: `Authorization: Bearer <admin_user_token>`

#### 强制用户下线
- **Method**: `POST`
- **URL**: `http://127.0.0.1:5000/api/admin/users/<username>/disconnect` (请将 `<username>` 替换为目标用户的用户名)
- **Headers**: `Authorization: Bearer <admin_user_token>` 