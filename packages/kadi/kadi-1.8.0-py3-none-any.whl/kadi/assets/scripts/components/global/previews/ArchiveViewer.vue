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
  <div :class="{'card bg-light max-vh-75 overflow-auto': depth === 0}">
    <div :class="{'mt-3 mr-4': depth === 0}">
      <ul :style="listWidth">
        <li v-for="entry in entries_" :key="entry.id">
          <div v-if="!entry.is_dir" class="entry d-flex justify-content-between px-1">
            <div class="text-break">
              <i class="fa-solid fa-file"></i> {{ entry.name }}
            </div>
            <small class="size text-right">{{ kadi.utils.filesize(entry.size) }}</small>
          </div>
          <div v-if="entry.is_dir">
            <collapse-item :id="entry.id"
                           class="px-1"
                           show-icon-class="fa-solid fa-folder"
                           hide-icon-class="fa-solid fa-folder-open">
              <strong>{{ entry.name }}</strong>
            </collapse-item>
            <archive-viewer :id="entry.id" :entries="entry.children" :depth="depth + 1"></archive-viewer>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.entry:hover {
  background-color: #dee6ed;
  border-radius: 0.25rem;
}

.size {
  min-width: 100px;
}
</style>

<script>
export default {
  props: {
    entries: Array,
    depth: {
      type: Number,
      default: 0,
    },
  },
  data() {
    return {
      entries_: [],
    };
  },
  computed: {
    listWidth() {
      return `min-width: ${Math.max(600 - (50 * this.depth), 300)}px`;
    },
  },
  mounted() {
    this.entries.forEach((entry) => {
      entry.id = kadi.utils.randomAlnum();
      this.entries_.push(entry);
    });
  },
};
</script>
