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
  <div class="card">
    <div class="card-header py-2 d-flex justify-content-between align-items-center">
      {{ title }}
      <button v-if="items.length > 0" type="button" class="close text-default" @click="clearItems">
        <i class="fa-solid fa-xmark fa-xs"></i>
      </button>
    </div>
    <div class="card-body p-3">
      <div v-if="items.length > 0" class="mb-3">
        <h5 class="d-inline">
          <span v-for="item in items"
                :key="item.id"
                class="filter-item badge badge-light border font-weight-normal m-1"
                :title="item.text">
            {{ kadi.utils.truncate(item.text, 20) }}
            <button type="button" class="btn btn-link text-muted shadow-none p-0 ml-1" @click="removeItem(item)">
              <i class="fa-solid fa-xmark fa-sm"></i>
            </button>
          </span>
        </h5>
      </div>
      <dynamic-selection v-if="endpoint"
                         container-classes="select2-single-sm"
                         :endpoint="endpoint"
                         :placeholder="placeholder"
                         :reset-on-select="true"
                         @select="addItem">
      </dynamic-selection>
      <div v-else class="input-group input-group-sm" @keydown.enter="enterItem">
        <input v-model="input" class="form-control" :placeholder="placeholder">
        <div class="input-group-append">
          <button type="button" class="input-group-text btn btn-light" @click="enterItem">
            <i class="fa-solid fa-plus"></i>
          </button>
        </div>
      </div>
    </div>
    <slot></slot>
  </div>
</template>

<style lang="scss" scoped>
.filter-item {
  cursor: default;
  white-space: normal;
  word-break: break-all;

  button {
    line-height: 15px;
  }
}
</style>

<script>
export default {
  props: {
    param: String,
    title: String,
    placeholder: {
      type: String,
      default: '',
    },
    endpoint: {
      type: String,
      default: null,
    },
    initialValues: {
      type: Array,
      default: null,
    },
  },
  emits: ['search'],
  data() {
    return {
      input: '',
      items: [],
    };
  },
  mounted() {
    // Always prioritize the given initial values.
    if (this.initialValues !== null) {
      for (const value of this.initialValues) {
        this.addItem({id: value[0], text: value[1]}, false);
      }
    } else if (kadi.utils.hasSearchParam(this.param)) {
      for (const param of kadi.utils.getSearchParam(this.param, true)) {
        this.addItem({id: param, text: param}, false);
      }
    }
  },
  methods: {
    clearItems() {
      const url = kadi.utils.removeSearchParam(this.param);
      kadi.utils.replaceState(url);

      this.items = [];
      this.$emit('search');
    },
    addItem(item, search = true) {
      for (const _item of this.items) {
        if (_item.id === item.id) {
          this.removeItem(item);
          return;
        }
      }

      this.items.push({id: item.id, text: item.text});

      if (search) {
        const url = kadi.utils.setSearchParam(this.param, item.id, false);
        kadi.utils.replaceState(url);
        this.$emit('search');
      }
    },
    enterItem() {
      // We simply assume that normalization will lead to better matching with any dynamically loaded items.
      const input = kadi.utils.normalize(this.input).toLowerCase();

      if (input) {
        this.addItem({id: input, text: input});
        this.input = '';
      }
    },
    removeItem(item) {
      const url = kadi.utils.removeSearchParam(this.param, item.id);
      kadi.utils.replaceState(url);

      let index = 0;

      for (const _item of this.items) {
        if (_item.id === item.id) {
          this.items.splice(index, 1);
          break;
        }
        index++;
      }

      this.$emit('search');
    },
  },
};
</script>
