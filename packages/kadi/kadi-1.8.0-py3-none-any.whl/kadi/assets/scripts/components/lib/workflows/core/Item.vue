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
  <div class="item" @click="onClick" @mouseover="onMouseover" @mouseleave="onMouseleave" @pointerdown.stop @wheel.stop>
    <div class="d-flex justify-content-between align-items-center">
      <span :class="item.class || ''">{{ item.label }}</span>
      <i v-if="item.subitems" class="fa-solid fa-xs fa-angle-right text-muted"></i>
    </div>
    <div v-if="item.subitems && subitemsVisible" class="subitems">
      <item v-for="subitem in item.subitems" :key="subitem.key" :item="subitem"></item>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/menu.scss';

.subitems {
  border: 1px solid $context-menu-border-color;
  border-radius: $context-menu-radius;
  left: 100%;
  max-height: 155px;
  overflow-x: hidden;
  overflow-y: auto;
  position: absolute;
  top: 0;
}
</style>

<script>
export default {
  name: 'Item',
  props: {
    item: Object,
  },
  emits: ['hide'],
  data() {
    return {
      visibleHandle: null,
      subitemsVisible: false,
    };
  },
  methods: {
    onClick() {
      this.item.handler();

      if (!this.item.keepOpen) {
        this.$emit('hide');
      }
    },
    onMouseover() {
      window.clearTimeout(this.visibleHandle);
      this.subitemsVisible = true;
    },
    onMouseleave() {
      window.clearTimeout(this.visibleHandle);
      this.visibleHandle = window.setTimeout(() => this.subitemsVisible = false, 50);
    },
  },
};
</script>
