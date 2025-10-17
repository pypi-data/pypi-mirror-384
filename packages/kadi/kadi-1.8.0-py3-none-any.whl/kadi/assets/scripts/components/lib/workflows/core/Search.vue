<!-- Copyright 2021 Karlsruhe Institute of Technology
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
  <div class="search">
    <input ref="input"
           v-model.trim="filter"
           class="form-control form-control-sm"
           placeholder="Filter"
           @pointerdown.stop
           @wheel.stop>
  </div>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/menu.scss';

.search {
  @extend .item;

  border-bottom: 1px solid $context-menu-border-color;
  padding: 7px;

  &:hover {
    background-color: $context-menu-color;
    cursor: default;
  }
}
</style>

<script>
export default {
  emits: ['filter'],
  data() {
    return {
      filter: '',
    };
  },
  watch: {
    filter() {
      this.$emit('filter', this.filter);
    },
  },
  mounted() {
    this.$refs.input.focus();
  },
};
</script>
