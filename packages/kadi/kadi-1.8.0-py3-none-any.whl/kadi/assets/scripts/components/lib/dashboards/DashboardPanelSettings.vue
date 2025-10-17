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
  <modal-dialog ref="dialog" :title="$t('Edit dashboard panel')">
    <template #body>
      <div v-if="panel_">
        <div>
          <label>{{ $t('Title') }}</label>
          <input v-model="panel_.title" class="form-control">
        </div>
        <div class="mt-3">
          <label>{{ $t('Subtitle') }}</label>
          <input v-model="panel_.subtitle" class="form-control">
        </div>

        <div class="mt-3">
          <label>{{ $t('Type') }}</label>
          <select v-model="panel_.type" class="custom-select" @change="changeType">
            <option v-for="(value, key) in availablePanels" :key="key" :value="key">{{ value.title }}</option>
          </select>
        </div>

        <div v-if="component">
          <hr>
          <component :is="component"
                     :id="panel_.id"
                     :key="panel_.id"
                     :settings="panel_.settings"
                     :endpoints="endpoints"
                     @settings-updated="onSettingsUpdated">
          </component>
        </div>
      </div>
    </template>
    <template #footer>
      <button type="button" class="btn btn-sm btn-primary" data-dismiss="modal" @click="$emit('panel-updated', panel_)">
        {{ $t('Apply') }}
      </button>
    </template>
  </modal-dialog>
</template>

<script>
import DashboardMarkdownSettings from 'panels/DashboardMarkdownSettings.vue';
import DashboardPlotlySettings from 'panels/DashboardPlotlySettings.vue';
import DashboardRecordViewSettings from 'panels/DashboardRecordViewSettings.vue';

export default {
  components: {
    DashboardMarkdownSettings,
    DashboardRecordViewSettings,
    DashboardPlotlySettings,
  },
  props: {
    panel: Object,
    endpoints: Object,
    availablePanels: Object,
  },
  emits: ['panel-updated'],
  data() {
    return {
      panel_: {},
    };
  },
  computed: {
    component() {
      return (this.panel_ && this.panel_.type)
        ? this.availablePanels[this.panel_.type].settingsComponent
        : null;
    },
  },
  watch: {
    panel() {
      this.panel_ = kadi.utils.deepClone(this.panel);
    },
  },
  methods: {
    show() {
      this.$refs.dialog.open();
    },
    changeType() {
      this.panel_.settings = this.availablePanels[this.panel_.type].settings;
    },
    onSettingsUpdated(newSettings) {
      this.panel_.settings = newSettings;
    },
  },
};
</script>
