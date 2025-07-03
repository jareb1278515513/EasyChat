### P2P 实现方法：使用 PeerJS 简化 WebRTC

本项目采用 **PeerJS** 库来建立和管理客户端之间的 P2P（点对点）连接。PeerJS 是一个强大的 JavaScript 库，它将复杂、繁琐的 WebRTC 连接过程封装成了简洁、易用的 API，让开发者可以轻松实现浏览器之间的直接数据通信。

#### PeerJS 是如何工作的？

虽然 PeerJS 让我们不必手动处理 WebRTC 的细节，但理解其背后的基本原理仍然很重要：

1.  **WebRTC 技术**: WebRTC 是现代浏览器内置的一套标准 API，允许网页在不需要任何中间服务器中转的情况下，直接在用户之间传输音视频或任意数据。但 WebRTC 本身只提供了建立连接的"零件"，并没有规定如何让两个素不相识的客户端找到对方并交换连接信息。这个交换信息的过程被称为"**信令 (Signaling)**"。

2.  **信令服务器**: 为了让两个客户端能够"认识"彼此，它们需要一个共同的"中间人"来传递信令。在我们的项目中，这个中间人就是我们已有的 **Flask-SocketIO 后端**。PeerJS 会自动生成所有必要的信令数据（如 Offer, Answer, ICE Candidates），我们只需要通过 WebSocket 将这些数据在客户端之间进行转发即可。

#### 在 EasyChat 中的具体实现流程

1.  **初始化与ID分配**:
    -   **服务层**: P2P连接的初始化逻辑位于 `frontend/src/services/peer.js` 的 `initializePeer(username)` 函数中。此函数会创建一个新的PeerJS实例。
    -   **视图层**: 当用户成功登录并进入 `ChatView.vue` 后，其 `created()` 生命周期钩子会调用 `initializePeer()`，并使用当前登录的用户名作为其在P2P网络中的唯一ID。

2.  **连接请求**:
    -   **用户操作**: 当用户在 `ChatView.vue` 中点击好友列表中的某个好友时，会触发 `selectRecipient(username)` 方法。
    -   **发起连接**: 在 `selectRecipient` 方法内部，会调用 `peer.connect('B的用户名')` 来向目标好友发起P2P连接请求。PeerJS库会在后台自动处理所有复杂的信令交换。

3.  **数据通道处理**:
    -   **接收连接**: 当一个客户端收到另一个客户端的连接请求时，`peer.js` 中 `initializePeer` 函数里设置的 `peer.on('connection', callback)` 事件监听器会被触发。
    -   **打开连接**: 在 `ChatView.vue` 的 `setupConnectionHandlers` 方法中，`conn.on('open', callback)` 事件监听器负责处理连接成功打开后的逻辑，最重要的是，它会通过比较双方用户名来决定由哪一方发起后续的密钥交换。
    -   **收发数据**: 同样在 `setupConnectionHandlers` 中，`conn.on('data', callback)` 负责接收所有通过P2P通道传来的数据（加密消息、密钥等）。

4.  **直接通信**:
    -   一旦数据通道建立，`ChatView.vue` 中的 `sendMessage` 方法就会将用户的聊天消息通过 `conn.send()` 直接发送给对方，不再经过服务器。

---

### 端到端加密（E2EE）的实现

**我们实现了端到端加密的完整方案，严格遵循了您在 `需求.txt` 中提出的要求。**

具体实现流程如下，涉及 `frontend/src/utils/crypto.js` 中的加密工具函数和 `frontend/src/views/ChatView.vue` 中的业务逻辑。

1.  **生成密钥对（非对称加密）**：
    -   **时机**: 当一个新用户在 `RegisterView.vue` 中成功注册时。
    -   **操作**: 系统会调用 `crypto.js` 中的 `generateRsaKeyPair()` 函数，为用户生成一对唯一的、高强度的 **RSA 公私钥**。
    -   **存储**:
        -   **公钥** 通过 `api.register()` 接口上传到后端服务器，以便其他用户可以请求获取。
        -   **私钥** **绝对不会离开用户的设备**。它被安全地存储在浏览器的 `localStorage` 中，与当前登录的用户绑定。

2.  **协商会话密钥（密钥交换）**：
    -   **时机**: 当一个P2P连接在 `ChatView.vue` 中成功建立后 (`conn.on('open')`)。
    -   **操作**: 由用户名字典序较小的一方，在 `performKeyExchange` 方法中执行以下操作：
        1.  调用 `api.getPublicKey(recipientUsername)` 从服务器获取对方的**公钥**。
        2.  调用 `crypto.js` 中的 `generateSymmetricKey()` 在本地生成一个用于本次聊天的一次性的、高效的**AES对称密钥**。
        3.  调用 `crypto.js` 中的 `encryptWithPublicKey()`，使用对方的公钥加密这个刚生成的AES密钥。

3.  **安全发送会ahh话密钥**：
    -   在 `performKeyExchange` 方法的最后，加密后的AES密钥通过 `conn.send()` 发送给对方。
    -   对方在 `handleNewP2PMessage` 方法中接收到这条消息，并使用 `crypto.js` 中的 `decryptWithPrivateKey()` 和自己本地存储的私钥来解密，从而安全地获得这个对称密钥。

4.  **加密通信（对称加密）**：
    -   **发送**: 在 `sendMessage` 方法中，消息在发送前会使用 `crypto.js` 中的 `encryptSymmetric()` 和协商好的AES密钥进行加密。
    -   **接收**: 在 `handleNewP2PMessage` 方法中，收到的加密消息会使用 `crypto.js` 中的 `decryptSymmetric()` 和同一个AES密钥进行解密，然后渲染到聊天窗口。

通过这个流程，我们实现了真正的端到端加密。服务器只参与了公钥的分发，对真正的通信内容（以及用于加密内容的对称密钥）一无所知。