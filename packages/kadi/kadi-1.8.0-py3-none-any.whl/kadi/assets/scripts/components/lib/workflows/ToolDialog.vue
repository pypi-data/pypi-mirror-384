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

<template>
  <modal-dialog ref="dialog" title="Add tools">
    <template #body>
      <dynamic-pagination placeholder="No tools."
                          filter-placeholder="Filter by filename or record identifier"
                          :endpoint="endpoint"
                          :per-page="5"
                          :enable-filter="true">
        <template #default="props">
          <ul v-if="props.total > 0" class="list-group">
            <li class="list-group-item bg-light py-2">
              <div class="row">
                <div class="col-lg-5">Tool</div>
                <div class="col-lg-5">File</div>
              </div>
            </li>
            <li v-for="item in props.items" :key="item.id" class="list-group-item py-2">
              <div class="row align-items-center">
                <div class="col-lg-5 mb-2 mb-lg-0">
                  <div v-if="item.tool">
                    <span class="badge badge-pill font-weight-normal badge-mt-minus mr-1"
                          :class="`tool-${item.tool.type}`">
                      {{ kadi.utils.capitalize(item.tool.type) }}
                    </span>
                    <strong>{{ item.tool.name }}</strong>
                    <span v-if="item.tool.version">
                      <br>
                      Version {{ item.tool.version }}
                    </span>
                  </div>
                  <div v-else>
                    <em class="text-muted">Invalid tool specification.</em>
                  </div>
                </div>
                <div class="col-lg-5 mb-2 mb-lg-0">
                  <strong>{{ item.file }}</strong>
                  <br>
                  @{{ item.record }}
                </div>
                <div class="col-lg-2 d-lg-flex justify-content-end">
                  <div>
                    <button type="button"
                            class="btn btn-light btn-sm"
                            title="Add tool"
                            :disabled="!item.tool"
                            @click="addTool(item.tool)">
                      <i class="fa-solid fa-plus"></i>
                    </button>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </template>
      </dynamic-pagination>
    </template>
  </modal-dialog>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/vars.scss';

.tool-env {
  background-color: $bg-env;
  color: white;
}

.tool-program {
  background-color: $bg-program;
  color: white;
}
</style>

<script>
export default {
  props: {
    endpoint: String,
  },
  emits: ['add-tool'],
  methods: {
    open() {
      this.$refs.dialog.open();
    },
    addTool(tool) {
      this.$emit('add-tool', tool);
    },
  },
};
</script>
