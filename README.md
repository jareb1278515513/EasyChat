# EasyChat - 安全即时通讯系统

EasyChat 是一个采用混合架构（C/S 和 P2P）并注重安全性的即时通讯应用。它利用非对称与对称加密技术保障端到端（E2E）通信的私密性，并实现了将信息隐藏在图片中的隐写术功能。

## ✨ 核心功能

*   **用户系统**: 支持用户注册和登录认证。
*   **好友管理**: 支持添加/删除好友、处理好友请求。
*   **实时在线状态**: 通过 WebSocket 实时同步好友的在线状态。
*   **端到端加密 (E2EE) 聊天**:
    *   用户登录时在本地生成 RSA 密钥对。
    *   通过服务器交换公钥，使用非对称加密协商对称密钥（AES）。
    *   所有好友间的文本消息均通过 AES-GCM 进行加密，确保只有通信双方可以解密。
*   **信息隐藏 (隐写术)**:
    *   支持将文本信息隐藏在图片中发送。
    *   利用 LSB (最低有效位) 算法将数据写入图片像素，接收方可提取隐藏信息。
*   **P2P 通信**:
    *   好友间的消息（包括加密文本和含密图片）通过 WebRTC (PeerJS) 进行点对点直接传输，不经过服务器中转。
*   **管理员功能**:
    *   提供 API 供管理员查看所有用户状态。
    *   提供 API 供管理员强制任意用户下线。

## 🛠️ 技术栈

*   **后端**:
    *   **框架**: Python, Flask, Flask-SocketIO
    *   **数据库**: SQLite + Flask-SQLAlchemy
    *   **数据库迁移**: Alembic + Flask-Migrate
    *   **认证**: JWT (PyJWT)
    *   **密码处理**: Bcrypt
*   **前端**:
    *   **框架**: Vue.js (Vue 3)
    *   **路由**: Vue Router
    *   **P2P通信**: PeerJS (WebRTC)
    *   **实时通信**: Socket.IO Client
    *   **HTTP请求**: Axios
*   **桌面应用构建** (已配置):
    *   Electron, electron-builder

## 🚀 启动项目
### 0.快速启动
> 快速启动的前提是已经配置好下文所说的环境

Windows直接运行根目录下的[start_frontend.bat](start_frontend.bat)和[start_backend.bat](start_backend.bat)即可分别启动前后端。

### 1. 环境准备

*   [Node.js](https://nodejs.org/) (v16 或更高版本)
*   [Python](https://www.python.org/) (v3.8 或更高版本)

### 2. 后端设置

首先，从项目根目录进入后端文件夹，创建虚拟环境并安装依赖。

```bash
# 进入后端目录
cd backend

# 创建 Python 虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS / Linux:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化/升级数据库
# (首次运行时会创建 app.db 文件和数据表)
flask db upgrade
```

### 3. 前端设置

打开一个新的终端，从项目根目录进入前端文件夹，并安装依赖。

```bash
# 进入前端目录
cd frontend

# 安装 npm 依赖
npm install
```

### 4. 运行应用

你需要保持两个终端窗口分别运行后端和前端。

*   **终端 1：运行后端**

   确保你仍处于 `backend` 目录下并且虚拟环境已激活。

   ```bash
   # 运行 Flask 应用
   flask run
   ```

   服务器默认会在 `http://127.0.0.1:5000` 启动。

*   **终端 2：运行前端**

   确保你处于 `frontend` 目录下。

   ```bash
   # 启动 Vue 开发服务器
   npm run serve
   ```

   前端开发服务器通常会启动在 `http://localhost:8080`。

### 5. 开始使用

在浏览器中打开前端应用的地址 (如 `http://localhost:8080`)，你就可以开始注册用户、添加好友并进行安全通讯了。

> **注意**: 要测试 P2P 聊天，你需要使用不同的浏览器或在浏览器的隐私模式下打开应用，并注册两个不同的用户。

## 📝 API 文档

本项目的后端 API 规范已详细记录在根目录的 `BACKEND_API_GUIDE.md` 文件中。该文档包含了所有 RESTful API 的端点、请求/响应格式以及 WebSocket 事件的详细说明。 