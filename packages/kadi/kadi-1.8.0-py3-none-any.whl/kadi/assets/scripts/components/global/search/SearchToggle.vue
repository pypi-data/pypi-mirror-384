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
  <div :class="{'card bg-light': showBorder}">
    <div class="d-flex align-items-center" :class="{'card-body py-2': showBorder}">
      <div class="form-check">
        <input :id="id" v-model="value" type="checkbox" class="form-check-input">
        <label :for="id" class="form-check-label">{{ label }}</label>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    label: String,
    param: String,
    showBorder: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['search'],
  data() {
    return {
      id: kadi.utils.randomAlnum(),
      value: false,
      initialized: false,
    };
  },
  watch: {
    value() {
      if (this.initialized) {
        this.setSearchParam();
        this.$emit('search');
      }
    },
  },
  async mounted() {
    if (kadi.utils.hasSearchParam(this.param)) {
      const value = kadi.utils.getSearchParam(this.param);

      if (value === 'true') {
        this.value = true;
      }

      this.setSearchParam();
    }

    // Skip first potential change.
    await this.$nextTick();
    this.initialized = true;
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
