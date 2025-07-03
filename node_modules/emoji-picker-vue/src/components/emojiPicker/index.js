import { emojiCodes, tabCodes, recentCodes } from './codepoints';

export default {
    props: {
        target: {
            required: true
        },
        show: {
            type: Boolean,
            required: true
        },
        config: {
            type: Object,
            default: null
        }
    },
    data() {
        return {
            emojiCodes,
            tabCodes,
            caret: 0,
            tabState: [],
            tabviewState: [],
            showIdx: 0,
            recentCodes,
            defaultStyle: {
                width: '288px',
                height: '180px'
            }
        }
    },
    created() {
        this.supportIE9Plus();
        this.tabCodes.forEach(_ => {
            this.tabState.push({ 'emoji-js-tab--is-active': false });
            this.tabviewState.push({ 'emoji-js-tabview--is-active': false })
        });
    },
    mounted() {
        this.setPosition();
        this.setStyle();
        this.tabState[this.showIdx]['emoji-js-tab--is-active'] = true;
        this.tabviewState[this.showIdx]['emoji-js-tabview--is-active'] = true;
        //target may be HTMLDivElement or undefined when this components is mounted
        if(this.target) {
            this.initTarget();
        }
    },
    watch: {
        target(){////target may be HTMLDivElement or undefined when this components is mounted
            this.initTarget();
        }
    },
    methods: {
        insertEmoji(codepoint, flag) {
            const html = this.target.innerHTML;
            this.target.innerHTML = html.substr(0, this.caret) + codepoint + html.substr(this.caret);
            
            codepoint.length < 9 ? this.caret += 1 : this.caret += 2;

            this.setRecent(flag, codepoint);
        },
        initTarget() {
            const type = Object.prototype.toString.call(this.target).slice(8,-1);
            if(type !== 'HTMLDivElement') throw new TypeError('prop [target] must be the element of input or div with contenteditable');
            this.addClickEventToTarget();
        },
        setRecent(flag, codepoint) {
            if (this.recentCodes.indexOf(codepoint) >= 0) return;
            flag ? '' : (this.recentCodes.length < 7 ?
                this.recentCodes.unshift(codepoint) :
                (this.recentCodes.pop(), this.recentCodes.unshift(codepoint))
            );
        },
        addClickEventToTarget() {
            this.target.addEventListener('click', () => {

                this.caret = document.getSelection().anchorOffset;
            });
            this.target.addEventListener('keyup', () => {

                this.caret = document.getSelection().anchorOffset;
            });
        },
        setPosition() {
            let emoji = this.$refs.emoji,
                trigger = emoji.children[0],
                emojiMain = emoji.children[1],
                top = trigger.offsetTop + trigger.offsetHeight,
                left = trigger.offsetLeft;
            emojiMain.style.top = top + 'px';
            emojiMain.style.left = left + 'px';
        },
        setStyle() {
            if(!this.config) return;

            const width = this.config.width,
                height = this.config.height;
            width ? this.defaultStyle.width = width : '';
            height ? this.defaultStyle.height = height : '';
            
        },
        switchTab(k) {
            this.tabState[this.showIdx]['emoji-js-tab--is-active'] = false;
            this.tabviewState[this.showIdx]['emoji-js-tabview--is-active'] = false;
            this.showIdx = k;
            this.tabState[k]['emoji-js-tab--is-active'] = true;
            this.tabviewState[k]['emoji-js-tabview--is-active'] = true;
        },
        supportIE9Plus() {
            //The color of unicode-emoji-code of IE9+ is only black and white
            window.navigator.userAgent.match(/(MSIE|Trident)/i) !== null ?
                document.body.style.fontFamily = 'Segoe UI Emoji' : '';
        }
    }
}