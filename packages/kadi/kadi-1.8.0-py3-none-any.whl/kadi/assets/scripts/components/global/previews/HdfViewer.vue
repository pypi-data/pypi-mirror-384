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
  <div :class="{'card bg-light max-vh-75 overflow-auto': depth === 0}">
    <div :class="{'mt-3 mr-4': depth === 0}">
      <ul :style="listWidth">
        <li v-for="entry in entries_" :key="entry.id">
          <div class="entry d-flex justify-content-between px-1">
            <div>
              <div v-if="!entry.is_group" class="text-break">
                <i class="fa-solid fa-file"></i> {{ entry.name }}
              </div>
              <collapse-item v-else
                             :id="entry.id"
                             show-icon-class="fa-solid fa-folder"
                             hide-icon-class="fa-solid fa-folder-open">
                <strong class="text-break">{{ entry.name }}</strong>
              </collapse-item>
            </div>
            <collapse-item v-if="hasDetails(entry)" :id="`${entry.id}-details`" :is-collapsed="true">
              {{ $t('Details') }}
            </collapse-item>
          </div>
          <div :id="`${entry.id}-details`">
            <div v-if="entry.meta" class="card card-body py-2 my-2">
              <strong>{{ $t('Object info') }}</strong>
              <hr class="my-1">
              <div v-for="attr in metaAttrs" :key="attr[1]" class="row mb-2 mb-md-0">
                <div class="col-md-4">{{ attr[1] }}</div>
                <div class="col-md-8">{{ entry.meta[attr[0]] }}</div>
              </div>
            </div>
            <div v-if="hasAttrs(entry)" class="card card-body py-2 my-2">
              <strong>{{ $t('Attributes') }}</strong>
              <hr class="my-1">
              <div v-for="(value, prop) in entry.attrs" :key="prop" class="row mb-2 mb-md-0">
                <div class="col-md-4">{{ prop }}</div>
                <div class="col-md-8">{{ value }}</div>
              </div>
            </div>
          </div>
          <div v-if="entry.is_group">
            <hdf-viewer :id="entry.id" :entries="entry.children" :depth="depth + 1"></hdf-viewer>
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
      metaAttrs: [
        ['dtype', $t('Data type')],
        ['ndim', $t('Number of dimensions')],
        ['shape', $t('Dimensions')],
        ['maxshape', $t('Maximum dimensions')],
        ['size', $t('Number of elements')],
        ['nbytes', 'Bytes'],
      ],
    };
  },
  computed: {
    listWidth() {
      return `min-width: ${Math.max(500 - (50 * this.depth), 300)}px`;
    },
  },
  mounted() {
    this.entries.forEach((entry) => {
      entry.id = kadi.utils.randomAlnum();
      this.entries_.push(entry);
    });
  },
  methods: {
    hasAttrs(entry) {
      return Object.keys(entry.attrs).length > 0;
    },
    hasDetails(entry) {
      return this.hasAttrs(entry) || entry.meta;
    },
  },
};
</script>
