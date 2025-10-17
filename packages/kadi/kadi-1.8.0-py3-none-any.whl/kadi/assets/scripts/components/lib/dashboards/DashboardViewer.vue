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
  <div ref="dashboardViewerRoot" class="fullscreen-bg">
    <confirm-dialog ref="dialog"></confirm-dialog>

    <dashboard-panel-settings ref="panelSettings"
                              :panel="editedPanel"
                              :endpoints="endpoints"
                              :available-panels="availablePanels"
                              @panel-updated="onPanelUpdated">
    </dashboard-panel-settings>

    <div v-if="!inEditMode" class="row">
      <div class="col-lg-8 mb-2 mb-lg-0">
        <button type="button" class="btn btn-sm btn-primary" :disabled="!isEditable" @click="newDashboard">
          <i class="fa-solid fa-plus"></i> {{ $t('New') }}
        </button>
        <button v-if="dashboard"
                type="button"
                class="btn btn-sm btn-light"
                :disabled="!isEditable"
                @click="enterEditMode">
          <i class="fa-solid fa-pencil"></i> {{ $t('Edit') }}
        </button>
        <button v-if="dashboard"
                type="button"
                class="btn btn-sm btn-danger"
                :disabled="!isEditable"
                @click="deleteDashboard">
          <i class="fa-solid fa-trash"></i> {{ $t('Delete') }}
        </button>
        <button v-if="dashboard"
                type="button"
                class="btn btn-sm btn-light"
                :disabled="!isEditable"
                @click="toggleFullscreen">
          <i class="fa-solid fa-expand"></i>
          {{ $t('Toggle fullscreen') }}
        </button>
      </div>

      <div class="col-lg-4 d-flex align-items-center">
        <dynamic-selection container-classes="select2-single-sm"
                           :dropdown-parent="'.fullscreen-bg'"
                           :placeholder="$t('Select a dashboard')"
                           :endpoint="selectEndpoint"
                           :initial-values="dashboardFiles"
                           :reset-on-select="false"
                           @select="selectDashboard"
                           @unselect="resetDashboard">
        </dynamic-selection>
      </div>
    </div>

    <div v-if="inEditMode && dashboard" class="row">
      <div class="col-md-10 mb-2 mb-md-0">
        <button type="button" class="btn btn-sm btn-primary" :disabled="!unsavedChanges_" @click="saveDashboard">
          <i class="fa-solid fa-floppy-disk"></i> {{ $t('Save') }}
        </button>
        <button type="button" class="btn btn-sm btn-primary" @click="dashboard.layout.addRow()">
          <i class="fa-solid fa-plus"></i> {{ $t('Add Row') }}
        </button>
        <button type="button" class="btn btn-sm btn-light" @click="cancelEditMode">
          <i class="fa-solid fa-ban"></i> {{ $t('Cancel') }}
        </button>
        <div class="input-group input-group-sm d-sm-inline-flex w-auto mt-2 mt-sm-0">
          <div class="input-group-prepend">
            <span class="input-group-text">{{ $t('Name') }}</span>
          </div>
          <input v-model="dashboard.name" class="form-control">
        </div>
      </div>
    </div>

    <hr v-if="dashboard && dashboard.layout.rows.length > 0">

    <grid v-if="dashboard" :id="dashboard.layout.id" :rows="dashboard.layout.rows" :disabled="!inEditMode">
      <template #default="{row, index: rowIndex}">
        <grid-row :id="row.id"
                  :columns="row.columns"
                  :disabled="!inEditMode"
                  :class="{'mb-4': rowIndex < dashboard.layout.rows.length - 1}"
                  @remove-row="removeRow(row)">

          <template #default="{column, index: columnIndex}">
            <grid-column :id="column.id"
                         :size="inEditMode ? column.size : column.isPlaceholder ? 0 : column.size"
                         :offset="inEditMode ? 0 : column.offset"
                         :same-height="false"
                         :can-resize="!column.isPlaceholder && inEditMode"
                         :max-column-count="row.maxColumnCount"
                         @grow="(dir) => row.growColumn(column, dir)"
                         @shrink="(dir) => row.shrinkColumn(column, dir)">

              <dashboard-panel v-if="!column.isPlaceholder"
                               class="column column-panel h-100"
                               :endpoints="endpoints"
                               :edit-mode="inEditMode"
                               :available-panels="availablePanels"
                               :panel="dashboard.getPanelByColumnId(column.id)"
                               @remove-panel="() => removePanel(row, column)"
                               @open-settings="() => openSettings(column)"/>
              <div v-else>
                <button v-if="inEditMode && row.canInsertColumnAt(columnIndex)"
                        class="column w-100 h-100 bg-transparent d-flex justify-content-center align-items-center"
                        :class="{'column-placeholder': inEditMode}"
                        @click="() => addPanel(row.insertColumnAt(columnIndex))">
                  <i class="fa-solid fa-plus"></i>
                </button>
                <div v-else class="column h-100" :class="{'column-placeholder': inEditMode}"></div>
              </div>
            </grid-column>
          </template>

        </grid-row>
      </template>
    </grid>
  </div>
</template>

<style lang="scss" scoped>
.column {
  min-height: 10em;
  padding: 0.75em;
}

.column-panel {
  border: 1px solid lightgray;
  border-radius: 0.5em;
}

.column-placeholder {
  border: 1px dashed lightgray;
  border-radius: 0.5em;
  max-height: 10em;
}
.fullscreen-bg:fullscreen {
  background: #fff;
  border-radius: 0.5em;
  min-height: 100vh;
  padding: 2rem;
  box-sizing: border-box;
}
</style>

<script>
import {Upload, UploadProvider} from 'scripts/lib/uploads.js';
import Dashboard from 'scripts/lib/dashboard.js';

import DashboardPanel from 'scripts/components/lib/dashboards/DashboardPanel.vue';
import DashboardPanelSettings from 'scripts/components/lib/dashboards/DashboardPanelSettings.vue';
import Grid from 'scripts/components/lib/grid/Grid.vue';
import GridColumn from 'scripts/components/lib/grid/GridColumn.vue';
import GridRow from 'scripts/components/lib/grid/GridRow.vue';

const DASHBOARD_FILE_KEY = 'dashboardFile';

export default {
  components: {
    DashboardPanel,
    DashboardPanelSettings,
    Grid,
    GridColumn,
    GridRow,
  },
  props: {
    selectEndpoint: String,
    selectFileEndpoint: String,
    selectJsonEndpoint: String,
    selectImageEndpoint: String,
    selectTemplateEndpoint: String,
    selectSearchEndpoint: String,
    loadSearchEndpoint: String,
    newRecordEndpoint: String,
    recordsEndpoint: String,
    uploadEndpoint: {
      type: String,
      default: null,
    },
    unsavedChanges: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['unsaved-changes'],
  data() {
    return {
      dashboard: null,
      editableDashboard: null,
      editedPanel: null,
      inEditMode: false,
      uploadProvider: null,
      dashboardFile: null,
      unsavedChanges_: false,
      dashboardFiles: [],
      availablePanels: {
        markdown: {
          title: 'Markdown',
          settings: {
            text: '',
          },
          component: 'DashboardMarkdown',
          settingsComponent: 'DashboardMarkdownSettings',
        },
        recordView: {
          title: 'Record View',
          settings: {
            template: null,
            queryString: '',
          },
          component: 'DashboardRecordView',
          settingsComponent: 'DashboardRecordViewSettings',
        },
        plotly: {
          title: 'Plotly',
          settings: {
            files: [],
          },
          component: 'DashboardPlotly',
          settingsComponent: 'DashboardPlotlySettings',
        },
      },
    };
  },
  computed: {
    isEditable() {
      return this.uploadProvider !== null;
    },
    endpoints() {
      return {
        selectFile: this.selectFileEndpoint,
        selectJson: this.selectJsonEndpoint,
        selectImage: this.selectImageEndpoint,
        selectTemplate: this.selectTemplateEndpoint,
        selectSearch: this.selectSearchEndpoint,
        loadSearch: this.loadSearchEndpoint,
        newRecord: this.newRecordEndpoint,
        records: this.recordsEndpoint,
      };
    },
  },
  watch: {
    uploadEndpoint() {
      this.initUploadProvider();
    },
    unsavedChanges() {
      this.unsavedChanges_ = this.unsavedChanges;
    },
    unsavedChanges_() {
      this.$emit('unsaved-changes', this.unsavedChanges_);
    },
    dashboard: {
      handler() {
        this.unsavedChanges_ = this.inEditMode;
      },
      deep: true,
    },
  },
  created() {
    const lastDashboardFile = localStorage.getItem(DASHBOARD_FILE_KEY);
    if (lastDashboardFile) {
      const json = JSON.parse(lastDashboardFile);
      this.dashboardFiles = [[json.id, json.text]];
    }
  },
  mounted() {
    this.initUploadProvider();
    this.loadLastUsedDashboard();
    window.addEventListener('beforeunload', this.beforeUnload);
  },
  unmounted() {
    window.removeEventListener('beforeunload', this.beforeUnload);
  },
  methods: {
    initUploadProvider() {
      if (!this.uploadEndpoint) {
        return;
      }

      this.uploadProvider = new UploadProvider(this.uploadEndpoint, this.onUploadReplace, this.onUploadSuccess);
    },
    async enterEditMode() {
      this.inEditMode = true;

      this.editableDashboard = Dashboard.from(this.dashboard);

      // Switch references so that we see the copy of the original dashboard.
      [this.dashboard, this.editableDashboard] = [this.editableDashboard, this.dashboard];

      await this.$nextTick();

      this.unsavedChanges_ = false;
    },
    cancelEditMode() {
      // Switch back to the original (unchanged) dashboard.
      [this.dashboard, this.editableDashboard] = [this.editableDashboard, this.dashboard];

      this.leaveEditMode();
    },
    leaveEditMode() {
      this.inEditMode = false;
      this.editedPanel = null;
    },
    newDashboard() {
      this.dashboardFile = null;
      this.dashboardFiles = [];
      this.dashboard = new Dashboard(`dashboard_${kadi.utils.randomAlnum(10)}`);
      this.enterEditMode();
    },
    resetDashboard() {
      this.leaveEditMode();

      this.dashboard = null;
      this.editableDashboard = null;
      this.dashboardFile = null;
      localStorage.removeItem(DASHBOARD_FILE_KEY);
    },
    saveDashboard() {
      if (!this.isEditable || !this.dashboard.name) {
        kadi.base.flashDanger($t('Error saving dashboard.'));
        return;
      }

      const file = new File([JSON.stringify(this.dashboard.toJSON())], `${this.dashboard.name}.json`);
      const upload = new Upload(file.name, file.size, file);

      this.uploadProvider.upload(upload);
    },
    async loadDashboard(endpoint) {
      const errorMsg = $t('Error loading dashboard.');

      try {
        const response = await axios.get(endpoint);

        this.editableDashboard = null;
        this.dashboard = Dashboard.from(response.data);

        if (this.dashboard) {
          this.dashboard.layout.restore();
        } else {
          kadi.base.flashDanger(errorMsg);
        }
      } catch (error) {
        kadi.base.flashDanger(errorMsg, error.request);
      }
    },
    async deleteDashboard() {
      if (!this.dashboardFile) {
        return;
      }

      const input = await this.$refs.dialog.open($t('Are you sure you want to delete this dashboard?'));

      if (!input.status) {
        return;
      }

      try {
        await axios.delete(this.dashboardFile.deleteEndpoint);

        kadi.base.flashSuccess($t('Dashboard deleted successfully.'));

        this.resetDashboard();
        this.selectDashboard(null);
        localStorage.removeItem(DASHBOARD_FILE_KEY);
        this.dashboardFiles = [];
      } catch (error) {
        kadi.base.flashDanger($t('Error deleting dashboard.'), error.request);
      }
    },
    selectDashboard(file) {
      if (file) {
        this.dashboardFile = {
          downloadEndpoint: file.download_endpoint,
          deleteEndpoint: file.delete_endpoint,
        };
        localStorage.setItem(DASHBOARD_FILE_KEY, JSON.stringify(file));
        this.loadDashboard(this.dashboardFile.downloadEndpoint);
      } else {
        this.dashboardFile = null;
      }
    },
    async removeRow(row) {
      const input = await this.$refs.dialog.open($t('Are you sure you want to remove this row?'));

      if (input.status) {
        this.dashboard.layout.removeRow(row);
      }
    },
    addPanel(column) {
      const panel = this.dashboard.createPanel(null);

      this.dashboard.panels[panel.id] = panel;
      this.dashboard.layoutAssignments[column.id] = panel.id;

      return panel;
    },
    async removePanel(row, column) {
      const input = await this.$refs.dialog.open($t('Are you sure you want to remove this panel?'));

      if (input.status) {
        const panel = this.dashboard.getPanelByColumnId(column.id);

        if (panel) {
          this.dashboard.removePanel(panel, column.id);
        }

        row.removeColumn(column);
      }
    },
    openSettings(column) {
      let panel = this.dashboard.getPanelByColumnId(column.id);

      if (!panel) {
        panel = this.addPanel(column);
      }

      this.editedPanel = panel;
      this.$refs.panelSettings.show();
    },
    onPanelUpdated(editedPanel) {
      this.dashboard.panels[editedPanel.id] = kadi.utils.deepClone(editedPanel);
    },
    async onUploadReplace(upload) {
      const msg = $t(
        'A file with the name "{{filename}}" already exists in the current record. Do you want to replace it?',
        {filename: upload.name},
      );

      const input = await this.$refs.dialog.open(msg);
      return input.status;
    },
    onUploadSuccess(upload, file) {
      this.dashboardFile = {
        downloadEndpoint: file._links.download,
        deleteEndpoint: file._actions.delete,
      };

      this.unsavedChanges_ = false;
      this.leaveEditMode();

      kadi.base.flashSuccess($t('Dashboard saved successfully.'));
    },
    beforeUnload(e) {
      if (this.unsavedChanges_) {
        e.preventDefault();
        return '';
      }
      return null;
    },
    toggleFullscreen(event) {
      kadi.utils.toggleFullscreen(this.$refs.dashboardViewerRoot);
      event.currentTarget.blur();
    },
    loadLastUsedDashboard() {
      const lastDashboardFile = localStorage.getItem(DASHBOARD_FILE_KEY);
      if (lastDashboardFile) {
        this.selectDashboard(JSON.parse(lastDashboardFile));
      }
    },
  },
};
</script>
