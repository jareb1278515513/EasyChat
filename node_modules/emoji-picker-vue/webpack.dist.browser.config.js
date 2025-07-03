const path = require('path');
const merge = require('webpack-merge');
const webpackBaseConfig = require('./webpack.base.js');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = merge(webpackBaseConfig,{
    mode: "production",
    entry: {
        index: path.join(__dirname, "/src/export-as-vue-plugin.js")
    },
    output: {
        path: path.join(__dirname, "/dist/browser/"),
        filename: "emoji-picker-vue.min.js",
        libraryTarget: 'umd',
        library: 'emojiPicker',
        umdNamedDefine: true
    },
    externals: {
        vue: 'vue'
    },
    optimization: {
    },
    plugins: [
        new OptimizeCSSAssetsPlugin(),
        new MiniCssExtractPlugin({
            filename: 'emoji-picker-vue.min.css',
            chunkFilename: 'emoji-picker-vue.min.css'
        })
    ]
})