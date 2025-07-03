# emoji-picker-vue
## demo
![demo](./misc/emoji-picker-vue.gif)

[online](https://i9neq.codesandbox.io/)

[codesandbox](https://codesandbox.io/embed/new-butterfly-i9neq)
## In node

    npm install emoji-picker-vue | yarn add emoji-picker-vue
```js
import Vue from 'vue';
import emojiPicker from 'emoji-picker-vue';
import 'emoji-picker-vue/dist/index.css';
```
## In browser
```html
<head>
    <link rel="stylesheet" href="dist/browser/emoji-picker-vue.min.css"/>
</head>
<body>
    <script src="vue.min.js"></script>
    <script src="dist/browser/emoji-picker-vue.min.js"></script>
</body>
```

## config

Prop | Type | Default | Description
-|-|-|-
target | HTMLDivElement | @required | container in which emoji is put
show | Boolean | @required | control the display of emoji
config | Object | @optional | config the style of emoji
config.width | String | 288px | width of emoji
config.height | String | 180px | height of emoji

## custom
- custom your own emoji or add more emoji, you should edit  `src/components/codepoints.js`, then run `npm run release`, finally, new `index.js` will be generated in `dist/`, emoji codepoint can be found in [unicode.org/emoji](https://unicode.org/emoji/charts/emoji-list.html)

- custom theme, you should edit  `src/components/emojiPicker/index.styl`, then run `npm run release`, finally, new `index.css` will be generated in `dist/`