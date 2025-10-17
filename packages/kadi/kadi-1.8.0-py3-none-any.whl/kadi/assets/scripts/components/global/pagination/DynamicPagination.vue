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
  <div>
    <slot :items="items" :total="total" :total-unfiltered="totalUnfiltered"></slot>
    <em v-if="initialized && total === 0" class="text-muted">{{ placeholder }}</em>
    <i v-if="!initialized" class="fa-solid fa-circle-notch fa-spin"></i>
    <div v-show="initialized && totalUnfiltered > 0" class="row" :class="{'mt-4': total > perPage || enableFilter}">
      <div v-show="total > perPage"
           :class="{'col-md-6 col-xl-8 mb-2 mb-md-0': enableFilter, 'col-md-12': !enableFilter}">
        <pagination-control ref="pagination" :total="total" :per-page="perPage" @update-page="onUpdatePage">
          <i v-if="loading" class="fa-solid fa-circle-notch fa-spin ml-4 align-self-center"></i>
        </pagination-control>
      </div>
      <div v-if="enableFilter" class="col-md-6 col-xl-4">
        <div class="input-group input-group-sm">
          <input :id="filterId" v-model.trim="filter" class="form-control" :placeholder="filterPlaceholder">
          <clear-button :input-id="filterId" :input="filter" @clear-input="resetFilter"></clear-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    endpoint: String,
    args: {
      type: Object,
      default: () => ({}),
    },
    placeholder: {
      type: String,
      default: $t('No results.'),
    },
    perPage: {
      type: Number,
      default: 10,
    },
    enableFilter: {
      type: Boolean,
      default: false,
    },
    filterPlaceholder: {
      type: String,
      default: $t('Filter'),
    },
  },
  data() {
    return {
      items: [],
      total: 0,
      totalUnfiltered: 0,
      page: 1,
      filter: '',
      filterId: kadi.utils.randomAlnum(),
      initialized: false,
      loading: false,
      updateTimeoutHandle: null,
    };
  },
  watch: {
    endpoint() {
      this.resetPage();
    },
    args(newValue, oldValue) {
      if (!kadi.utils.objectsEqual(newValue, oldValue)) {
        this.resetPage();
      }
    },
    perPage() {
      this.resetPage();
    },
    filter() {
      this.resetPage();
    },
  },
  mounted() {
    this.update();
  },
  methods: {
    onUpdatePage(page) {
      this.page = page;

      window.clearTimeout(this.updateTimeoutHandle);
      this.updateTimeoutHandle = window.setTimeout(this.update, 500);
    },
    resetPage() {
      this.$refs.pagination.updatePage(1, true);
    },
    resetFilter() {
      this.filter = '';
    },
    async update() {
      this.loading = true;

      const args = {...this.args};

      if (this.enableFilter) {
        args.filter = this.filter;
      }

      try {
        const params = {page: this.page, per_page: this.perPage, ...args};
        const response = await axios.get(this.endpoint, {params});

        this.items = response.data.items;
        this.total = response.data._pagination.total_items;

        // Only update the unfiltered total amount if no filter is currently specified. This should at least be the
        // case once after mounting.
        if (!this.filter) {
          this.totalUnfiltered = this.total;
        }

        this.initialized = true;
      } catch (error) {
        kadi.base.flashDanger($t('Error loading data.'), error.request);
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
