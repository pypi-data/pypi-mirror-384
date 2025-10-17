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
import {onMounted, ref} from 'vue';

const props = defineProps({
  message: String,
  hash: String,
});

const showBroadcastMsg = ref(false);

const storageKey = 'hide_broadcast_msg';

function dismissBroadcast() {
  // Store the hash of the broadcast message in the local storage when dismissing it.
  window.localStorage.setItem(storageKey, props.hash);
  showBroadcastMsg.value = false;
}

onMounted(() => {
  // If the broadcast message is not empty, check if it changed since the last time it was dismissed based on its hash.
  // If it did, show it and delete the old hash from the local storage, if applicable.
  if (props.message === '') {
    window.localStorage.removeItem(storageKey);
  } else if (window.localStorage.getItem(storageKey) !== props.hash) {
    window.localStorage.removeItem(storageKey);
    showBroadcastMsg.value = true;
  }
});
</script>

<template>
  <div v-if="showBroadcastMsg" class="card bg-info text-white">
    <div class="card-body">
      <button type="button" class="close ml-4" @click="dismissBroadcast">
        <i class="fa-solid fa-xmark fa-xs"></i>
      </button>
      <markdown-renderer :input="message"></markdown-renderer>
    </div>
  </div>
</template>
