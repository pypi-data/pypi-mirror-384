<!-- Copyright 2022 Karlsruhe Institute of Technology
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
import {onBeforeMount, onMounted, ref, watch} from 'vue';

const props = defineProps({
  maxItems: {
    type: Number,
    default: 5,
  },
});

const items = ref([]);
const collapsed = ref(false);

let initialized = false;

const id = kadi.utils.randomAlnum();
const itemsStorageKey = 'recently_visited_items';
const collapseStorageKey = 'recently_visited_collapse';

const itemTypes = {
  record: $t('Record'),
  collection: $t('Collection'),
  template: $t('Template'),
  group: $t('Group'),
};

function addItem(type, title, identifier, endpoint, timestamp = null) {
  const item = {
    id: kadi.utils.randomAlnum(),
    timestamp: timestamp || new Date().toISOString(),
    type,
    title,
    identifier,
    endpoint,
  };

  // If an item already exists, it will be removed at first and then added again, with potentially updated values. We
  // simply use the endpoint as a unique identification of an item.
  const index = items.value.findIndex((el) => el.endpoint === endpoint);

  if (index !== -1) {
    items.value.splice(index, 1);
  }

  // Add items in order when initializing and to the front otherwise.
  if (!initialized) {
    items.value.push(item);
  } else {
    items.value.unshift(item);
  }

  items.value = items.value.slice(0, props.maxItems);

  if (initialized) {
    const results = [];

    for (const item of items.value) {
      const newItem = {...item};
      delete newItem.id;
      results.push(newItem);
    }

    window.localStorage.setItem(itemsStorageKey, JSON.stringify(results));
  }
}

function clearItems() {
  items.value = [];
  window.localStorage.removeItem(itemsStorageKey);
}

watch(collapsed, () => {
  if (collapsed.value) {
    window.localStorage.setItem(collapseStorageKey, 'true');
  } else {
    window.localStorage.removeItem(collapseStorageKey);
  }
});

onBeforeMount(() => {
  if (kadi.globals.userActive) {
    if (window.localStorage.getItem(collapseStorageKey)) {
      collapsed.value = true;
    } else {
      collapsed.value = false;
    }
  }
});

onMounted(() => {
  if (!kadi.globals.userActive) {
    // Clear all items for non-active users.
    clearItems();
  } else {
    try {
      const items = JSON.parse(window.localStorage.getItem(itemsStorageKey));

      for (const item of items) {
        addItem(item.type, item.title, item.identifier, item.endpoint, item.timestamp);
      }
    } catch {
      clearItems();
    }

    initialized = true;
  }
});

defineExpose({
  addItem,
});
</script>

<template>
  <div v-show="items.length > 0" v-if="kadi.globals.userActive" class="card">
    <div class="card-header py-1" :class="{'border-bottom-0': collapsed}">
      <collapse-item :id="id"
                     class="text-default stretched-link d-flex align-items-center"
                     :is-collapsed="collapsed"
                     @collapse="collapsed = $event">
        <div class="d-inline-flex justify-content-between align-items-center flex-grow-1">
          <strong class="mx-1">{{ $t('Recently visited') }}</strong>
          <button type="button" class="close text-default elevated" @click.stop="clearItems">
            <i class="fa-solid fa-xmark fa-xs"></i>
          </button>
        </div>
      </collapse-item>
    </div>
    <div :id="id" class="card-body items">
      <div class="list-group list-group-flush">
        <div v-for="item in items" :key="item.id" class="list-group-item list-group-item-action">
          <a class="text-default stretched-link" :href="item.endpoint">
            <span class="badge badge-light border font-weight-normal float-right ml-3">
              {{ itemTypes[item.type] || item.type }}
            </span>
            <div class="d-flow-root">
              <strong class="font-title elevated" :title="item.title">{{ kadi.utils.truncate(item.title, 50) }}</strong>
            </div>
            <div class="font-identifier">@{{ item.identifier }}</div>
            <div class="text-muted font-timestamp mt-1">
              {{ $t('Last visited') }} <from-now :timestamp="item.timestamp"></from-now>
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.font-identifier {
  font-size: 90%;
}

.font-timestamp {
  font-size: 80%;
}

.font-title {
  font-size: 95%;
}

.items {
  padding: 0 0 1px 0;
}

.type {
  @media (min-width: 1200px) and (max-width: 1500px) {
    display: none;
  }
}
</style>
