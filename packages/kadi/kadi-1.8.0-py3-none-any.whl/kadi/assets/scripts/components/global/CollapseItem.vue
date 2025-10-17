<!-- Copyright 2020 Karlsruhe Institute of Technology
   -
   - Licensed under the Apache License, Version 2.0 (the "License");
   - you may not use this file except in compliance with the License.
   - You may obtain a copy of the License at
   -
   -     http://www.apache.org/licenses/LICENSE-2.0
   -
   - Unless required by applicable law or agreed to in writing, software
   - distributed under the License is distributed on an "AS IS" BASIS,
   - WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   - See the License for the specific language governing permissions and
   - limitations under the License. -->

<template>
  <a href="#" tabindex="-1" @click.prevent="collapseItem">
    <i :class="iconClass"></i>
    <slot>{{ collapseText }}</slot>
  </a>
</template>

<script>
export default {
  props: {
    id: String,
    isCollapsed: {
      type: Boolean,
      default: false,
    },
    showIconClass: {
      type: String,
      default: 'fa-solid fa-angle-down',
    },
    hideIconClass: {
      type: String,
      default: 'fa-solid fa-angle-up',
    },
  },
  emits: ['collapse'],
  data() {
    return {
      initialized: false,
      isCollapsed_: this.isCollapsed,
      prevDisplay: 'block',
    };
  },
  computed: {
    iconClass() {
      return this.isCollapsed_ ? this.showIconClass : this.hideIconClass;
    },
    collapseText() {
      return this.isCollapsed_ ? $t('Show') : $t('Hide');
    },
  },
  watch: {
    isCollapsed() {
      if (this.isCollapsed_ === this.isCollapsed) {
        return;
      }

      if (this.isCollapsed) {
        this.collapseItem('hide');
      } else {
        this.collapseItem('show');
      }
    },
  },
  mounted() {
    if (this.isCollapsed_) {
      this.collapseItem('hide');
    } else {
      this.collapseItem('show');
    }

    this.initialized = true;
  },
  methods: {
    collapseItem(collapse = null) {
      const elem = document.getElementById(this.id);

      if (!elem) {
        return;
      }

      if (collapse === 'hide') {
        this.isCollapsed_ = true;
      } else if (collapse === 'show') {
        this.isCollapsed_ = false;
      } else {
        this.isCollapsed_ = !this.isCollapsed_;
      }

      const display = elem.style.display;

      if (display && display !== 'none') {
        this.prevDisplay = display;
      }

      if (this.isCollapsed_) {
        elem.style.display = 'none';
      } else {
        elem.style.display = this.prevDisplay;
      }

      if (this.initialized) {
        this.$emit('collapse', this.isCollapsed_);
      }
    },
  },
};
</script>
