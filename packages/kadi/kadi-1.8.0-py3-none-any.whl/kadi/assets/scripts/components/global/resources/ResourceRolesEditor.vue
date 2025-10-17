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
          <li v-for="subject in props.items"
              :key="subject.user ? subject.user.id : subject.group.id"
              class="list-group-item py-1">
            <div class="row align-items-center">
              <div v-if="subject.user" class="col-md-7 mb-2 mb-md-0">
                <identity-popover :user="subject.user"></identity-popover>
                <br>
                <small>@{{ subject.user.identity.username }}</small>
              </div>
              <div v-if="subject.group" class="col-md-7 mb-2 mb-md-0">
                <component :is="subject.group._links ? 'a' : 'div'"
                           :href="subject.group._links ? subject.group._links.view : ''"
                           :class="{'text-muted': !subject.group._links}">
                  <basic-resource-info :resource="subject.group" :show-description="false"></basic-resource-info>
                </component>
              </div>
              <div class="col-md-4 mb-2 mb-md-0">
                <div class="input-group input-group-sm">
                  <div class="input-group-prepend">
                    <span class="input-group-text">{{ $t('Role') }}</span>
                  </div>
                  <select v-model="subject.role.name"
                          class="custom-select"
                          :disabled="subject.disabled"
                          @change="changeRole(subject)">
                    <option v-for="role in roles" :key="role.name" :value="role.name">
                      {{ kadi.utils.capitalize(role.name) }}
                    </option>
                  </select>
                </div>
              </div>
              <div class="col-md-1 mb-2 mb-lg-0 d-md-flex justify-content-end">
                <button type="button"
                        class="btn btn-sm btn-danger"
                        :title="$t('Remove role')"
                        :disabled="subject.disabled"
                        @click="removeRole(subject)">
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
    roles: Array,
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
    async changeRole(subject) {
      subject.disabled = true;

      try {
        await axios.patch(subject._actions.change, {name: subject.role.name});

        kadi.base.flashSuccess($t('Role changed successfully.'));
      } catch (error) {
        kadi.base.flashDanger($t('Error changing role.'), error.request);
      } finally {
        subject.disabled = false;
      }
    },
    async removeRole(subject) {
      const input = await this.$refs.dialog.open($t('Are you sure you want to remove this role?'));

      if (!input.status) {
        return;
      }

      subject.disabled = true;

      try {
        await axios.delete(subject._actions.remove);

        this.$refs.pagination.update();
        kadi.base.flashSuccess($t('Role removed successfully.'));
      } catch (error) {
        kadi.base.flashDanger($t('Error removing role.'), error.request);
        subject.disabled = false;
      }
    },
  },
};
</script>
