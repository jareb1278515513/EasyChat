# 接入 DeepSeek AI 助手功能实现指南

本文档旨在详细阐述 EasyChat 项目中"DeepSeek 助手"功能的具体实现方法。我们采用了一种对现有代码侵入性极小、复用率极高的"虚拟好友"方案。

## 核心设计思路：虚拟好友

为了在不引入全新聊天组件、最大化复用现有UI和逻辑的前提下集成AI对话功能，我们将DeepSeek大语言模型"伪装"成一个特殊的好友。

**优势:**
- **高代码复用**：完全复用 `ChatView.vue` 中的好友列表、聊天窗口、消息气泡等UI元素。
- **低开发成本**：无需编写新的视图组件，改动集中在逻辑层面。
- **统一用户体验**：用户与AI助手交互的方式和与真人好友聊天完全一致，无需学习新界面。

## 实现步骤

### 第一步：安全的 API 密钥配置

直接将API密钥硬编码在前端代码中是极不安全的，因为密钥会随代码一同暴露给最终用户。我们采用标准的 `.env` 文件来管理密钥。

1.  在 `frontend/` 目录下创建一个名为 `.env.local` 的文件。
2.  在该文件中添加您的DeepSeek API密钥，格式如下：
    ```
    VUE_APP_DEEPSEEK_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
    ```
    **注意**：`VUE_APP_` 是 Vue CLI 项目读取环境变量的强制前缀。

### 第二步：创建独立的 AI 服务模块

为了保持代码的模块化和清晰性，我们将所有与DeepSeek API的交互逻辑都封装在一个专属的服务模块中。

1.  **文件位置**：`frontend/src/services/ai.js`
2.  **核心功能**：该文件导出一个核心函数 `getAiReply(messages)`。
    -   **读取密钥**：它通过 `process.env.VUE_APP_DEEPSEEK_API_KEY` 在一个安全的环境中读取密钥。
    -   **API 请求**：使用 `axios` 库向 DeepSeek 的 `/v1/chat/completions` 端点发起POST请求。
    -   **参数构造**：根据API文档，构造包含 `model`, `messages` 等参数的请求体。
    -   **错误处理**：封装了对API密钥未配置、网络请求失败、API返回错误等情况的优雅处理，并返回用户友好的提示信息。

### 第三步：在聊天视图中集成

这是将"虚拟好友"变为现实的关键一步，所有改动都集中在 `frontend/src/views/ChatView.vue` 文件中。

1.  **定义AI助手对象**：
    在 `<script>` 标签的顶部，我们定义一个`const`常量来代表AI助手。这个对象包含了作为"好友"所需的所有属性（如`id`, `username`, `avatar_url`等）。
    ```javascript
    const AI_ASSISTANT = {
      id: 'deepseek-ai-assistant', // 唯一的、不会与真实用户冲突的ID
      username: 'DeepSeek助手',
      is_online: true,
      avatar_url: require('@/assets/ai_avatar.png'),
      // ... 其他资料属性
    };
    ```

2.  **注入好友列表**：
    我们修改了 `fetchFriends()` 方法。在成功从后端获取真实好友列表后，使用 `unshift()` 方法将`AI_ASSISTANT`对象添加到好友数组的最前面，确保它始终在列表顶部。

3.  **分流聊天逻辑**：
    我们修改了多个核心方法，通过判断当前聊天对象（`this.currentRecipient`）是否为AI助手来执行不同的逻辑分支。
    -   **`selectRecipient(username)`**: 如果用户点击的是AI助手，则跳过所有P2P连接的尝试。
    -   **`sendMessage()`**:
        -   如果聊天对象是AI助手，则调用 `ai.js` 中的 `getAiReply()` 函数，并将用户的输入和AI的回复依次渲染到聊天窗口。
        -   如果聊天对象是普通好友，则执行原有的P2P加密消息发送流程。
    -   **`removeFriend(friendId)`** 和 **`showFriendProfile(username)`**: 同样增加了判断，阻止用户删除AI助手，并为其展示预设的资料信息。

通过以上三个步骤，我们就以一种优雅且高效的方式，将强大的AI对话功能无缝地集成到了现有的即时通讯应用中。 