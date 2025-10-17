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
  <button ref="tooltip" type="button" class="btn btn-light" :title="msg" @click="copy">
    <slot>
      <i class="fa-solid fa-copy"></i>
    </slot>
  </button>
</template>

<script>
export default {
  props: {
    content: String,
    showTooltip: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      tooltip: null,
      msg: $t('Copy to clipboard'),
    };
  },
  mounted() {
    if (this.showTooltip) {
      this.tooltip = $(this.$refs.tooltip).tooltip({title: this.msg});
    }
  },
  unmounted() {
    if (this.showTooltip) {
      this.tooltip.tooltip('dispose');
    }
  },
  methods: {
    copy() {
      navigator.clipboard.writeText(this.content).catch(() => console.warn('Cannot copy to clipboard.'));
    },
  },
};
</script>
