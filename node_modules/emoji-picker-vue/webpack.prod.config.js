const path = require('path');
const merge = require('webpack-merge');
const webpackBaseConfig = require('./webpack.base.js');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = merge(webpackBaseConfig,{
    mode: "production",
    entry: {
        index: path.join(__dirname, "/test/index.js")
    },
    output: {
        path: path.join(__dirname, "/test/prod-test"),
        filename: "[name].js",
        libraryTarget: 'umd',
        library: 'emoji-picker-vue',
        umdNamedDefine: true
    },
    externals: {
        vue: 'vue',
    },
    plugins: [
        new HtmlWebpackPlugin({
            filename: 'index.html',
            template: path.join(__dirname,'/test/template/index.template.html')
        }),
        new OptimizeCSSAssetsPlugin(),
        new MiniCssExtractPlugin({
            filename: 'emoji-picker-vue.min.css',
            chunkFilename: 'emoji-picker-vue.min.css',
        })
    ]
})