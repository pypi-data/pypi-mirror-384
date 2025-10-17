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
    <confirm-dialog ref="dialog"></confirm-dialog>
    <dynamic-pagination ref="pagination"
                        :endpoint="endpoint"
                        :placeholder="placeholder"
                        :per-page="perPage"
                        :enable-filter="enableFilter">
      <template #default="props">
        <p>
          <strong>{{ title }}</strong>
          <span class="badge-total">{{ props.total }}</span>
        </p>
        <ul class="list-group">
          <li v-for="resource in props.items" :key="resource.id" class="list-group-item py-1">
            <div class="row align-items-center">
              <div class="col-md-10 mb-2 mb-md-0">
                <a :href="resource._links.view">
                  <basic-resource-info :resource="resource" :show-description="false"></basic-resource-info>
                </a>
              </div>
              <div class="col-md-2 mb-2 mb-lg-0 d-md-flex justify-content-end">
                <button type="button"
                        class="btn btn-sm btn-danger"
                        :title="$t('Remove link')"
                        :disabled="resource.disabled"
                        @click="removeLink(resource)">
                  <i class="fa-solid fa-trash"></i>
                </button>
              </div>
            </div>
          </li>
        </ul>
      </template>
    </dynamic-pagination>
  </div>
</template>

<script>
export default {
  props: {
    title: String,
    placeholder: String,
    endpoint: String,
    perPage: {
      type: Number,
      default: 5,
    },
    enableFilter: {
      type: Boolean,
      default: true,
    },
  },
  methods: {
    async removeLink(resource) {
      const input = await this.$refs.dialog.open($t('Are you sure you want to remove this link?'));

      if (!input.status) {
        return;
      }

      resource.disabled = true;

      try {
        await axios.delete(resource._actions.remove_link);

        this.$refs.pagination.update();
        kadi.base.flashSuccess($t('Link removed successfully.'));
      } catch (error) {
        kadi.base.flashDanger($t('Error removing link.'), error.request);
        resource.disabled = false;
      }
    },
  },
};
</script>
