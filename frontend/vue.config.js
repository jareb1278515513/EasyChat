/**
 * Vue项目配置文件
 * 使用@vue/cli-service提供的defineConfig方法定义配置
 */
const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  // 需要转译的依赖项
  transpileDependencies: true,

  // 开发服务器配置
  devServer: {
    // 监听所有网络接口，校园网范围内可用
    host: '0.0.0.0',
    // 使用环境变量PORT或默认8081端口
    port: process.env.PORT || 8081,
    // 启用HTTPS
    https: true
  }
})
