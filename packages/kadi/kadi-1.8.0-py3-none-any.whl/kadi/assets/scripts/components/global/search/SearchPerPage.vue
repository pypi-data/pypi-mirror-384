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
  <div class="card">
    <div class="card-header py-2">{{ $t('Results per page') }}: {{ value }}</div>
    <range-slider class="mt-3 mx-2 mb-2" :min="min" :initial-value="value" @input="value = $event" @change="change">
    </range-slider>
  </div>
</template>

<script>
export default {
  emits: ['search'],
  data() {
    return {
      value: null,
      min: 10,
      max: 100,
      param: 'per_page',
    };
  },
  beforeMount() {
    this.value = this.min;

    if (kadi.utils.hasSearchParam(this.param)) {
      let value = kadi.utils.getSearchParam(this.param);
      value = Number.parseInt(value, 10) || this.min;

      this.value = kadi.utils.clamp(value, this.min, this.max);
      this.setSearchParam();
    }
  },
  methods: {
    change() {
      this.setSearchParam();
      this.$emit('search');
    },
    setSearchParam() {
      let url = null;

      if (this.value !== this.min) {
        url = kadi.utils.setSearchParam(this.param, this.value);
      } else {
        url = kadi.utils.removeSearchParam(this.param);
      }

      kadi.utils.replaceState(url);
    },
  },
};
</script>
