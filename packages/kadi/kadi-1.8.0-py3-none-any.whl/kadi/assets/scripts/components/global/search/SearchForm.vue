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
  <div>
    <div v-if="extrasSearch" :id="extrasId" class="mb-4">
      <search-extras :query-string="extras" @change="extras = $event" @search="search"></search-extras>
    </div>
    <div class="form-row">
      <div class="mb-2 mb-xl-0" :class="{'col-xl-6': extrasSearch, 'col-xl-8': !extrasSearch}">
        <div class="input-group">
          <input :id="`query-${id}`"
                 v-model="query"
                 class="form-control"
                 :placeholder="$t('Search title, identifier and description')"
                 @keydown.enter="search">
          <clear-button :input="query" :input-id="`query-${id}`" @clear-input="query = ''"></clear-button>
          <div class="input-group-append">
            <button type="button"
                    class="btn btn-light"
                    :disabled="!query"
                    :title="$t('Toggle whole word match')"
                    @click="toggleQuotation">
              <i class="fa-solid fa-quote-left"></i>
            </button>
            <button type="button" class="btn btn-light" :title="$t('Execute search')" @click="search">
              <i class="fa-solid fa-magnifying-glass"></i> {{ $t('Search') }}
            </button>
          </div>
        </div>
      </div>
      <div class="col-xl-4 mb-2 mb-xl-0">
        <div class="input-group">
          <div class="input-group-prepend">
            <label class="input-group-text" :for="`sort-${id}`">{{ $t('Sort by') }}</label>
          </div>
          <select :id="`sort-${id}`" class="custom-select" :value="sort" @input="changeSortOption($event.target.value)">
            <option v-for="option in sortOptions" :key="option.name" :value="option.name">{{ option.title }}</option>
          </select>
          <div v-if="sort !== sortOptions[0].name" class="input-group-append">
            <button type="button"
                    class="btn btn-light"
                    :title="sortAscending ? $t('Ascending') : $t('Descending')"
                    @click="toggleSortDirection">
              <i v-if="sortAscending" class="fa-solid fa-arrow-down-short-wide"></i>
              <i v-else class="fa-solid fa-arrow-down-wide-short"></i>
            </button>
          </div>
        </div>
      </div>
      <div v-if="extrasSearch" class="col-xl-2">
        <collapse-item :id="extrasId"
                       class="btn btn-block btn-light"
                       :is-collapsed="!extrasSearchActive"
                       :title="$t('Search extra metadata')"
                       @collapse="extrasSearchActive = !$event">
          {{ $t('Extras') }}
        </collapse-item>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    extrasSearch: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['search'],
  data() {
    return {
      id: kadi.utils.randomAlnum(),
      query: '',
      prevQuery: '',
      queryParam: 'query',
      sort: '_score',
      sortAscending: true,
      sortParam: 'sort',
      sortOptions: [
        {name: '_score', title: $t('Relevance'), sortAscending: true},
        {name: 'last_modified', title: $t('Modification date'), sortAscending: false},
        {name: 'created_at', title: $t('Creation date'), sortAscending: false},
        {name: 'title', title: $t('Title'), sortAscending: true},
        {name: 'identifier', title: $t('Identifier'), sortAscending: true},
      ],
      extras: '[]',
      prevExtras: '[]',
      extrasParam: 'extras',
      extrasId: kadi.utils.randomAlnum(),
      extrasSearchActive: false,
      prevExtrasSearchActive: false,
      initialized: false,
    };
  },
  async beforeMount() {
    if (kadi.utils.hasSearchParam(this.queryParam)) {
      this.query = kadi.utils.getSearchParam(this.queryParam);
      this.prevQuery = this.query;

      this.setSearchParam(this.query, this.queryParam, this.query);
    }

    if (kadi.utils.hasSearchParam(this.extrasParam)) {
      this.extras = kadi.utils.getSearchParam(this.extrasParam);
      this.prevExtras = this.extras;
      this.prevExtrasSearchActive = this.extrasSearchActive = true;

      this.setSearchParam(this.extrasSearchActive, this.extrasParam, this.extras);
    }

    if (kadi.utils.hasSearchParam(this.sortParam)) {
      const options = [];

      for (const option of this.sortOptions) {
        options.push(option.name);

        if (option !== this.sortOptions[0]) {
          options.push(`-${option.name}`);
        }
      }

      const sort = kadi.utils.getSearchParam(this.sortParam);

      if (options.includes(sort)) {
        if (sort.startsWith('-')) {
          this.sort = sort.substring(1);
          this.sortAscending = false;
        } else {
          this.sort = sort;
        }
      }

      this.updateSort();
    }

    // Skip first potential change.
    await this.$nextTick();
    this.initialized = true;
  },
  methods: {
    toggleQuotation() {
      if (kadi.utils.isQuoted(this.query)) {
        this.query = this.query.slice(1, this.query.length - 1);
      } else {
        this.query = `"${this.query}"`;
      }
    },
    changeSortOption(sort) {
      const option = this.sortOptions.find((option) => option.name === sort);
      this.sort = sort;
      this.sortAscending = option.sortAscending;
      this.updateSort();
    },
    toggleSortDirection() {
      this.sortAscending = !this.sortAscending;
      this.updateSort();
    },
    updateSort() {
      const paramValue = this.sortAscending ? this.sort : `-${this.sort}`;
      this.setSearchParam(this.sort !== this.sortOptions[0].name, this.sortParam, paramValue);

      if (this.initialized) {
        this.$emit('search');
      }
    },
    setSearchParam(condition, param, value) {
      let url = null;

      if (condition) {
        url = kadi.utils.setSearchParam(param, value);
      } else {
        url = kadi.utils.removeSearchParam(param);
      }

      kadi.utils.replaceState(url);
    },
    search() {
      // Do not search if nothing changed.
      if (this.query === this.prevQuery
          && this.extras === this.prevExtras
          && this.extrasSearchActive === this.prevExtrasSearchActive) {
        return;
      }

      this.setSearchParam(this.query, this.queryParam, this.query);
      this.setSearchParam(this.extrasSearchActive, this.extrasParam, this.extras);

      this.$emit('search');

      this.prevQuery = this.query;
      this.prevExtras = this.extras;
      this.prevExtrasSearchActive = this.extrasSearchActive;
    },
  },
};
</script>
