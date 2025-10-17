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
      <select :id="field.id"
              ref="select"
              v-model="input"
              :name="field.name"
              :required="field.validation.required"
              :disabled="disabled"
              :class="[enableSearch ? 'select2-hidden-accessible' : 'custom-select', {'has-error': props.hasError}]">
        <option v-for="choice in field.choices" :key="choice[0]" :value="choice[0]">{{ choice[1] }}</option>
      </select>
    </template>
  </base-field>
</template>

<script>
export default {
  props: {
    field: Object,
    disabled: {
      type: Boolean,
      default: false,
    },
    enableSearch: {
      type: Boolean,
      default: false,
    },
    searchPlaceholder: {
      type: String,
      default: '',
    },
    searchContainerClasses: {
      type: String,
      default: '',
    },
    searchDropdownParent: {
      type: String,
      default: null,
    },
  },
  emits: ['select'],
  data() {
    return {
      select: null,
      input: null,
      initialValueSet: false,
    };
  },
  watch: {
    input() {
      // Ignore the change event triggered by the initial value.
      if (this.initialValueSet) {
        this.$emit('select', this.input);
        // Dispatch a regular 'change' event from the element as well.
        this.$el.dispatchEvent(new Event('change', {bubbles: true}));
      } else {
        this.initialValueSet = true;
      }
    },
  },
  mounted() {
    if (this.enableSearch) {
      this.select = $(this.$refs.select).select2({
        containerCssClass: this.searchContainerClasses,
        placeholder: this.searchPlaceholder,
        dropdownParent: this.searchDropdownParent ? $(this.searchDropdownParent) : null,
        allowClear: true,
        language: {
          removeAllItems() {
            return $t('Clear selection');
          },
          searching() {
            return $t('Searching...');
          },
        },
      });

      // Keep the input value in sync, which will also trigger the watcher.
      this.select.on('select2:select', (e) => this.input = e.params.data.id);

      // Workaround for the search input not receiving focus using the newest jQuery version.
      this.select.on('select2:open', () => {
        const searchInput = document.querySelector(`[aria-controls=select2-${this.field.id}-results]`);
        searchInput.focus();
      });
    }

    this.selectValue(this.field.data);
  },
  unmounted() {
    if (this.enableSearch) {
      this.select.select2('destroy');
    }
  },
  methods: {
    selectValue(value) {
      for (const choice of this.field.choices) {
        if (choice[0] === value) {
          this.input = value;

          if (this.select) {
            this.select.val(this.input);
            this.select.trigger('change');
          }

          return;
        }
      }

      // Fall back to the first option value.
      this.selectValue(this.field.choices[0][0]);
    },
  },
};
</script>
