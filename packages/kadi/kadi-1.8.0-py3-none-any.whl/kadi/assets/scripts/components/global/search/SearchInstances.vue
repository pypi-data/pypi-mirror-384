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
  <div v-if="instances.length > 0" class="card">
    <div class="card-header py-2">{{ $t('Search external instance') }}</div>
    <div class="card-body p-3">
      <select v-model="value" class="custom-select custom-select-sm">
        <option value="">{{ $t('Current instance') }}</option>
        <option v-for="instance in instances" :key="instance.name" :value="instance.name">{{ instance.title }}</option>
      </select>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    instances: Array,
  },
  emits: ['search', 'instance'],
  data() {
    return {
      value: '',
      param: 'instance',
    };
  },
  watch: {
    value() {
      if (this.initialized) {
        this.setSearchParam();

        this.$emit('search');
        this.$emit('instance', Boolean(this.value));
      }
    },
  },
  async mounted() {
    if (kadi.utils.hasSearchParam(this.param)) {
      const value = kadi.utils.getSearchParam(this.param);

      for (const instance of this.instances) {
        if (instance.name === value) {
          this.value = value;
          break;
        }
      }

      this.setSearchParam();
    }

    // Skip first potential change.
    await this.$nextTick();
    this.initialized = true;

    this.$emit('instance', Boolean(this.value));
  },
  methods: {
    setSearchParam() {
      let url = null;

      if (this.value) {
        url = kadi.utils.setSearchParam(this.param, this.value);
      } else {
        url = kadi.utils.removeSearchParam(this.param);
      }

      kadi.utils.replaceState(url);
    },
  },
};
</script>
