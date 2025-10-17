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
  <popover-toggle v-if="roles.length > 0" :toggle-class="toggleClasses" :title="$t('Roles')">
    <template #toggle>
      <i class="fa-solid fa-circle-info"></i> {{ $t('Roles') }}
    </template>
    <template #content>
      <div v-for="(role, index) in roles" :key="role.name">
        <strong>{{ kadi.utils.capitalize(role.name) }}</strong>
        <br>
        <div v-for="permission in role.permissions" :key="permission.action" class="row">
          <div class="col-3">{{ permission.action }}</div>
          <div class="col-9">
            <small>{{ permission.description }}</small>
          </div>
        </div>
        <hr v-if="index < roles.length - 1">
      </div>
    </template>
  </popover-toggle>
</template>

<script>
export default {
  props: {
    roles: Array,
    smallLayout: {
      type: Boolean,
      default: false,
    },
  },
  computed: {
    toggleClasses() {
      const baseClasses = 'btn btn-light';
      return this.smallLayout ? `${baseClasses} btn-sm` : baseClasses;
    },
  },
};
</script>
