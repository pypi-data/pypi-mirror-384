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
import {onMounted, ref, useTemplateRef} from 'vue';

const props = defineProps({
  message: String,
  type: {
    type: String,
    default: 'info',
  },
});

const icon = ref(null);

const alertRef = useTemplateRef('alert-ref');

onMounted(() => {
  if (props.type === 'info') {
    icon.value = 'circle-info';
  } else if (props.type === 'danger') {
    icon.value = 'circle-xmark';
  } else if (props.type === 'warning') {
    icon.value = 'triangle-exclamation';
  } else if (props.type === 'success') {
    icon.value = 'circle-check';
  }

  const timeout = Math.min(Math.max(props.message.length * 75, 2500), 7000);
  window.setTimeout(() => $(alertRef.value).alert('close'), timeout);
});
</script>

<template>
  <div ref="alert-ref" class="alert fade show" :class="`alert-${type}`">
    <i v-if="icon" class="fa" :class="`fa-${icon}`"></i> {{ message }}
  </div>
</template>
