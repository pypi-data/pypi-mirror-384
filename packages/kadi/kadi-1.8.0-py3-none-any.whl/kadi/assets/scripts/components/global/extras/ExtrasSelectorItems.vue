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

<script setup>
import {onMounted} from 'vue';

const props = defineProps({
  extras: Array,
  initialSelection: {
    type: Object,
    default: () => ({}),
  },
});

function checkExtras(extras, checked, disabled = false) {
  for (const extra of kadi.utils.asArray(extras)) {
    extra.checked = checked;

    if (disabled) {
      extra.disabled = extra.checked;
    }
    if (kadi.utils.isNestedType(extra.type)) {
      checkExtras(extra.value, checked, true);
    }
  }
}

function initializeSelection(extras, selection) {
  for (let i = 0; i < extras.length; i++) {
    const extra = extras[i];
    const key = extra.key || i;

    if (key in selection) {
      extra.collapsed = false;

      if (Object.keys(selection[key]).length > 0) {
        initializeSelection(extra.value, selection[key]);
      } else {
        checkExtras(extra, true);
      }
    }
  }
}

onMounted(() => {
  initializeSelection(props.extras, props.initialSelection);
});
</script>

<template>
  <div>
    <div v-for="(extra, index) in extras" :key="extra.id">
      <div class="row my-2 my-md-0">
        <div class="col-md-10">
          <div class="form-check">
            <input :id="`checkbox-${extra.id}`"
                   v-model="extra.checked"
                   type="checkbox"
                   class="form-check-input"
                   :disabled="extra.disabled"
                   @click="checkExtras(extra, $event.target.checked)">
            <label v-if="!kadi.utils.isNestedType(extra.type)"
                   class="form-check-label key"
                   :for="`checkbox-${extra.id}`">
              {{ extra.key || `(${index + 1})` }}
            </label>
            <collapse-item v-else :id="extra.id" show-icon-class="" hide-icon-class="" :is-collapsed="extra.collapsed">
              <strong class="key" :class="{'text-muted': extra.disabled}">{{ extra.key || `(${index + 1})` }}</strong>
            </collapse-item>
          </div>
        </div>
        <div class="col-md-2 d-md-flex justify-content-end">
          <small class="text-muted">{{ kadi.utils.capitalize(kadi.utils.prettyTypeName(extra.type)) }}</small>
        </div>
      </div>
      <div v-if="kadi.utils.isNestedType(extra.type)" :id="extra.id">
        <extras-selector-items class="border-dotted pl-5 ml-2" :extras="extra.value"></extras-selector-items>
      </div>
    </div>
  </div>
</template>

<style scoped>
.border-dotted {
  border-left: 1px dotted #2c3e50;
}

.key {
  word-break: break-all;
}
</style>
