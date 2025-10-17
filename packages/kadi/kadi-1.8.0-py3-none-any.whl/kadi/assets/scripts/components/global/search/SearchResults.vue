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
  <div ref="container" class="card">
    <div v-show="connectServiceEndpoint" class="card-body">
      <service-manager :connect-endpoint="connectServiceEndpoint" :manage-endpoint="manageServicesEndpoint">
      </service-manager>
    </div>
    <div v-show="!connectServiceEndpoint">
      <div class="card-header py-2">
        <div class="d-flex justify-content-between align-items-center">
          <span v-if="initialized">{{ searchResultsText }}</span>
          <span v-else>{{ $t('Loading...') }}</span>
          <i v-if="loading" class="fa-solid fa-circle-notch fa-spin"></i>
        </div>
      </div>
      <div class="card-body results">
        <div class="list-group list-group-flush">
          <div v-for="resource in resources"
               :key="resource.id"
               class="list-group-item list-group-item-action text-body p-0">
            <a class="text-default"
               :href="resource._links.view"
               :target="isExternal ? '_blank' : null"
               :rel="isExternal ? 'noopener noreferrer' : null">
              <div class="result">
                <img v-if="resource._links.image"
                     class="img-max-100 img-thumbnail float-sm-left mr-sm-3 mb-2"
                     loading="lazy"
                     :src="resource._links.image">
                <div class="d-flow-root">
                  <div class="row mb-2 mb-sm-0">
                    <div v-trim-ws class="col-sm-7">
                      <small>
                        <resource-visibility :visibility="resource.visibility"></resource-visibility>
                      </small>
                      <strong class="ml-2" :class="{'mr-2': resource.type}">{{ resource.title }}</strong>
                      <resource-type class="badge-mt-minus" :type="resource.type" :is-template="Boolean(resource.data)">
                      </resource-type>
                      <p>@{{ resource.identifier }}</p>
                    </div>
                    <div class="col-sm-5 d-sm-flex justify-content-end mb-2 mb-sm-0">
                      <div class="text-sm-right">
                        <small class="text-muted">
                          {{ $t('Created') }} <from-now :timestamp="resource.created_at"></from-now>
                        </small>
                        <br>
                        <small class="text-muted">
                          {{ $t('Last modified') }} <from-now :timestamp="resource.last_modified"></from-now>
                        </small>
                      </div>
                    </div>
                  </div>
                  <div class="text-muted pb-3">
                    <span v-if="resource.plain_description">
                      {{ kadi.utils.truncate(resource.plain_description, 250) }}
                    </span>
                    <em v-else>{{ $t('No description.') }}</em>
                  </div>
                  <div class="row align-items-end">
                    <div :class="{'col-sm-8': hasExtras(resource), 'col-sm-12': !hasExtras(resource)}">
                      <div v-if="resource.creator">
                        {{ $t('Created by') }}
                        <identity-popover v-if="!isExternal" :user="resource.creator"></identity-popover>
                        <a v-else target="_blank" rel="noopener noreferrer" :href="resource.creator._links.view">
                          <strong>{{ kadi.utils.truncate(resource.creator.displayname, 50) }}</strong>
                        </a>
                      </div>
                    </div>
                    <div v-if="hasExtras(resource)"
                         class="col-sm-4 mt-2 mt-sm-0 d-flex justify-content-sm-end align-items-end">
                      <collapse-item :id="`extras-${resource.id}`"
                                     class="text-default"
                                     :is-collapsed="true"
                                     @collapse="renderExtras(resource)">
                        {{ $t('Extra metadata') }}
                      </collapse-item>
                    </div>
                  </div>
                </div>
              </div>
            </a>
            <div v-if="hasExtras(resource)" :id="`extras-${resource.id}`" class="mx-2 mb-2">
              <extras-viewer v-if="renderedExtras[resource.id]" :extras="resource.extras" :show-toolbar="false">
              </extras-viewer>
            </div>
          </div>
          <div v-if="!loading && resources.length === 0" class="list-group-item">
            <em class="text-muted">{{ $t('No results.') }}</em>
          </div>
        </div>
        <div class="border-top justify-content-center" :class="{'d-flex': total > perPage, 'd-none': total <= perPage}">
          <div class="py-3">
            <pagination-control ref="pagination"
                                :total="total"
                                :per-page="perPage"
                                :max-pages="100"
                                @update-page="updatePage">
            </pagination-control>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results {
  padding: 0 0 1px 0;
}

.result {
  padding: 0.75rem 1.25rem;
}
</style>

<script>
export default {
  props: {
    endpoint: String,
    manageServicesEndpoint: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      resources: [],
      // To keep track of all resource IDs where the extra metadata has at least been shown once.
      renderedExtras: {},
      total: 0,
      perPage: 10,
      pageParam: 'page',
      connectServiceEndpoint: '',
      isExternal: false,
      initialized: false,
      loading: false,
      searchTimeoutHandle: null,
    };
  },
  computed: {
    searchResultsText() {
      const resultsText = this.total === 1 ? $t('result found') : $t('results found');
      return `${this.total} ${resultsText}`;
    },
  },
  mounted() {
    this.search(false);
  },
  methods: {
    hasExtras(resource) {
      return resource.extras && resource.extras.length > 0;
    },
    renderExtras(resource) {
      this.renderedExtras[resource.id] = true;
    },
    updatePage(page) {
      const url = kadi.utils.setSearchParam(this.pageParam, page);
      kadi.utils.replaceState(url);
      this.search(false, true);
    },
    search(removePageParam = true, scrollIntoView = false) {
      this.loading = true;

      if (removePageParam) {
        const url = kadi.utils.removeSearchParam(this.pageParam);
        kadi.utils.replaceState(url);
        this.$refs.pagination.setPage(1);
      }

      const _updateData = async() => {
        const params = {};
        const searchParams = new URLSearchParams(window.location.search);

        for (const key of searchParams.keys()) {
          params[key] = searchParams.getAll(key);
        }

        // If the instance query parameter is present, we assume a federated search.
        this.isExternal = Boolean(params.instance);
        this.perPage = Number.parseInt(params.per_page, 10) || 10;
        this.connectServiceEndpoint = '';

        try {
          const response = await axios.get(this.endpoint, {params});
          const data = response.data;

          this.resources = data.items;
          this.total = data._pagination.total_items;

          if (!this.initialized) {
            this.$refs.pagination.setPage(data._pagination.page);
          }
        } catch (error) {
          this.resources = [];
          this.total = 0;

          if (error.request.status === 400) {
            this.connectServiceEndpoint = error.response.data._links.connect;
          } else {
            kadi.base.flashDanger($t('Error loading search results.'), error.request);
          }
        } finally {
          this.initialized = true;
          this.loading = false;

          if (scrollIntoView) {
            kadi.utils.scrollIntoView(this.$refs.container, 'top');
          }
        }
      };

      window.clearTimeout(this.searchTimeoutHandle);
      this.searchTimeoutHandle = window.setTimeout(_updateData, 500);
    },
  },
};
</script>
