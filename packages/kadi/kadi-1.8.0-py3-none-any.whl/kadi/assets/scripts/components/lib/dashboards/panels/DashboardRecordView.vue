<!-- Copyright 2024 Karlsruhe Institute of Technology
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

<script setup>
import {computed, onBeforeMount, watch} from 'vue';

const props = defineProps({
  endpoints: Object,
  settings: Object,
});

const perPageParam = 'per_page';

const template = computed(() => props.settings.template);
const queryString = computed(() => props.settings.queryString);

const newRecordEndpoint = computed(() => {
  if (!template.value) {
    return null;
  }

  const url = kadi.utils.setSearchParam('template', template.value.id, true, props.endpoints.newRecord);
  return url.toString();
});

const recordsEndpoint = computed(() => {
  let url = props.endpoints.records;
  const params = new URLSearchParams(queryString.value);

  for (const [key, value] of params) {
    if ([perPageParam, 'page'].includes(key)) {
      continue;
    }

    url = kadi.utils.setSearchParam(key, value, false, url);
  }

  return url.toString();
});

let perPage = 6;

function updatePerPage() {
  const params = new URLSearchParams(queryString.value);
  const perPage_ = Number.parseInt(params.get(perPageParam), 10);

  if (perPage_) {
    perPage = Math.max(1, perPage_);
  }
}

watch(queryString, updatePerPage);

onBeforeMount(updatePerPage);
</script>

<template>
  <div>
    <div v-if="template" class="mt-1 mb-2">
      <a target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-primary" :href="newRecordEndpoint">
        {{ $t('New record') }}
      </a>
    </div>

    <div class="w-100">
      <resource-view :title="$t('Records')"
                     :placeholder="$t('No records.')"
                     :endpoint="recordsEndpoint"
                     :per-page="perPage"
                     :show-description="false"
                     :enable-filter="false">
      </resource-view>
    </div>
  </div>
</template>
