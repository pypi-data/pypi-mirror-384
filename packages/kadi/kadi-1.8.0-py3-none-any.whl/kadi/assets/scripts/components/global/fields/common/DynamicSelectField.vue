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
      <div class="input-group">
        <dynamic-selection :id="field.id"
                           :endpoint="endpoint"
                           :placeholder="placeholder"
                           :initial-values="initialValues"
                           :multiple="multiple"
                           :tags="tags"
                           :max-input-length="maxInputLength_"
                           :container-classes="containerClasses"
                           :name="field.name"
                           :required="field.validation.required"
                           :disabled="disabled"
                           :class="[{'has-error': props.hasError}, 'select2-hidden-accessible']"
                           @select="selectItem"
                           @unselect="unselectItem">
        </dynamic-selection>
        <slot name="append"></slot>
      </div>
    </template>
  </base-field>
</template>

<script>
export default {
  props: {
    field: Object,
    endpoint: String,
    disabled: {
      type: Boolean,
      default: false,
    },
    placeholder: {
      type: String,
      default: '',
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    tags: {
      type: Boolean,
      default: false,
    },
    maxInputLength: {
      type: Number,
      default: null,
    },
    containerClasses: {
      type: String,
      default: '',
    },
  },
  emits: ['select', 'unselect'],
  data() {
    return {
      initialValues: null,
      maxInputLength_: null,
    };
  },
  beforeMount() {
    this.initialValues = this.field.data;

    if (!this.multiple) {
      // Wrap the initial (single) value in an array, if applicable.
      if (this.initialValues) {
        this.initialValues = [this.initialValues];
      } else {
        this.initialValues = [];
      }
    }

    // If no maximum input length is provided explicitly, we try to take it from the field's validation object directly
    // instead.
    this.maxInputLength_ = this.maxInputLength;

    if (!this.maxInputLength && this.field.validation.max) {
      this.maxInputLength_ = this.field.validation.max;
    }
  },
  methods: {
    selectItem(item) {
      this.$emit('select', item);
      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
    unselectItem(item) {
      this.$emit('unselect', item);
      // Dispatch a regular 'change' event from the element as well.
      this.$el.dispatchEvent(new Event('change', {bubbles: true}));
    },
  },
};
</script>
