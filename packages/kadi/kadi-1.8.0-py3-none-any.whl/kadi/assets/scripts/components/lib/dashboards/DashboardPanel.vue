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

<template>
  <div>
    <div class="d-flex justify-content-between align-items-start">
      <div v-if="editMode" class="sort-handle btn btn-link text-primary pl-0 py-0">
        <i class="fa-solid fa-bars"></i>
      </div>

      <div class="flex-grow-1">
        <div v-if="panel">
          <div class="h5 mb-0 font-weight-bold">{{ panel.title }}</div>
          <div v-if="panel.subtitle" class="text-muted">{{ panel.subtitle }}</div>
        </div>
      </div>

      <div v-if="editMode" class="d-flex align-items-start ml-4">
        <div>
          <button type="button" class="btn btn-link text-primary px-1 py-0" @click="$emit('open-settings')">
            <i class="fa-solid fa-gear"></i>
          </button>
          <button type="button" class="btn btn-link text-primary px-1 py-0" @click="$emit('remove-panel')">
            <i class="fa-solid fa-xmark fa-lg"></i>
          </button>
        </div>
      </div>
    </div>

    <hr class="my-2">

    <div v-if="panel && panel.type" class="w-100 h-100 overflow-hidden">
      <component :is="availablePanels[panel.type].component"
                 :key="panel.id"
                 :endpoints="endpoints"
                 :settings="panel.settings">
      </component>
    </div>
  </div>
</template>

<script>
import DashboardMarkdown from 'scripts/components/lib/dashboards/panels/DashboardMarkdown.vue';
import DashboardPlotly from 'scripts/components/lib/dashboards/panels/DashboardPlotly.vue';
import DashboardRecordView from 'scripts/components/lib/dashboards/panels/DashboardRecordView.vue';

export default {
  components: {
    DashboardMarkdown,
    DashboardPlotly,
    DashboardRecordView,
  },
  props: {
    endpoints: Object,
    editMode: Boolean,
    panel: Object,
    availablePanels: Object,
  },
  emits: ['open-settings', 'remove-panel'],
  data() {
    return {
    };
  },
};
</script>
