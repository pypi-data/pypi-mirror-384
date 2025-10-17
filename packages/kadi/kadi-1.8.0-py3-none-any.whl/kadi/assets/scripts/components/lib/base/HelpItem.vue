<!-- Copyright 2023 Karlsruhe Institute of Technology
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

defineProps({
  helpUrl: String,
  aboutUrl: String,
  newsUrl: String,
});

const showNotification = ref(false);

const storageKey = 'hide_version_notification';

function dismissNotification() {
  // Store the current version in the local storage when dismissing the notification.
  window.localStorage.setItem(storageKey, kadi.globals.version);
  showNotification.value = false;
}

onMounted(() => {
  // Check if the version changed since the last time the notification was dismissed. If it did, show the notification
  // again and delete the old version from the local storage, if applicable.
  if (window.localStorage.getItem(storageKey) !== kadi.globals.version) {
    window.localStorage.removeItem(storageKey);
    showNotification.value = true;
  }
});
</script>

<template>
  <div>
    <a class="nav-link" href="#" data-toggle="dropdown">
      <span class="navbar-icon">
        <i class="fa-regular fa-lg fa-circle-question"></i>
      </span>
      <span v-if="showNotification" id="notification-toggle" class="notification"></span>
    </a>
    <div class="dropdown-menu dropdown-menu-right navbar-mt">
      <a class="dropdown-item" :href="helpUrl">
        <i class="fa-regular fa-circle-question"></i> {{ $t('Help') }}
      </a>
      <a class="dropdown-item" :href="aboutUrl">
        <i class="fa-solid fa-circle-info"></i> {{ $t('About') }}
      </a>
      <a class="dropdown-item" target="_blank" rel="noopener noreferrer" :href="newsUrl" @click="dismissNotification">
        <i class="fa-solid fa-rocket"></i> {{ $t("What's new") }}
        <span v-if="showNotification" id="notification-item" class="notification"></span>
      </a>
    </div>
  </div>
</template>

<style scoped>
.notification {
  background-color: #009682;
  border-radius: 50%;
  display: inline-block;
}

#notification-item {
  height: 10px;
  margin-left: 30px;
  width: 10px;
}

#notification-toggle {
  border: 2px solid #2c3e50;
  height: 12px;
  position: absolute;
  right: 10px;
  top: 8px;
  width: 12px;
}
</style>
