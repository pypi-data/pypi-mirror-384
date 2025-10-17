<!-- Copyright 2020 Karlsruhe Institute of Technology
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
  <div class="row">
    <div class="col-2 ws-nowrap">{{ min }}</div>
    <div class="col-8">
      <input v-model.number="value"
             type="range"
             class="w-100"
             :min="min"
             :max="max"
             :step="step"
             @change="$emit('change', value)">
    </div>
    <div class="col-2 ws-nowrap d-flex justify-content-end">{{ max }}</div>
  </div>
</template>

<script>
export default {
  props: {
    initialValue: {
      type: Number,
      default: 0,
    },
    min: {
      type: Number,
      default: 0,
    },
    max: {
      type: Number,
      default: 100,
    },
    step: {
      type: Number,
      default: 10,
    },
  },
  emits: ['change', 'input'],
  data() {
    return {
      value: this.initialValue,
    };
  },
  watch: {
    value() {
      this.$emit('input', this.value);
    },
  },
};
</script>
