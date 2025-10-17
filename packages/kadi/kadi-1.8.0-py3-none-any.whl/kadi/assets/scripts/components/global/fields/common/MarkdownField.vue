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
      <markdown-editor :id="field.id"
                       :name="field.name"
                       :required="field.validation.required"
                       :initial-value="field.data"
                       :link-endpoint="linkEndpoint"
                       :image-endpoint="imageEndpoint"
                       :rows="rows"
                       :has-error="props.hasError"
                       @input="data = $event">
      </markdown-editor>
    </template>
  </base-field>
</template>

<script>
export default {
  props: {
    field: Object,
    linkEndpoint: {
      type: String,
      default: null,
    },
    imageEndpoint: {
      type: String,
      default: null,
    },
    rows: {
      type: Number,
      default: 8,
    },
  },
  emits: ['input'],
  data() {
    return {
      data: this.field.data,
    };
  },
  watch: {
    data() {
      this.$emit('input', this.data);
      this.$refs.base.validate(this.data);
    },
  },
};
</script>
