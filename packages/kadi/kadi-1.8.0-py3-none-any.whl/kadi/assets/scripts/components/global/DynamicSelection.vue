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
  <select :id="id" ref="select" :multiple="multiple" :disabled="disabled">
    <!-- Including an empty option is required for single selections to behave properly. -->
    <option v-if="!multiple"></option>
  </select>
</template>

<script>
export default {
  props: {
    endpoint: String,
    id: {
      type: String,
      default: () => kadi.utils.randomAlnum(),
    },
    multiple: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    requestParams: {
      type: Object,
      default: () => ({}),
    },
    containerClasses: {
      type: String,
      default: '',
    },
    placeholder: {
      type: String,
      default: '',
    },
    tags: {
      type: Boolean,
      default: false,
    },
    maxInputLength: {
      type: Number,
      default: null,
    },
    dropdownParent: {
      type: String,
      default: null,
    },
    initialValues: {
      type: Array,
      default: () => [],
    },
    resetOnSelect: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['select', 'unselect'],
  data() {
    return {
      select: null,
    };
  },
  mounted() {
    this.select = $(this.$refs.select).select2({
      containerCssClass: this.containerClasses,
      placeholder: this.placeholder,
      tags: this.tags,
      maximumInputLength: this.maxInputLength,
      dropdownParent: this.dropdownParent ? $(this.dropdownParent) : null,
      allowClear: !this.multiple,
      templateResult: (data) => {
        if (!data.id || !data.body) {
          return data.text;
        }
        return $(data.body);
      },
      ajax: {
        url: this.endpoint,
        delay: 300,
        data: (params) => {
          return {
            page: params.page || 1,
            term: params.term,
            ...this.requestParams,
          };
        },
      },
      language: {
        inputTooLong(args) {
          const overChars = args.input.length - args.maximum;
          return overChars === 1
            ? $t('Please delete {{chars}} character', {chars: overChars})
            : $t('Please delete {{chars}} characters', {chars: overChars});
        },
        loadingMore() {
          return $t('Loading...');
        },
        noResults() {
          return $t('No results.');
        },
        removeAllItems() {
          return $t('Clear selection');
        },
        searching() {
          return $t('Searching...');
        },
      },
    });

    this.initialValues.forEach((option) => {
      this.select.append(new Option(option[1], option[0], true, true)).trigger('change');
    });

    this.select.on('select2:select', (e) => {
      this.$emit('select', e.params.data);

      if (this.resetOnSelect) {
        this.select.val(null).trigger('change');
      }
    });

    this.select.on('select2:unselect', (e) => {
      this.$emit('unselect', e.params.data);
      this.$nextTick(() => this.select.select2('close'));
    });

    const searchInput = this.select.data('select2').$container.find('.select2-search__field')[0];

    if (searchInput) {
      // Ensure the input is always initialized to a sensible default value.
      searchInput.style.width = '100%';

      // Workaround for the search input not receiving focus using newer jQuery versions and to prevent unnecessary
      // change events propagating to the outside.
      this.select.on('select2:open', () => {
        searchInput.focus();
        searchInput.addEventListener('change', (e) => e.stopPropagation());
      });
    }
  },
  unmounted() {
    this.select.select2('destroy');
  },
};
</script>
