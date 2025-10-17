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
  <span ref="tooltip" data-toggle="tooltip">
    <slot></slot>
  </span>
</template>

<script>
export default {
  props: {
    title: String,
    container: {
      type: String,
      default: 'body',
    },
    placement: {
      type: String,
      default: 'top',
    },
  },
  data() {
    return {
      tooltip: null,
    };
  },
  watch: {
    title() {
      this.tooltip.attr('data-original-title', this.title).tooltip('update');
    },
  },
  mounted() {
    this.tooltip = $(this.$refs.tooltip).tooltip({
      boundary: 'window',
      container: this.container,
      placement: this.placement,
      title: this.title,
    });
  },
  unmounted() {
    this.tooltip.tooltip('dispose');
  },
};
</script>
