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

<script setup>
import {ref} from 'vue';

import FlashMessage from 'scripts/components/lib/base/FlashMessage.vue';

const messages = ref([]);

function addMessage(type, message, request = null) {
  let _message = message;

  if (request !== null) {
    // Do nothing if the error originates from a canceled request.
    if (request.status === 0) {
      return;
    }

    _message = `${message} (${request.status})`;
  }

  messages.value.push({
    id: kadi.utils.randomAlnum(),
    message: _message,
    type,
  });
}

function flashDanger(message, request = null) {
  addMessage('danger', message, request);
}

function flashInfo(message, request = null) {
  addMessage('info', message, request);
}

function flashSuccess(message, request = null) {
  addMessage('success', message, request);
}

function flashWarning(message, request = null) {
  addMessage('warning', message, request);
}

defineExpose({
  flashDanger,
  flashInfo,
  flashSuccess,
  flashWarning,
});
</script>

<template>
  <div>
    <div v-for="message in messages" :key="message.id">
      <flash-message :message="message.message" :type="message.type"></flash-message>
    </div>
  </div>
</template>
