<style src="./index.styl" lang="stylus"></style>
<script src="./index.js"/>

<template lang="pug">
div(ref="emoji" class="emoji")
    slot
    div(class="emoji-main" v-show="show")
        div(class="emoji-main__tab")
            ul(class="emoji-l-list")
                li(class="emoji-l-list__item--for-tab" v-for="(v,k) in tabCodes" :key="k")
                    span(class="emoji-main__entity" @click="switchTab(k)" :class="tabState[k]" v-html="v")
                    
        div(class="emoji-main__recent")
            p(class="emoji-main__text") recent
            ul(class="emoji-l-list")
                li(class="emoji-l-list__item" @click="insertEmoji(v,'recent')" v-for="(v,k) in recentCodes" :key="k" v-html="v")
        div(ref="emojibody" :style="defaultStyle" class="emoji-main__body emoji__scroll")
            div(class="emoji-main__tab-view" v-for="(v,k) in emojiCodes" :key="k" :class="tabviewState[k]")
                ul(class="emoji-l-list")
                    li(class="emoji-l-list__item" @click="insertEmoji(vv)" v-for="(vv,kk) in v.codes" :key="kk" v-html="vv")
</template>