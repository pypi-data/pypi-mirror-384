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
  <div class="card">
    <div class="card-body filter-container">
      <div v-if="showRecordsFilter" class="form-check my-2">
        <input :id="`records-${suffix}`" v-model="filter.records" type="checkbox" class="form-check-input">
        <label class="form-check-label" :for="`records-${suffix}`">{{ $t('Exclude records') }}</label>
      </div>
      <div v-if="showExportFilter" class="my-2">
        <div class="mb-2">{{ $t('Include export data') }}</div>
        <div class="card bg-light">
          <div class="card-body">
            <div v-for="exportMeta in [['json', 'JSON'], ['rdf', 'RDF (Turtle)'], ['pdf', 'PDF']]"
                 :key="exportMeta[0]"
                 class="form-check">
              <input :id="`export-type-${exportMeta[0]}-${suffix}`"
                     v-model="filter.crateExportData[exportMeta[0]]"
                     type="checkbox"
                     class="form-check-input">
              <label class="form-check-label" :for="`export-type-${exportMeta[0]}-${suffix}`">
                {{ exportMeta[1] }}
              </label>
            </div>
          </div>
        </div>
      </div>
      <div v-if="showUserFilter" class="form-check my-2">
        <input :id="`user-${suffix}`" v-model="filter.user" type="checkbox" class="form-check-input">
        <label class="form-check-label" :for="`user-${suffix}`">{{ $t('Exclude user information') }}</label>
      </div>
      <div v-if="showLinksFilter" class="my-2">
        <label class="form-control-label" :for="`links-${suffix}`">{{ $t('Exclude record links') }}</label>
        <select :id="`links-${suffix}`" v-model="filter.links" class="custom-select custom-select-sm">
          <option value=""></option>
          <option value="out">{{ $t('Outgoing') }}</option>
          <option value="in">{{ $t('Incoming') }}</option>
          <option value="both">{{ $t('Both') }}</option>
        </select>
      </div>
      <div v-if="showExtrasFormatFilter" class="my-2">
        <label class="form-control-label" :for="`format-${suffix}`">{{ $t('Extra metadata format') }}</label>
        <select :id="`format-${suffix}`" v-model="filter.extrasFormat" class="custom-select custom-select-sm">
          <option value="standard">{{ $t('Standard') }}</option>
          <option value="plain">{{ $t('Plain') }}</option>
        </select>
      </div>
      <div v-if="showExtrasFilter" class="my-2">
        <div class="row mb-2">
          <div class="col-md-6 mb-2 mb-md-0">{{ $t('Exclude extra metadata') }}</div>
          <div v-if="showExtrasPropagationFilter" class="col-md-6 d-md-flex justify-content-end">
            <div class="form-check">
              <input :id="`propagate-${suffix}`" v-model="filter.propagate" type="checkbox" class="form-check-input">
              <label class="form-check-label" :for="`propagate-${suffix}`">{{ $t('Apply to linked records') }}</label>
            </div>
          </div>
        </div>
        <div class="card bg-light">
          <div class="card-body">
            <extras-selector :extras="extras"
                             :initial-selection="initialFilter.extras || {}"
                             @select="filter.extras = $event">
            </extras-selector>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-container {
  padding-bottom: 0.75rem;
  padding-top: 0.75rem;
}
</style>

<script>
export default {
  props: {
    resourceType: String,
    exportType: {
      type: String,
      default: null,
    },
    initialFilter: {
      type: Object,
      default: () => ({}),
    },
    extras: {
      type: Array,
      default: () => [],
    },
    allowExtrasPropagation: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['filter'],
  data() {
    return {
      suffix: kadi.utils.randomAlnum(),
      filter: {
        user: false,
        records: false,
        links: '',
        extrasFormat: 'standard',
        extras: {},
        propagate: false,
        crateExportData: {
          json: true,
          rdf: true,
          pdf: false,
        },
      },
    };
  },
  computed: {
    showRecordsFilter() {
      return this.resourceType === 'collection';
    },
    showExportFilter() {
      return this.exportType === 'ro-crate' && !this.filter.records;
    },
    showUserFilter() {
      return ['record', 'collection', 'template'].includes(this.resourceType) && this.exportType !== 'json-schema';
    },
    showLinksFilter() {
      return ['record', 'collection'].includes(this.resourceType) && !this.filter.records;
    },
    showExtrasFormatFilter() {
      return this.resourceType === 'extras' && this.exportType === 'json';
    },
    showExtrasFilter() {
      return ['record', 'extras', 'template'].includes(this.resourceType) && this.extras.length > 0;
    },
    showExtrasPropagationFilter() {
      return this.resourceType === 'record' && this.allowExtrasPropagation && this.filter.links !== 'both';
    },
  },
  watch: {
    filter: {
      handler() {
        this.updateFilter();
      },
      deep: true,
    },
  },
  mounted() {
    if ('user' in this.initialFilter) {
      this.filter.user = this.initialFilter.user;
    }

    this.filter.records = Boolean(this.initialFilter.records);

    if (this.initialFilter.links === true) {
      this.filter.links = 'both';
    } else {
      this.filter.links = this.initialFilter.links || this.filter.links;
    }

    this.filter.extrasFormat = this.initialFilter.format || this.filter.extrasFormat;
    this.filter.propagate = Boolean(this.initialFilter.propagate_extras);

    if (this.initialFilter.export_data) {
      for (const exportType of Object.keys(this.filter.crateExportData)) {
        this.filter.crateExportData[exportType] = this.initialFilter.export_data.includes(exportType);
      }
    }

    this.updateFilter();
  },
  methods: {
    updateFilter() {
      const filter = {};

      // Always include this flag explicitely, so we can rely on it when populating the initial filter, independent of
      // the default user value.
      filter.user = this.filter.user;

      if (this.filter.records !== false) {
        filter.records = this.filter.records;
      }
      if (this.filter.links !== '') {
        filter.links = this.filter.links === 'both' ? true : this.filter.links;
      }
      if (this.filter.extrasFormat !== 'standard') {
        filter.format = this.filter.extrasFormat;
      }
      if (Object.keys(this.filter.extras).length > 0) {
        filter.extras = this.filter.extras;
      }
      if (this.filter.propagate) {
        filter.propagate_extras = true;
      }

      if (this.exportType === 'ro-crate') {
        const exportData = [];

        for (const [key, value] of Object.entries(this.filter.crateExportData)) {
          if (value) {
            exportData.push(key);
          }
        }

        filter.export_data = exportData;
      }

      this.$emit('filter', filter);
    },
  },
};
</script>
