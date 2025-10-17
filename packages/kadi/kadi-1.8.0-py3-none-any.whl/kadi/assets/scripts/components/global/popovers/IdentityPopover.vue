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
  <span v-trim-ws>
    <popover-toggle toggle-class="" placement="top" trigger="hover" :width="315">
      <template #toggle>
        <a :href="user._links.view"
           :target="openInNewTab ? '_blank' : null"
           :rel="openInNewTab ? 'noopener noreferrer' : null">
          <slot :user="user">
            <strong>{{ kadi.utils.truncate(user.displayname, 50) }}</strong>
          </slot>
        </a>
      </template>
      <template #content>
        <span class="row">
          <span v-if="user._links.image" class="col-4">
            <img class="img-max-75 img-thumbnail" :src="user._links.image">
          </span>
          <span :class="{'col-8': user._links.image, 'col-12': !user._links.image}">
            <strong class="text-break">{{ user.displayname }}</strong>
            <br>
            <p class="text-break">@{{ user.identity.username }}</p>
            <span class="text-muted">{{ $t('Account type') }}: {{ user.identity.name }}</span>
          </span>
        </span>
      </template>
    </popover-toggle>
  </span>
</template>

<script>
export default {
  props: {
    user: Object,
    openInNewTab: {
      type: Boolean,
      default: false,
    },
  },
};
</script>
