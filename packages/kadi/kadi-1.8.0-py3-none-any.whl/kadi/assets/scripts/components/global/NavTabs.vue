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
    <div class="card-header">
      <ul class="nav nav-tabs nav-fill card-header-tabs">
        <li v-for="tab in tabs" :key="tab" class="nav-item">
          <span :ref="`${tab}-trigger`" class="nav-link px-2" :data-target="`#${tab}-tab`" @click="changeTab(tab)">
            <slot :name="`${tab}-head`"></slot>
          </span>
        </li>
      </ul>
    </div>
    <div class="card-body">
      <div class="tab-content">
        <div v-for="tab in tabs" :id="`${tab}-tab`" :key="tab" class="tab-pane">
          <div v-if="tab in loadedTabs">
            <slot :name="`${tab}-body`"></slot>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    tabs: Array,
    tabParam: {
      type: String,
      default: 'tab',
    },
  },
  emits: ['change-tab'],
  data() {
    return {
      loadedTabs: {},
    };
  },
  mounted() {
    let currentTab = this.tabs[0];
    const currentParam = kadi.utils.getSearchParam(this.tabParam);

    for (const tab of this.tabs) {
      if (tab === currentParam) {
        currentTab = tab;
      }

      // Wait until the tab is actually shown before emitting the event.
      $(this.$refs[`${tab}-trigger`]).on('shown.bs.tab', () => {
        this.$emit('change-tab', tab);
      });
    }

    this.showTab(currentTab);
  },
  unmounted() {
    for (const tab of Object.values(this.loadedTabs)) {
      tab.tab('dispose');
    }
  },
  methods: {
    showTab(tab) {
      this.loadedTabs[tab] = $(this.$refs[`${tab}-trigger`]).tab('show');
    },
    changeTab(tab) {
      if (!this.tabs.includes(tab)) {
        return;
      }

      const url = kadi.utils.setSearchParam(this.tabParam, tab);
      kadi.utils.replaceState(url);

      this.showTab(tab);
    },
  },
};
</script>
