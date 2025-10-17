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
import {onMounted, ref, watch} from 'vue';

const props = defineProps({
  timestamp: String,
  refreshInterval: {
    type: Number,
    default: 60_000,
  },
});

const fromNow = ref('');
const title = ref('');

function updateTimestamp() {
  const date = dayjs(props.timestamp);
  fromNow.value = date.fromNow();
  title.value = date.format('LL LTS');
}

watch(() => props.timestamp, updateTimestamp);

onMounted(() => {
  updateTimestamp();
  setInterval(updateTimestamp, props.refreshInterval);
});
</script>

<template>
  <span class="elevated" :title="title">{{ fromNow }}</span>
</template>
