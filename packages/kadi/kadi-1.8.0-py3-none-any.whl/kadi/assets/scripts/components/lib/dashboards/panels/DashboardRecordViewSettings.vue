<!-- Copyright 2024 Karlsruhe Institute of Technology
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

async function selectTemplate(template = null) {
  if (template === null) {
    currentSettings.value.template = null;
    return;
  }

  try {
    const response = await axios.get(template.endpoint);
    const data = response.data;

    currentSettings.value.template = {
      id: data.id,
      title: data.title,
      viewEndpoint: data._links.view,
    };
  } catch (error) {
    kadi.base.flashDanger($t('Error loading template.'), error.request);
  }
}

async function loadSearch(id) {
  const errorMsg = $t('Error loading saved search.');

  try {
    const response = await axios.get(`${props.endpoints.loadSearch}/${id}`);
    const data = response.data;

    if (data.object !== 'record') {
      kadi.base.flashDanger(errorMsg);
    } else {
      currentSettings.value.queryString = data.query_string;
    }
  } catch (error) {
    kadi.base.flashDanger(errorMsg, error.request);
  }
}
</script>

<template>
  <div>
    <div :id="`select-template-${id}`">
      <label>{{ $t('Record template') }}</label>

      <dynamic-selection container-classes="select2-single-sm"
                         :placeholder="$t('Select a record template')"
                         :endpoint="endpoints.selectTemplate"
                         :dropdown-parent="`#select-template-${id}`"
                         :reset-on-select="true"
                         @select="selectTemplate">
      </dynamic-selection>

      <div v-if="currentSettings.template" class="input-group input-group-sm mt-2">
        <input class="form-control" :value="currentSettings.template.title" disabled>

        <div class="input-group-append">
          <a class="btn btn-sm btn-light"
             target="_blank"
             rel="noopener noreferrer"
             :title="$t('View template')"
             :href="currentSettings.template.viewEndpoint">
            <i class="fa-solid fa-eye"></i>
          </a>
        </div>

        <div class="input-group-append">
          <button type="button"
                  class="input-group-text btn btn-sm btn-light"
                  :title="$t('Deselect template')"
                  @click="selectTemplate(null)">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
      </div>
    </div>

    <div :id="`select-search-${id}`" class="mt-3">
      <label>{{ $t('Record search') }}</label>

      <dynamic-selection container-classes="select2-single-sm"
                         :placeholder="$t('Select a saved search')"
                         :endpoint="endpoints.selectSearch"
                         :dropdown-parent="`#select-search-${id}`"
                         :reset-on-select="true"
                         @select="loadSearch($event.id)">
      </dynamic-selection>

      <input v-model="currentSettings.queryString"
             class="form-control form-control-sm mt-2"
             :placeholder="$t('Current search')">
    </div>
  </div>
</template>
