/**
 * Vue路由配置文件
 * 配置整个应用的路由结构和导航逻辑
 * 使用vue-router 4.x版本
 */

import { createRouter, createWebHashHistory } from 'vue-router'

/**
 * 页面组件导入
 * 使用懒加载优化性能
 */
import LoginView from '../views/LoginView.vue'      // 用户登录页面
import RegisterView from '../views/RegisterView.vue' // 用户注册页面
import ChatView from '../views/ChatView.vue'        // 主聊天界面
import SettingsView from '../views/SettingsView.vue' // 用户设置页面
import AdminView from '../views/AdminView.vue'      // 管理员后台页面

/**
 * 路由配置数组
 * 每个路由对象包含以下常用属性:
 * - path: 路由路径
 * - name: 路由名称作为唯一标识
 * - component: 对应组件
 * - meta: 路由元信息
 * - redirect: 重定向路径
 * - children: 嵌套路由
 */
const routes = [
  // 根路径重定向到登录页，即默认页面
  {
    path: '/',
    redirect: '/login'
  },
  // 登录路由 - 无需认证
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      title: '用户登录',      // 页面标题
      requiresAuth: false    // 是否需要登录
    }
  },
  // 注册路由 - 无需认证
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: {
      title: '用户注册',
      requiresAuth: false
    }
  },
  // 主聊天路由 - 需要登录认证
  {
    path: '/chat',
    name: 'chat',
    component: ChatView,
    meta: {
      title: '聊天室',
      requiresAuth: true     // 需要登录后才能访问
    }
  },
  // 设置路由 - 需要登录认证
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: {
      title: '个人设置',
      requiresAuth: true
    }
  },
  // 管理后台路由 - 需要管理员权限
  {
    path: '/admin',
    name: 'admin',
    component: AdminView,
    meta: {
      title: '管理后台',
      requiresAuth: true,
      requiresAdmin: true    // 需要管理员权限
    }
  }
]

/**
 * 创建路由实例
 * @type {import('vue-router').Router}
 * 配置项说明:
 * - history: 路由历史模式
 * - routes: 路由配置数组
 * - scrollBehavior: 滚动行为控制
 */
const router = createRouter({
  // 使用hash模式
  history: createWebHashHistory(),

  // 路由配置
  routes,

  // 可选的滚动行为配置
  scrollBehavior(to, from, savedPosition) {
    // 返回滚动位置对象或选择器
    return savedPosition || { top: 0 }
  }
})

/**
 * 路由全局前置守卫
 * 可用于权限控制、页面标题设置等
 */
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title || 'EasyChat'
  next()
})

// 导出路由实例供main.js使用
export default router