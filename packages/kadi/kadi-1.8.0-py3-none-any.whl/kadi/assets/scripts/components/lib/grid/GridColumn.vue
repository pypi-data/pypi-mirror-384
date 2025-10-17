<!-- Copyright 2024 Karlsruhe Institute of Technology
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
  <div ref="column">
    <div class="column" :class="{'h-100': sameHeight}">
      <slot></slot>
      <div v-if="canResize" class="resize-handle resize-handle-right" @mousedown="(e) => startResize(e, 'right')"></div>
      <div v-if="canResize" class="resize-handle resize-handle-left" @mousedown="(e) => startResize(e, 'left')"></div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.column {
  position: relative;
}

.resize-handle {
  background-color: #DDD;
  bottom: 0;
  cursor: ew-resize;
  height: 100%;
  position: absolute;
  width: 5px;
}

.resize-handle-right {
  border-bottom-right-radius: 0.5em;
  border-top-right-radius: 0.5em;
  right: 0;
}

.resize-handle-left {
  border-bottom-left-radius: 0.5em;
  border-top-left-radius: 0.5em;
  left: 0;
}
</style>

<script>
export default {
  props: {
    id: String,
    size: {
      type: Number,
      default: 1,
    },
    offset: {
      type: Number,
      default: 0,
    },
    sameHeight: {
      type: Boolean,
      default: true,
    },
    canResize: {
      type: Boolean,
      default: false,
    },
    maxColumnCount: {
      type: Number,
      default: 12,
    },
  },
  emits: ['grow', 'shrink'],
  data() {
    return {
      isResizing: false,
      direction: null,
      gutterWidth: 30,
      layoutBreakpoint: 992,
    };
  },
  computed: {
    isRightResize() {
      return this.isResizing && this.direction === 'right';
    },
    isLeftResize() {
      return this.isResizing && this.direction === 'left';
    },
  },
  watch: {
    size() {
      this.applyLayout();
    },
    offset() {
      this.applyLayout();
    },
  },
  mounted() {
    this.applyLayout();
  },
  unmounted() {
    this.stopResize();
  },
  methods: {
    applyLayout() {
      // We need to apply the layout on the parent element to ensure each column class is a direct child of each
      // corresponding row class. This is due to the container div we need to use to make vuedraggable work.
      const parent = this.$refs.column.parentElement;

      if (parent.attributes['data-draggable']) {
        if (!this.size) {
          parent.className = 'd-none';
        } else {
          parent.className = `col-lg-${this.size} offset-lg-${this.offset}`;
        }
      }
    },
    startResize(e, direction) {
      if (window.innerWidth < this.layoutBreakpoint) {
        return;
      }

      this.isResizing = true;
      this.direction = direction;

      window.addEventListener('mousemove', this.resize);
      window.addEventListener('mouseup', this.stopResize);

      e.preventDefault();
    },
    resize(e) {
      const rowWidth = this.$parent.$el.getBoundingClientRect().width;
      const columnSize = rowWidth / this.maxColumnCount;

      const offset = this.$refs.column.getBoundingClientRect();

      let newWidth = 0;

      if (this.direction === 'right') {
        newWidth = e.clientX - offset.left;
      } else if (this.direction === 'left') {
        newWidth = offset.right - e.clientX;
      }

      const requiredColumns = Math.round((newWidth + this.gutterWidth) / columnSize);

      if (requiredColumns > this.size) {
        this.$emit('grow', this.direction);
      } else if (requiredColumns < this.size) {
        this.$emit('shrink', this.direction);
      }
    },
    stopResize() {
      this.isResizing = false;

      window.removeEventListener('mousemove', this.resize);
      window.removeEventListener('mouseup', this.stopResize);
    },
  },
};
</script>
