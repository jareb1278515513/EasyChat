// Vue应用主入口文件
import { createApp } from 'vue'  // 导入Vue核心功能
import App from './App.vue'      // 导入根组件
import router from './router'    // 导入路由配置

// 创建Vue应用实例
// 使用路由插件
// 挂载到#app DOM元素
createApp(App).use(router).mount('#app')
