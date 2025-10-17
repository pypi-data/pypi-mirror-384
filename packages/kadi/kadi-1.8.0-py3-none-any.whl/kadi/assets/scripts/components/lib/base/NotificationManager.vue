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
import {nextTick, onMounted, onUnmounted, ref, useTemplateRef} from 'vue';

import NotificationToast from 'scripts/components/lib/base/NotificationToast.vue';

const props = defineProps({
  endpoint: String,
});

const notifications = ref([]);

const containerRef = useTemplateRef('container-ref');

let originalTitle = null;
let lastNotificationDate = null;
let currentTimeout = null;
let pollTimeoutHandle = null;

const minTimeout = 5_000;
const maxTimeout = 30_000;

function disablePolling() {
  window.clearTimeout(pollTimeoutHandle);
  pollTimeoutHandle = null;
}

function pollNotifications() {
  // Clear any previous timeout.
  disablePolling();
  pollTimeoutHandle = window.setTimeout(pollNotifications, currentTimeout);

  // Make sure we don't retrieve notifications if the current timeout has not elapsed yet.
  if (lastNotificationDate === null || new Date() - lastNotificationDate >= currentTimeout) {
    // eslint-disable-next-line no-use-before-define
    getNotifications(false, false);
  }

  // Slowly increase the polling timeout up to the maximum.
  if (currentTimeout < maxTimeout) {
    currentTimeout += 1_000;
  }
}

async function getNotifications(scrollTo = false, resetTimeout = true) {
  if (resetTimeout) {
    currentTimeout = minTimeout;
  }

  lastNotificationDate = new Date();

  try {
    const response = await axios.get(props.endpoint);

    notifications.value = response.data;
    const numNotifications = notifications.value.length;

    if (numNotifications > 0) {
      document.title = `(${numNotifications}) ${originalTitle}`;

      if (scrollTo) {
        nextTick(() => kadi.utils.scrollIntoView(containerRef.value, 'bottom'));
      }

      // Start polling again if currently not the case.
      if (!pollTimeoutHandle) {
        pollNotifications();
      }
    } else {
      document.title = originalTitle;
      // If no notifications were retrieved, stop polling for the time being.
      disablePolling();
    }
  } catch {
    disablePolling();
  }
}

function onBlur() {
  // Stop polling if the window is not in focus.
  disablePolling();
}

function onFocus() {
  currentTimeout = minTimeout;
  // Start polling again if the window is back in focus.
  pollNotifications();
}

function onBeforeUnload() {
  disablePolling();
}

defineExpose({
  getNotifications,
});

onMounted(() => {
  originalTitle = document.title;
  currentTimeout = minTimeout;

  if (document.hasFocus()) {
    pollNotifications();
  }

  window.addEventListener('blur', onBlur);
  window.addEventListener('focus', onFocus);
  window.addEventListener('beforeunload', onBeforeUnload);
});

onUnmounted(() => {
  window.removeEventListener('blur', onBlur);
  window.removeEventListener('focus', onFocus);
  window.removeEventListener('beforeunload', onBeforeUnload);
});
</script>

<template>
  <div ref="container-ref">
    <div v-for="notification in notifications" :key="notification.id">
      <notification-toast class="mb-4"
                          :title="notification.data.title"
                          :body="notification.data.body"
                          :timestamp="notification.created_at"
                          :dismiss-endpoint="notification._actions.dismiss">
      </notification-toast>
    </div>
  </div>
</template>
