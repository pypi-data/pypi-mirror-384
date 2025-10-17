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
        <div :class="enableSort ? 'col-md-6 col-xl-8' : 'col-6'">
          <p>
            <strong>{{ title }}</strong>
            <span class="badge-total">{{ paginationProps.total }}</span>
          </p>
        </div>
        <div v-if="paginationProps.totalUnfiltered > 0"
             class="mb-3 mb-md-2 d-flex justify-content-end"
             :class="enableSort ? 'col-md-6 col-xl-4' : 'col-6'">
          <div v-if="enableSort && paginationProps.total > 1" class="flex-grow-1 mr-2">
            <div class="input-group input-group-sm">
              <div class="input-group-prepend">
                <label class="input-group-text" :for="`sort-${id}`">{{ $t('Sort by') }}</label>
              </div>
              <select :id="`sort-${id}`"
                      class="custom-select"
                      :value="sort"
                      @input="changeSortOption($event.target.value)">
                <option v-for="option in sortOptions" :key="option.name" :value="option.name">
                  {{ option.title }}
                </option>
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
          <div v-if="paginationProps.total > 0">
            <button class="btn btn-sm btn-light" :title="$t('Change layout')" @click="changeView">
              <i v-if="isListView" class="fa-solid fa-table"></i>
              <i v-else class="fa-solid fa-list-ul"></i>
            </button>
          </div>
        </div>
      </div>
      <ul v-if="isListView" class="list-group">
        <li v-for="item in paginationProps.items" :key="item.id" class="list-group-item list-group-item-action py-1">
          <a class="text-default stretched-link" :href="item._links.view">
            <div class="form-row align-items-center">
              <div v-trim-ws class="col-md-4 order-1">
                <small>
                  <resource-visibility :visibility="item.visibility"></resource-visibility>
                </small>
                <strong class="ml-2">{{ item.title }}</strong>
              </div>
              <div class="col-md-3 order-3">
                <small>@{{ item.identifier }}</small>
              </div>
              <div class="col-md-3 order-3">
                <small class="text-muted">
                  {{ $t('Last modified') }} <from-now :timestamp="item.last_modified"></from-now>
                </small>
              </div>
              <div class="col-md-2 d-md-flex justify-content-end order-2 order-md-4">
                <span>
                  <resource-type :type="item.type" :is-template="Boolean(item.data)"></resource-type>
                </span>
              </div>
            </div>
          </a>
        </li>
      </ul>
      <card-deck v-else :items="paginationProps.items">
        <template #default="props">
          <div class="card-body py-2">
            <a class="text-default stretched-link" :href="props.item._links.view">
              <resource-type class="float-right badge-mt-plus ml-3"
                             :type="props.item.type"
                             :is-template="Boolean(props.item.data)">
              </resource-type>
              <img v-if="props.item._links.image"
                   class="img-max-75 img-thumbnail float-right ml-3"
                   loading="lazy"
                   :src="props.item._links.image">
              <basic-resource-info :resource="props.item" :show-description="showDescription"></basic-resource-info>
            </a>
          </div>
          <div class="card-footer py-1">
            <small class="text-muted">
              {{ $t('Last modified') }} <from-now :timestamp="props.item.last_modified"></from-now>
            </small>
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
    placeholder: String,
    endpoint: String,
    perPage: {
      type: Number,
      default: 6,
    },
    enableSort: {
      type: Boolean,
      default: true,
    },
    enableFilter: {
      type: Boolean,
      default: true,
    },
    showDescription: {
      type: Boolean,
      default: true,
    },
  },
  data() {
    return {
      id: kadi.utils.randomAlnum(),
      viewStorageKey: 'resource_view_list_layout',
      isListView: false,
      sort: 'last_modified',
      sortAscending: false,
      sortOptions: [
        {name: 'last_modified', title: $t('Modification date'), sortAscending: false},
        {name: 'created_at', title: $t('Creation date'), sortAscending: false},
        {name: 'title', title: $t('Title'), sortAscending: true},
        {name: 'identifier', title: $t('Identifier'), sortAscending: true},
      ],
    };
  },
  mounted() {
    if (window.localStorage.getItem(this.viewStorageKey)) {
      this.isListView = true;
    }

    window.addEventListener('kadi-resource-layout', (e) => {
      if (this.id !== e.detail.id) {
        this.isListView = e.detail.isListView;
      }
    });
  },
  methods: {
    changeSortOption(sort) {
      const option = this.sortOptions.find((option) => option.name === sort);
      this.sort = sort;
      this.sortAscending = option.sortAscending;
    },
    changeView() {
      this.isListView = !this.isListView;

      // Globally dispatch a custom event as well in order to synchronize layout changes between multiple components.
      const event = new CustomEvent('kadi-resource-layout', {detail: {id: this.id, isListView: this.isListView}});
      window.dispatchEvent(event);

      if (this.isListView) {
        window.localStorage.setItem(this.viewStorageKey, 'true');
      } else {
        window.localStorage.removeItem(this.viewStorageKey);
      }
    },
  },
};
</script>
