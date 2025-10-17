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
  <div ref="menu" class="menu" @pointerdown.stop @wheel.stop>
    <search-bar v-if="searchBar" @filter="filter = $event"></search-bar>
    <item v-for="item in filteredItems" :key="item.key" :item="item" @hide="onHide"></item>
  </div>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/menu.scss';

.menu {
  border: 1px solid $context-menu-border-color;
  border-radius: $context-menu-radius;
}
</style>

<script>
import Item from 'Item.vue';
import Search from 'Search.vue';

function extractLeafs(items) {
  const leafs = [];

  for (const item of items) {
    if (item.subitems) {
      leafs.push(...extractLeafs(item.subitems));
    } else {
      leafs.push(item);
    }
  }

  return leafs;
}

export default {
  components: {
    Item,
    SearchBar: Search,
  },
  props: {
    items: Array,
    searchBar: Boolean,
    onHide: Function,
  },
  data() {
    return {
      filter: '',
      maxItems: 5,
    };
  },
  computed: {
    filteredItems() {
      if (!this.filter) {
        return this.items;
      }

      const regex = new RegExp(this.filter, 'i');
      const items = [];

      for (const item of extractLeafs(this.items)) {
        if (item.label.match(regex)) {
          if (items.length === this.maxItems) {
            items.push({
              key: kadi.utils.randomAlnum(),
              label: 'Show more...',
              class: 'font-italic',
              keepOpen: true,
              handler: () => this.maxItems += 5,
            });
            break;
          }

          items.push(item);
        }
      }

      return items;
    },
  },
  watch: {
    filter() {
      this.maxItems = 5;
    },
  },
  mounted() {
    // The container element of the menu is created separately.
    this.$el.parentNode.style.zIndex = 1000;
    this.fitViewport();
  },
  updated() {
    this.fitViewport();
  },
  methods: {
    fitViewport() {
      const parentNode = this.$el.parentNode;

      const currX = Number.parseFloat(parentNode.style.left, 10);
      const currY = Number.parseFloat(parentNode.style.top, 10);

      const newX = Math.min(currX, window.innerWidth - this.$refs.menu.clientWidth - 5);
      const newY = Math.min(currY, window.innerHeight - this.$refs.menu.clientHeight - 5);

      parentNode.style.left = `${newX}px`;
      parentNode.style.top = `${newY}px`;
    },
  },
};
</script>
