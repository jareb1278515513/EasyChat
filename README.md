<div align="center">
  <h1>
    <img src="img/logo.png" width="30" alt="logo">
    EasyChat - 安全的端到端加密即时通讯
  </h1>
  <p>
    <strong>一款采用C/S与P2P混合架构，通过端到端加密和信息隐藏技术，确保通信私密与安全的即时通讯桌面应用。</strong>
  </p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D" alt="Vue.js">
    <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
    <img src="https://img.shields.io/badge/Socket.io-010101?style=for-the-badge&logo=socketdotio&logoColor=white" alt="Socket.io">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge" alt="License: MIT">
  </p>
</div>

---


## 📜 目录

- [✨ 主要功能](#-主要功能)
  - [核心通讯功能](#核心通讯功能)
  - [安全特性](#安全特性)
  - [管理员功能](#管理员功能)
- [🛠️ 技术栈与架构](#️-技术栈与架构)
- [🏗️ 项目代码结构](#️-项目代码结构)
- [🚀 安装与运行](#-安装与运行)
- [🤝 贡献指南](#-贡献指南)
- [📝 许可证](#-许可证)
- [📚 API 文档](#-api-文档)

---

## ✨ 主要功能

### 核心通讯功能
- **👤 用户认证**: 提供完整的用户注册和登录流程，包含邮箱格式验证和密码强度评估。
- **👥 好友管理**: 支持添加好友、删除好友、实时接受/拒绝好友请求。
- **🟢 实时状态**: 通过 WebSocket 实时更新好友的在线状态。
- **💬 P2P 即时通讯**: 用户间的聊天消息通过 WebRTC (PeerJS) 直接在客户端之间传输，不经过中心服务器。
- **⚙️ 设置中心**: 用户可以随时更改自己的邮箱和密码，并提供相应的输入验证。
- **😉 发送表情符号**: 在聊天中轻松选择并发送 Emoji，丰富表达方式。
- **ℹ️ 查看好友资料**: 在聊天界面方便地查看好友的公开个人信息。
- **⚙️ 个性化设置中心**: 用户可以随时更改自己的邮箱、密码，并编辑个人资料（性别、年龄、个人简介）。

### 安全特性
- **🔒 端到端加密 (E2EE)**: 在建立P2P连接后，客户端之间会通过RSA非对称加密协商一个一次性的AES对称密钥。所有后续的聊天消息都使用此密钥进行加密，确保只有通信双方可以解密消息内容。
- **🔑 公钥管理**: 服务器负责托管用户的公钥，以便于进行密钥协商。
- **🖼️ 信息隐藏 (Steganography)**: 用户可以将文本信息隐藏在图片中发送，接收方可以从图片中提取出隐藏的文本，为通信提供额外的安全层。

### 管理员功能
- **👑 内置管理员**: 系统通过初始化脚本内置 `admin` 账户 (`admin` / `liujialun`)。
- **📊 用户看板**: 管理员可以查看系统中所有用户的列表及其详细信息（如邮箱、在线状态等）。
- **🔌 强制下线**: 管理员可以强制将任何在线用户踢下线。
- **🗑️ 删除用户**: 管理员可以从数据库中永久删除任何用户及其所有相关数据（如好友关系、好友请求等），已配置级联删除以保证数据一致性。

## 🛠️ 技术栈与架构

- **后端**:
  - **框架**: Python, Flask
  - **实时通信**: Flask-SocketIO
  - **数据库**: SQLite3
- **前端**:
  - **框架**: Vue.js 3 (Options API)
  - **P2P通信**: PeerJS
- **🏛️ 架构**:
  系统采用 **客户端/服务器 (C/S) 与 P2P 的混合架构**。
  - **中心服务器**: 负责处理用户注册、登录认证、好友关系管理、用户状态维护以及P2P连接建立前的信令交换。
  - **P2P网络**: 一旦好友双方建立连接，后续的聊天消息将直接通过P2P网络传输，不经过服务器，保证了通信的低延迟和私密性。

## 🏗️ 项目代码结构
```
EasyChat/
├── backend/            # 后端 Flask 应用
│   ├── app/            # 应用核心代码包
│   │   ├── api/        # RESTful API 蓝图
│   │   ├── __init__.py # 应用工厂函数
│   │   ├── models.py   # SQLAlchemy 数据库模型
│   │   └── socket_events.py # Socket.IO 事件处理器
│   ├── migrations/     # 数据库迁移脚本
│   ├── venv/           # Python 虚拟环境
│   ├── config.py       # 配置文件
│   ├── requirements.txt# Python 依赖
│   └── run.py          # 应用启动脚本
│
├── frontend/           # 前端 Vue.js 应用
│   ├── public/         # 公共文件 (如 index.html)
│   ├── src/            # 前端源码
│   │   ├── assets/     # 静态资源 (图片等)
│   │   ├── router/     # 路由配置
│   │   ├── services/   # API, Socket, PeerJS 服务封装
│   │   ├── utils/      # 工具函数 (加密、隐写)
│   │   ├── views/      # 页面级组件 (LoginView, ChatView 等)
│   │   ├── App.vue     # 根组件
│   │   └── main.js     # 应用入口
│   ├── package.json    # npm 依赖和脚本
│   └── vue.config.js   # Vue CLI 配置文件
│
├── img/                # README 文档中使用的图片
├── BACKEND_API_GUIDE.md# 后端 API 详细文档
└── README.md           # 项目说明文档
```

## 🚀 安装与运行

### 1. 后端设置

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活Python虚拟环境
# Windows
python -m venv venv
venv\\Scripts\\activate
# macOS/Linux
# python3 -m venv venv
# source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化/重置数据库并创建管理员账户
#    (管理员用户名: admin, 密码: liujialun)
python reset_db.py

# 5. 启动后端服务
python run.py
```
> 后端服务将运行在 `http://localhost:5000`。

### 2. 前端设置

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 运行开发服务器
#    (支持通过环境变量指定端口, 默认为8081)
npm run serve
```
> 前端开发服务器将运行在 `https://localhost:8081` (或其他指定端口)。
>
> **注意**：当同一个主机启动多个前端以模拟多用户时，推荐使用不同的浏览器或者打开浏览器的隐私模式。

### 3. 快速启动 (Windows)
为了方便 Windows 用户，项目根目录提供了两个批处理脚本：
- `start_backend.bat`: 自动进入后端目录，激活虚拟环境，并启动 Flask 服务器。
- `start_frontend.bat`: 自动进入前端目录，并启动 Vue 开发服务器。

> 在完成上述的首次依赖安装后，你只需分别双击运行这两个脚本即可快速启动整个应用。

## 🤝 贡献指南

我们欢迎各种形式的贡献！如果你有任何想法或建议，请随时提出 Issue 或提交 Pull Request。

1.  Fork 本仓库
2.  创建你的新分支 (`git checkout -b feature/AmazingFeature`)
3.  提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4.  将你的分支推送到远程 (`git push origin feature/AmazingFeature`)
5.  开启一个 Pull Request

## 📝 许可证

本项目采用 MIT 许可证。详情请见 `LICENSE` 文件。

## 📚 API 文档

详细的后端 API 和 WebSocket 事件说明，请参阅项目中的 `