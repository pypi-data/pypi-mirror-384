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
  <base-field ref="base" :field="field">
    <template #default="props">
      <div class="input-group">
        <slot name="prepend"></slot>
        <input :id="field.id"
               v-model="data"
               :name="field.name"
               :required="field.validation.required"
               :disabled="disabled"
               :placeholder="placeholder"
               :class="['form-control', {'has-error': props.hasError}]">
        <slot name="append"></slot>
      </div>
    </template>
  </base-field>
</template>

<script>
export default {
  props: {
    field: Object,
    input: {
      type: String,
      default: null,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    placeholder: {
      type: String,
      default: '',
    },
  },
  emits: ['input'],
  data() {
    return {
      data: this.field.data,
    };
  },
  watch: {
    input() {
      this.data = this.input;
      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
    data() {
      this.$emit('input', this.data);
      this.$refs.base.validate(this.data);
    },
  },
};
</script>
