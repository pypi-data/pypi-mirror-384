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
import {useDashboardSettings} from 'scripts/components/composables/dashboard-settings.js';

const props = defineProps({
  id: String,
  settings: Object,
  endpoints: Object,
});

const emit = defineEmits(['settings-updated']);

const {currentSettings} = useDashboardSettings(props, (settings) => {
  emit('settings-updated', settings);
});

function onInput(input) {
  currentSettings.value.text = input;
}
</script>

<template>
  <markdown-editor :id="`markdown-editor-${id}`"
                   :rows="16"
                   :initial-value="currentSettings.text"
                   :link-endpoint="endpoints.selectFile"
                   :image-endpoint="endpoints.selectImage"
                   @input="onInput">
  </markdown-editor>
</template>
