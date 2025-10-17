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
  <div :class="{'card': showBorder}">
    <div v-if="title" class="card-header py-2">{{ title }}</div>
    <div :class="{'card-body p-3': showBorder}">
      <select v-model="value" class="custom-select custom-select-sm">
        <option v-for="choice in choices" :key="choice[0]" :value="choice[0]">{{ choice[1] }}</option>
      </select>
    </div>
    <slot></slot>
  </div>
</template>

<script>
export default {
  props: {
    param: String,
    choices: Array,
    title: {
      type: String,
      default: null,
    },
    showBorder: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['search'],
  data() {
    return {
      value: null,
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
    this.value = this.choices[0][0];

    if (kadi.utils.hasSearchParam(this.param)) {
      const value = kadi.utils.getSearchParam(this.param);

      for (const choice of this.choices) {
        if (choice[0] === value) {
          this.value = value;
          break;
        }
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

      if (this.value !== this.choices[0][0]) {
        url = kadi.utils.setSearchParam(this.param, this.value);
      } else {
        url = kadi.utils.removeSearchParam(this.param);
      }

      kadi.utils.replaceState(url);
    },
  },
};
</script>
