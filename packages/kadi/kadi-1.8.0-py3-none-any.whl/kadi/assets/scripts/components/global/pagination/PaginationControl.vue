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
  <div v-if="totalPages > 1" class="input-group input-group-sm">
    <div class="input-group-prepend">
      <button type="button" class="btn btn-light" :disabled="page === 1" @click="page = 1">
        <i class="fa-solid fa-angles-left"></i>
      </button>
    </div>
    <div class="input-group-prepend">
      <button type="button" class="btn btn-light" :disabled="page === 1" @click="page--">
        <i class="fa-solid fa-angle-left"></i>
      </button>
    </div>
    <div class="input-group-prepend">
      <span class="input-group-text bg-light text-primary">{{ $t('Page') }}</span>
    </div>
    <input v-model.number="page" class="input form-control">
    <div class="input-group-append">
      <span class="input-group-text bg-light text-primary">{{ $t('of') }} {{ totalPages }}</span>
    </div>
    <div class="input-group-append">
      <button type="button" class="btn btn-light" :disabled="page === totalPages" @click="page++">
        <i class="fa-solid fa-angle-right"></i>
      </button>
    </div>
    <div class="input-group-append">
      <button type="button" class="btn btn-light" :disabled="page === totalPages" @click="page = totalPages">
        <i class="fa-solid fa-angles-right"></i>
      </button>
    </div>
    <slot></slot>
  </div>
</template>

<style scoped>
.input {
  background-color: #ffffff;
  border: 1px solid #ced4da;
  max-width: 50px;
  text-align: center;
}
</style>

<script>
export default {
  props: {
    total: Number,
    perPage: Number,
    maxPages: {
      type: Number,
      default: null,
    },
  },
  emits: ['update-page'],
  data() {
    return {
      page: 1,
      prevPage: 1,
    };
  },
  computed: {
    totalPages() {
      let totalPages = Math.ceil(this.total / this.perPage);

      if (this.maxPages !== null && totalPages > this.maxPages) {
        totalPages = this.maxPages;
      }

      if (totalPages <= 1) {
        totalPages = 1;
        this.updatePage(totalPages);
      } else if (this.page > totalPages) {
        this.updatePage(totalPages);
      }

      return totalPages;
    },
  },
  watch: {
    page() {
      let page = this.page;

      if (page < 1 || window.isNaN(page)) {
        page = 1;
      } else if (page > this.totalPages) {
        page = this.totalPages;
      }

      this.updatePage(Math.round(page));
    },
  },
  methods: {
    updatePage(page, forceUpdate = false) {
      this.page = page;

      if (this.page !== this.prevPage || forceUpdate) {
        this.prevPage = this.page;
        this.$emit('update-page', this.page);
      }
    },
    // Convenience method to set the page from outside without triggering an update (unless the page is invalid).
    setPage(page) {
      this.page = this.prevPage = page;
    },
  },
};
</script>
