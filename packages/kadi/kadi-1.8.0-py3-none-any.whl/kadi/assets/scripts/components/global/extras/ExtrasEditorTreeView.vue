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

<script setup>
defineProps({
  extras: Array,
});

const emit = defineEmits(['focus-extra']);

function focusExtra(extra, event = null) {
  // Do not focus the extra when clicking on the collapse toggle.
  if (event === null || !event.target.classList.contains('collapse-toggle')) {
    emit('focus-extra', extra);
  }
}
</script>

<template>
  <div>
    <div v-for="(extra, index) in extras" :key="extra.id">
      <div class="row my-1 my-md-0 align-items-center cursor-pointer extra" @click="focusExtra(extra, $event)">
        <div class="col-md-9">
          <div class="d-flex align-items-center">
            <collapse-item v-if="kadi.utils.isNestedType(extra.type.value)"
                           :id="extra.id"
                           class="mr-2"
                           show-icon-class="fa-regular fa-square-plus collapse-toggle"
                           hide-icon-class="fa-regular fa-square-minus collapse-toggle">
              <span></span>
            </collapse-item>
            <span class="py-1" :class="{'font-weight-bold': kadi.utils.isNestedType(extra.type.value)}">
              {{ extra.key.value || `(${index + 1})` }}
            </span>
          </div>
        </div>
        <div class="col-md-3 d-md-flex justify-content-end">
          <small class="text-muted">{{ kadi.utils.capitalize(kadi.utils.prettyTypeName(extra.type.value)) }}</small>
        </div>
      </div>
      <div v-if="kadi.utils.isNestedType(extra.type.value)" :id="extra.id" class="border-dotted pl-4 ml-1">
        <extras-editor-tree-view :extras="extra.value.value" @focus-extra="focusExtra"></extras-editor-tree-view>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.border-dotted {
  border-left: 1px dotted #2c3e50;
}

.extra {
  border-radius: 0.25rem;
  min-width: 150px;

  &:hover {
    background-color: #dee6ed;
  }
}
</style>
