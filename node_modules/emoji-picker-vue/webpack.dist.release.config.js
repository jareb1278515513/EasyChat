const path = require('path');
const merge = require('webpack-merge');
const webpackBaseConfig = require('./webpack.base.js');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = merge(webpackBaseConfig,{
    mode: "production",
    entry: {
        index: path.join(__dirname, "/src/components/emojiPicker/index.vue")
    },
    output: {
        path: path.join(__dirname, "/dist/"),
        filename: "index.js",
        libraryTarget: 'umd',
        library: 'emojiPicker',
        umdNamedDefine: true
    },
    externals: {
        vue: 'vue'
    },
    optimization: {
        //minimize: false
    },
    plugins: [
        new OptimizeCSSAssetsPlugin(),
        new MiniCssExtractPlugin({
            filename: 'index.css',
            //chunkFilename: 'emoji-picker-vue.min.css'
        })
    ]
})