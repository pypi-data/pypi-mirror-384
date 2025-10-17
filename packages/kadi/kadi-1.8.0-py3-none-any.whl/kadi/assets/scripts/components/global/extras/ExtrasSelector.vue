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
import {onBeforeMount, ref, watch} from 'vue';

const props = defineProps({
  extras: Array,
  initialSelection: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['select']);

const extras_ = ref(props.extras);

function getSelection(extras) {
  const filter = {};

  for (let i = 0; i < extras.length; i++) {
    const extra = extras[i];
    const filterKey = extra.key || i;

    if (kadi.utils.isNestedType(extra.type)) {
      const nestedFilter = getSelection(extra.value);

      if (Object.keys(nestedFilter).length > 0) {
        filter[filterKey] = nestedFilter;
      }
    }

    if (extra.checked) {
      filter[filterKey] = {};
    }
  }

  return filter;
}

function initializeExtras(extras) {
  extras.forEach((extra) => {
    extra.id = kadi.utils.randomAlnum();
    extra.checked = false;
    extra.disabled = false;
    extra.collapsed = true;

    if (kadi.utils.isNestedType(extra.type)) {
      initializeExtras(extra.value);
    }
  });
}

watch(
  extras_,
  () => {
    emit('select', getSelection(extras_.value));
  },
  {deep: true},
);

onBeforeMount(() => {
  initializeExtras(extras_.value);
});
</script>

<template>
  <extras-selector-items :extras="extras_" :initial-selection="initialSelection"></extras-selector-items>
</template>
