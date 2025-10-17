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

<template>
  <div>
    <div class="row mb-4">
      <div v-if="isCustomizable" class="col-md-6 mb-2 mb-md-0">
        <div>
          <collapse-item :id="`collapse-${suffix}`"
                         :is-collapsed="true"
                         class="btn btn-sm btn-light"
                         @collapse="showUpdateButton = !$event">
            {{ $t('Customize') }}
          </collapse-item>
          <button v-if="showUpdateButton"
                  type="button"
                  class="btn btn-sm btn-light"
                  :disabled="loading"
                  @click="updatePreview">
            <i class="fa-solid fa-eye"></i>
            {{ $t('Update preview') }}
          </button>
        </div>
      </div>
      <div class="d-md-flex justify-content-end" :class="isCustomizable ? 'col-md-6' : 'col-md-12'">
        <a class="btn btn-sm btn-light" :href="downloadEndpoint">
          <i class="fa-solid fa-download"></i>
          {{ $t('Download') }}
        </a>
      </div>
    </div>
    <div v-if="isCustomizable" :id="`collapse-${suffix}`" class="mb-4">
      <resource-export-filter :resource-type="resourceType"
                              :export-type="exportType"
                              :extras="extras"
                              :allow-extras-propagation="allowExtrasPropagation"
                              @filter="filter = $event">
      </resource-export-filter>
    </div>
    <div v-if="!loading" ref="previewContainer">
      <div v-if="hasTextPreview">
        <div class="card bg-light">
          <clipboard-button class="btn-sm clipboard-btn"
                            :content="serializedExportData"
                            :style="clipboardBtnStyle">
          </clipboard-button>
          <div class="my-1 ml-2 mr-0">
            <pre ref="textContent" class="max-vh-75 mb-0">{{ exportData }}</pre>
          </div>
        </div>
      </div>
      <div v-else-if="exportType === 'pdf'">
        <iframe class="w-100 vh-75 border rounded" frameborder="0" allowfullscreen :src="exportData">
        </iframe>
      </div>
      <div v-else-if="exportType === 'qr'">
        <div class="border bg-light text-center">
          <img class="img-fluid" :src="exportData">
        </div>
      </div>
    </div>
    <i v-else class="fa-solid fa-circle-notch fa-spin"></i>
  </div>
</template>

<style scoped>
.clipboard-btn {
  position: absolute;
  top: 0.5rem;
}
</style>

<script>
export default {
  props: {
    resourceType: String,
    exportType: String,
    endpoint: String,
    extras: {
      type: Array,
      default: () => [],
    },
  },
  data() {
    return {
      suffix: kadi.utils.randomAlnum(),
      exportData: null,
      loading: true,
      showUpdateButton: false,
      clipboardBtnStyle: '',
      filter: {},
    };
  },
  computed: {
    downloadEndpoint() {
      return `${this.endpoint}?download=true&filter=${JSON.stringify(this.filter)}`;
    },
    serializedExportData() {
      if (typeof this.exportData === 'string') {
        return this.exportData;
      }

      return JSON.stringify(this.exportData, null, 2);
    },
    isCustomizable() {
      return this.exportType !== 'qr';
    },
    hasTextPreview() {
      return ['json', 'json-schema', 'rdf', 'ro-crate', 'shacl'].includes(this.exportType);
    },
    allowExtrasPropagation() {
      return ['json', 'ro-crate'].includes(this.exportType);
    },
  },
  mounted() {
    this.updateExportData();
  },
  methods: {
    async updateExportData(scrollIntoView = false) {
      this.loading = true;

      try {
        const params = {filter: JSON.stringify(this.filter)};
        const response = await axios.get(this.endpoint, {params});

        this.exportData = response.data;
        this.loading = false;

        await this.$nextTick();

        if (this.hasTextPreview) {
          if (this.$refs.textContent.scrollHeight > this.$refs.textContent.clientHeight) {
            this.clipboardBtnStyle = 'right: 1.5rem;';
          } else {
            this.clipboardBtnStyle = 'right: 0.5rem;';
          }
        }

        if (scrollIntoView) {
          kadi.utils.scrollIntoView(this.$refs.previewContainer, 'top');
        }
      } catch (error) {
        kadi.base.flashDanger($t('Error loading export data.'), error.request);
      }
    },
    updatePreview() {
      this.updateExportData(true);
    },
  },
};
</script>
