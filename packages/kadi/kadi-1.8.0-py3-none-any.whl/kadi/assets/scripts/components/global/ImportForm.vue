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

<template>
  <div>
    <span class="dropdown">
      <button type="button" class="btn btn-sm btn-light dropdown-toggle mr-1" data-toggle="dropdown">
        {{ $t('Import from file') }}
      </button>
      <div class="dropdown-menu dropdown-menu-right">
        <a class="dropdown-item" href="#" @click="openInput('json')">JSON</a>
        <span v-if="resourceType === 'template'">
          <a class="dropdown-item" href="#" @click="openInput('json-schema')">JSON Schema</a>
          <a class="dropdown-item" href="#" @click="openInput('shacl')">SHACL (Turtle)</a>
        </span>
      </div>
    </span>
    <popover-toggle toggle-class="btn btn-sm btn-light text-muted" :title="$t('Import formats')">
      <template #toggle>
        <i class="fa-regular fa-circle-question"></i> {{ $t('Help') }}
      </template>
      <template #content>
        <strong>JSON</strong>
        <br>
        <!-- eslint-disable-next-line @stylistic/js/max-len -->
        {{ $t('This import can be used to prefill basic and, if applicable, generic metadata. Note that only the JSON format used by Kadi4Mat is supported.') }}
        <span v-if="['record', 'template'].includes(resourceType)">
          {{ $t('Valid contents include the exported data of records, record templates and extras templates.') }}
        </span>
        <div v-if="resourceType === 'template'">
          <hr>
          <strong>JSON Schema</strong>
          <br>
          <!-- eslint-disable-next-line @stylistic/js/max-len -->
          {{ $t('This import can be used to prefill generic metadata. Note that only JSON Schema version 2020-12 is supported, but older schemas might still work.') }}
          <hr>
          <strong>SHACL (Turtle)</strong>
          <br>
          <!-- eslint-disable-next-line @stylistic/js/max-len -->
          {{ $t('This import can be used to prefill some basic and, if applicable, generic metadata. Note that the supported SHACL structure is based on the structure exported by Kadi4Mat.') }}
        </div>
      </template>
    </popover-toggle>
    <submission-form ref="form" enctype="multipart/form-data" :check-dirty="false">
      <input class="input" :name="importTypeName" :value="importType">
      <input ref="input" type="file" class="input" :name="importDataName" :accept="accept" @change="changeFile">
      <slot></slot>
    </submission-form>
  </div>
</template>

<style scoped>
.input {
  position: absolute;
  visibility: hidden;
}
</style>

<script>
export default {
  props: {
    resourceType: String,
    maxSize: Number,
    importTypeName: {
      type: String,
      default: 'import_type',
    },
    importDataName: {
      type: String,
      default: 'import_data',
    },
  },
  data() {
    return {
      importTypes: {
        json: ['application/json'],
        'json-schema': ['application/json'],
        shacl: ['text/turtle', 'text/plain'],
      },
      importType: '',
      accept: '',
    };
  },
  methods: {
    async openInput(type) {
      this.importType = type;
      this.accept = this.importTypes[type].join(',');

      await this.$nextTick();

      this.$refs.input.click();
    },
    changeFile(e) {
      const file = e.target.files[0];

      if (file.size > this.maxSize) {
        kadi.base.flashWarning($t('File exceeds the maximum size.'));
        this.$refs.input.value = '';
      } else {
        this.$refs.form.submit();
      }
    },
  },
};
</script>
