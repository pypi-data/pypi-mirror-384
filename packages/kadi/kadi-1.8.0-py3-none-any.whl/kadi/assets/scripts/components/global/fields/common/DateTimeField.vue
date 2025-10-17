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
  <base-field :field="field">
    <template #default="props">
      <input type="hidden" :name="field.name" :value="data">
      <date-time-picker :id="field.id"
                        :required="field.validation.required"
                        :initial-value="field.data"
                        :class="{'has-error': props.hasError}"
                        @input="data = $event">
      </date-time-picker>
    </template>
  </base-field>
</template>

<script>
export default {
  props: {
    field: Object,
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
    },
  },
};
</script>
