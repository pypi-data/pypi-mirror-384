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
        <ul v-if="props.total > 0" class="list-group">
          <li v-for="link in props.items" :key="link.id" class="list-group-item py-1">
            <div class="row align-items-center">
              <div class="col-lg-4 mb-2 mb-lg-0">
                <a :href="link._links.view">
                  <strong>{{ link.name }}</strong>
                </a>
              </div>
              <div class="col-lg-5 mb-2 mb-lg-0">
                <a :href="direction === 'out' ? link.record_to._links.view : link.record_from._links.view">
                  <basic-resource-info :resource="direction === 'out' ? link.record_to : link.record_from"
                                       :show-description="false">
                  </basic-resource-info>
                </a>
              </div>
              <div class="col-lg-3 mb-2 mb-lg-0 d-lg-flex justify-content-end">
                <div class="btn-group btn-group-sm">
                  <a class="btn btn-light" :href="link._links.edit">
                    <i class="fa-solid fa-pencil"></i> {{ $t('Edit') }}
                  </a>
                  <button type="button"
                          class="btn btn-danger"
                          :title="$t('Remove link')"
                          :disabled="link.disabled"
                          @click="removeLink(link)">
                    <i class="fa-solid fa-trash"></i>
                  </button>
                </div>
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
    endpoint: String,
    direction: String,
    placeholder: {
      type: String,
      default: $t('No record links.'),
    },
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
    async removeLink(link) {
      const input = await this.$refs.dialog.open($t('Are you sure you want to remove this record link?'));

      if (!input.status) {
        return;
      }

      link.disabled = true;

      try {
        await axios.delete(link._actions.remove);

        this.$refs.pagination.update();
        kadi.base.flashSuccess($t('Record link removed successfully.'));
      } catch (error) {
        kadi.base.flashDanger($t('Error removing record link.'), error.request);
        link.disabled = false;
      }
    },
  },
};
</script>
