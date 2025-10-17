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
  <div class="form-group">
    <label class="form-control-label">{{ field.label }}</label>
    <vue-draggable handle=".sort-handle" :item-key="(item) => items.indexOf(item)" :list="items" :force-fallback="true">
      <template #item="{element: item, index}">
        <div class="form-row" :class="{'mb-3': index < items.length - 1}">
          <div class="col-md-5 mb-1 mb-md-0">
            <div class="input-group input-group-sm">
              <div class="input-group-prepend">
                <span class="input-group-text">{{ $t('Title') }}</span>
              </div>
              <input v-model.trim="item[0]" class="form-control">
            </div>
          </div>
          <div class="col-md-5 mb-1 mb-md-0">
            <div class="input-group input-group-sm">
              <div class="input-group-prepend">
                <span class="input-group-text">URL</span>
              </div>
              <input v-model.trim="item[1]" class="form-control">
            </div>
          </div>
          <div class="col-md-2 mb-1 mb-md-0">
            <div class="btn-group btn-group-sm w-100">
              <button type="button"
                      class="btn btn-light"
                      :title="$t('Add item')"
                      @click="addItem(index)">
                <i class="fa-solid fa-plus"></i>
              </button>
              <button v-if="items.length > 1"
                      type="button"
                      class="btn btn-light"
                      :title="$t('Remove item')"
                      @click="removeItem(index)">
                <i class="fa-solid fa-xmark"></i>
              </button>
              <span class="btn btn-light disabled sort-handle" tabindex="-1">
                <i class="fa-solid fa-bars"></i>
              </span>
            </div>
          </div>
        </div>
      </template>
    </vue-draggable>
    <small class="form-text text-muted">{{ field.description }}</small>
    <input type="hidden" :name="field.name" :value="serializedItems">
  </div>
</template>

<script>
import VueDraggable from 'vuedraggable';

export default {
  components: {
    VueDraggable,
  },
  props: {
    field: Object,
  },
  data() {
    return {
      items: [],
    };
  },
  computed: {
    serializedItems() {
      const serializedItems = [];

      for (const item of this.items) {
        if (item[0] !== '' || item[1] !== '') {
          serializedItems.push(item);
        }
      }

      return JSON.stringify(serializedItems);
    },
  },
  mounted() {
    if (this.field.data.length > 0) {
      for (const item of this.field.data) {
        this.addItem(null, item);
      }
    } else {
      this.addItem();
    }
  },
  methods: {
    addItem(index = null, item = null) {
      const newItem = item !== null ? item : ['', ''];
      kadi.utils.addToArray(this.items, newItem, index);
    },
    removeItem(index) {
      this.items.splice(index, 1);
    },
  },
};
</script>
