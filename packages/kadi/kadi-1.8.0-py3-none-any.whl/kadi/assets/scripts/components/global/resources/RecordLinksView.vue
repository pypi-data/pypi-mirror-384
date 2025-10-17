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
  <dynamic-pagination :endpoint="endpoint"
                      :args="{sort: sortAscending ? sort : `-${sort}`}"
                      :placeholder="placeholder"
                      :per-page="perPage"
                      :enable-filter="enableFilter">
    <template #default="paginationProps">
      <div class="row align-items-center">
        <div class="col-md-6 col-xl-8">
          <p>
            <strong>{{ title }}</strong>
            <span class="badge-total">{{ paginationProps.total }}</span>
          </p>
        </div>
        <div v-if="paginationProps.totalUnfiltered > 1" class="col-md-6 col-xl-4 mb-3 mb-md-2">
          <div class="input-group input-group-sm">
            <div class="input-group-prepend">
              <label class="input-group-text" :for="`sort-${id}`">{{ $t('Sort by') }}</label>
            </div>
            <select :id="`sort-${id}`"
                    class="custom-select"
                    :value="sort"
                    @input="changeSortOption($event.target.value)">
              <option v-for="option in sortOptions" :key="option.name" :value="option.name">{{ option.title }}</option>
            </select>
            <div class="input-group-append">
              <button type="button"
                      class="btn btn-light"
                      :title="sortAscending ? $t('Ascending') : $t('Descending')"
                      @click="sortAscending = !sortAscending">
                <i v-if="sortAscending" class="fa-solid fa-arrow-down-short-wide"></i>
                <i v-else class="fa-solid fa-arrow-down-wide-short"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <card-deck :items="paginationProps.items">
        <template #default="props">
          <div class="card-header bg-white py-2">
            <strong class="font-italic">{{ props.item.name }}</strong>
          </div>
          <div class="card-body py-2">
            <a class="text-default stretched-link" :href="getLinkedRecord(props.item)._links.view">
              <resource-type class="float-right badge-mt-plus ml-3" :type="getLinkedRecord(props.item).type">
              </resource-type>
              <basic-resource-info :resource="getLinkedRecord(props.item)" :show-description="false">
              </basic-resource-info>
            </a>
          </div>
          <div class="card-footer py-1">
            <small class="text-muted">
              {{ $t('Last modified') }} <from-now :timestamp="props.item.last_modified"></from-now>
            </small>
          </div>
          <div class="card-footer elevated py-1">
            <div class="d-flex justify-content-between">
              <a class="btn btn-sm btn-link text-primary p-0" :href="props.item._links.view">
                <i class="fa-solid fa-eye"></i> {{ $t('View link') }}
              </a>
              <a v-if="props.item._links.edit"
                 class="btn btn-sm btn-link text-primary p-0"
                 :href="props.item._links.edit">
                <i class="fa-solid fa-pencil"></i> {{ $t('Edit link') }}
              </a>
            </div>
          </div>
        </template>
      </card-deck>
    </template>
  </dynamic-pagination>
</template>

<script>
export default {
  props: {
    title: String,
    endpoint: String,
    direction: String,
    placeholder: {
      type: String,
      default: $t('No record links.'),
    },
    perPage: {
      type: Number,
      default: 6,
    },
    enableFilter: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      id: kadi.utils.randomAlnum(),
      sort: 'last_modified',
      sortAscending: false,
      sortOptions: [
        {name: 'last_modified', title: $t('Modification date'), sortAscending: false},
        {name: 'created_at', title: $t('Creation date'), sortAscending: false},
        {name: 'name', title: $t('Name'), sortAscending: true},
      ],
    };
  },
  methods: {
    changeSortOption(sort) {
      const option = this.sortOptions.find((option) => option.name === sort);
      this.sort = sort;
      this.sortAscending = option.sortAscending;
    },
    getLinkedRecord(link) {
      return this.direction === 'out' ? link.record_to : link.record_from;
    },
  },
};
</script>
