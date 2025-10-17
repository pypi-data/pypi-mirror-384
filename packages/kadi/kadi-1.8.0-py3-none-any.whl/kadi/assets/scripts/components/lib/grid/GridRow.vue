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
  <div>
    <div v-if="!disabled" class="d-flex justify-content-between mb-1">
      <span class="sort-handle btn btn-link text-primary px-1 py-0">
        <i class="fa-solid fa-bars"></i>
      </span>
      <button type="button" class="btn btn-link text-primary px-1 py-0" @click="$emit('remove-row')">
        <i class="fa-solid fa-xmark fa-lg"></i>
      </button>
    </div>
    <vue-draggable item-key="id"
                   handle=".sort-handle"
                   :list="columns"
                   :group="id"
                   :disabled="disabled"
                   :force-fallback="true"
                   :component-data="{'class': 'row'}">
      <template #item="{element: column, index}">
        <div>
          <!-- The container div is a necessary workaround as vuedraggable can't deal with the dynamic slot content. -->
          <slot :column="column" :index="index"></slot>
        </div>
      </template>
    </vue-draggable>
  </div>
</template>

<script>
import VueDraggable from 'vuedraggable';

export default {
  components: {
    VueDraggable,
  },
  props: {
    id: String,
    columns: {
      type: Array,
      default: () => [],
    },
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['remove-row'],
};
</script>
