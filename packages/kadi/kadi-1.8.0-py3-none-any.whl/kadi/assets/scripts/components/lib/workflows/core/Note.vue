<!-- Copyright 2022 Karlsruhe Institute of Technology
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
  <div ref="node" class="node" :class="[data.selected ? 'selected': '']">
    <textarea v-model="text" class="content form-control" spellcheck="false" :rows="rows" @pointerdown.stop></textarea>
  </div>
</template>

<style lang="scss" scoped>
$bg-note: #f5ec9a;

.node {
  background: $bg-note;
  border: 2px solid $bg-note;
  cursor: pointer;
  padding-top: 30px;
  width: 350px;

  &:hover, &.selected {
    background: darken($bg-note, 20%);
    border: 2px solid darken($bg-note, 20%);
  }

  .content {
    background: rgba(lighten($bg-note, 15%), 0.85);
    border: 0;
    border-radius: 0;
    box-shadow: none;
    color: black;
    min-height: 35px;
    overflow: hidden;
    padding: 5px;
    resize: none;
  }
}
</style>

<script>
export default {
  props: {
    data: Object,
    emit: Function,
    seed: Number,
  },
  data() {
    return {
      text: this.data.text,
    };
  },
  computed: {
    rows() {
      return this.text.split('\n').length;
    },
  },
  watch: {
    text() {
      this.data.setText(this.text);
    },
  },
  mounted() {
    const observer = new ResizeObserver((entries) => {
      const borderBox = entries[0].borderBoxSize[0];
      this.data.setWidth(borderBox.inlineSize);
      this.data.setHeight(borderBox.blockSize);
    });
    observer.observe(this.$refs.node);
  },
};
</script>
