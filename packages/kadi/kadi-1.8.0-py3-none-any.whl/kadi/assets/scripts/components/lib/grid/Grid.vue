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
  <vue-draggable item-key="id"
                 handle=".sort-handle"
                 :list="rows"
                 :group="id"
                 :disabled="disabled"
                 :force-fallback="true">
    <template #item="{element: row, index}">
      <div>
        <!-- The container div is a necessary workaround as vuedraggable can't deal with the dynamic slot content. -->
        <slot :row="row" :index="index"></slot>
      </div>
    </template>
  </vue-draggable>
</template>

<script>
import VueDraggable from 'vuedraggable';

export default {
  components: {
    VueDraggable,
  },
  props: {
    id: String,
    rows: Array,
    disabled: {
      type: Boolean,
      default: false,
    },
  },
};
</script>
