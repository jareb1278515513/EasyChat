/**
 * Electron主进程入口文件
 * 负责管理应用程序生命周期、创建浏览器窗口和处理系统事件
 */

'use strict'

// Electron模块导入
import { app, protocol, BrowserWindow } from 'electron'
// Vue CLI Electron Builder插件工具
import { createProtocol } from 'vue-cli-plugin-electron-builder/lib'
// Electron开发者工具安装器
import installExtension, { VUEJS3_DEVTOOLS } from 'electron-devtools-installer'

// 环境判断
const isDevelopment = process.env.NODE_ENV !== 'production'

/**
 * 注册自定义协议
 */
protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: {
      secure: true,  // 启用安全策略
      standard: true // 作为标准协议处理
    }
  }
])

/**
 * 创建浏览器窗口
 */
async function createWindow() {
  // 创建浏览器窗口配置
  const win = new BrowserWindow({
    width: 800,   // 初始宽度
    height: 600,  // 初始高度
    webPreferences: {
      // Node.js集成配置，根据环境变量决定
      nodeIntegration: process.env.ELECTRON_NODE_INTEGRATION,
      // 上下文隔离配置，与nodeIntegration相反
      contextIsolation: !process.env.ELECTRON_NODE_INTEGRATION
    }
  })

  // 开发模式加载webpack dev server
  if (process.env.WEBPACK_DEV_SERVER_URL) {
    await win.loadURL(process.env.WEBPACK_DEV_SERVER_URL)
    // 非测试环境下打开开发者工具
    if (!process.env.IS_TEST) win.webContents.openDevTools()
  } else {
    // 生产模式加载app协议
    createProtocol('app')
    win.loadURL('app://./index.html')
  }
}

// 所有窗口关闭时退出应用，但是macOS除外，因为macOS通常应用会保持活动状态直到用户显式退出
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// macOS激活事件处理
app.on('activate', () => {
  // 点击dock图标且没有其他窗口时重新创建窗口
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow()
  }
})

// Electron初始化完成事件
app.on('ready', async () => {
  // 开发模式下安装Vue开发者工具
  if (isDevelopment && !process.env.IS_TEST) {
    try {
      await installExtension(VUEJS3_DEVTOOLS)
    } catch (e) {
      console.error('Vue Devtools安装失败:', e.toString())
    }
  }
  // 创建主窗口
  createWindow()
})

// 开发模式下处理父进程退出请求
if (isDevelopment) {
  // Windows平台消息处理
  if (process.platform === 'win32') {
    process.on('message', (data) => {
      if (data === 'graceful-exit') {
        app.quit()
      }
    })
  } else {
    // 其他平台信号处理
    process.on('SIGTERM', () => {
      app.quit()
    })
  }
}
