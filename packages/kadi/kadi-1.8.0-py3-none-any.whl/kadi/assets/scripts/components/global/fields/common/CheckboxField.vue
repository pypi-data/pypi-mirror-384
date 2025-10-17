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
  <div class="form-group">
    <div class="form-check">
      <input :id="field.id"
             v-model="data"
             type="checkbox"
             class="form-check-input"
             :name="field.name"
             :disabled="disabled">
      <label class="form-check-label" :for="field.id">
        <slot>{{ field.label }}</slot>
      </label>
    </div>
    <div v-for="error in field.errors" :key="error" class="invalid-feedback mt-0">{{ error }}</div>
    <small v-if="field.errors.length === 0" class="form-text text-muted mt-0">{{ field.description }}</small>
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
    disabled: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['change'],
  data() {
    return {
      data: this.field.data,
    };
  },
  watch: {
    data() {
      this.$emit('change', this.data);
    },
  },
};
</script>
