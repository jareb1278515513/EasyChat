const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const merge = require('webpack-merge');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpackBaseConfig = require('./webpack.base.js');

module.exports = merge(webpackBaseConfig,{
    mode: "development",
    devtool: 'eval-source-map',
    entry: {
        index: path.join(__dirname, "/test/test-in-node/index.js")
    },
    output: {
        path: path.join(__dirname, "/test/"),
        filename: "[name].js",
    },
    devServer: {
        contentBase: "./test", //本地服务器所加载的页面所在的目录
        port: "8088",
        historyApiFallback: true, //不跳转
        inline: true,
        hot: true,
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8080',
                pathRewrite: {'/api':''},
                changeOrigin: true,
                secure: false
            }
        }
    },
    optimization: {
        runtimeChunk: 'single',
        splitChunks: {
            cacheGroups: {
                vender: {
                    test: /[\\/]node_modules[\\/]/,
                    chunks: 'all',
                    minChunks: 1,
                    name: 'vender',
                    reuseExistingChunk: true,
                    minSize: 0,
                    priority: 10
                },
                commons: {
                    chunks: 'initial',
                    minChunks: 2,
                    name: 'commons',
                }
            }
        }
    },
    plugins: [
        new HtmlWebpackPlugin({
            filename: 'index.html',
            template: path.join(__dirname,'/test/test-in-node/template/index.template.html')
        }),
        new webpack.HotModuleReplacementPlugin(),
        new MiniCssExtractPlugin({
            filename: 'emoji-picker-vue.css',
            chunkFilename: 'emoji-picker-vue.css',
        })
    ]
})