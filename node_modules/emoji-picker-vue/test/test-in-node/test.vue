<template lang="pug">
div
    div(ref='container' class="target" contenteditable)
    emojiPicker(:target="target" :show="isShowEmoji")
        label(@click="showEmoji" class="emoji-trigger" v-html="triggerCode")
</template>
<script>
import Vue from 'vue';
import emojiPicker from '../../dist/index.js';
import '../../dist/index.css';
export default {
    components: {
        emojiPicker
    },
    data(){
        return {
            target: null,
            isShowEmoji: false,
            triggerCode: '&#x1F600;',
            customStyle: {
            // width: '288px',
            // height: '180px'
            }
        }
    },
    mounted() {
        this.target = this.$refs.container;
    },
    methods: {
        showEmoji() {
            this.isShowEmoji = !this.isShowEmoji;
        }
    }    
}
</script>
<style>
    .emoji-trigger {
        font-size: 24px;
        cursor: pointer;
        user-select: none;
    }
    .target {
        height: 100px;
        width: 300px;
        border: 1px solid #eee;
        overflow-y: auto;
    }
</style>