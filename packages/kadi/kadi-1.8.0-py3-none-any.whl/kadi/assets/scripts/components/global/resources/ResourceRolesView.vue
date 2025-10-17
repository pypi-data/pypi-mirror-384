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
  <dynamic-pagination :endpoint="endpoint" :placeholder="placeholder" :per-page="perPage" :enable-filter="enableFilter">
    <template #default="paginationProps">
      <div class="row">
        <div class="col-md-4">
          <p>
            <strong>{{ title }}</strong>
            <span class="badge-total">{{ paginationProps.total }}</span>
          </p>
        </div>
        <slot></slot>
      </div>
      <card-deck :items="paginationProps.items">
        <template #default="props">
          <div class="card-body py-2">
            <component :is="getLink(props.item) ? 'a' : 'div'"
                       :href="getLink(props.item)"
                       :class="getLinkClass(props.item)">
              <div v-if="props.item.user">
                <img v-if="hasImage(props.item)"
                     class="img-max-75 img-thumbnail float-right ml-3"
                     loading="lazy"
                     :src="props.item.user._links.image">
                <div class="d-flow-root">
                  <strong :title="props.item.user.displayname">
                    {{ kadi.utils.truncate(props.item.user.displayname, 50) }}
                  </strong>
                </div>
                <small>@{{ props.item.user.identity.username }}</small>
                <br>
                <small class="text-muted">{{ $t('Account type') }}: {{ props.item.user.identity.name }}</small>
              </div>
              <div v-if="props.item.group">
                <img v-if="hasImage(props.item)"
                     class="img-max-75 img-thumbnail float-right ml-3"
                     loading="lazy"
                     :src="props.item.group._links.image">
                <basic-resource-info :resource="props.item.group"></basic-resource-info>
              </div>
            </component>
          </div>
          <div class="card-footer d-flex justify-content-between align-items-center py-1">
            <strong class="text-primary">{{ kadi.utils.capitalize(props.item.role.name) }}</strong>
            <span v-if="props.item.user && creator === props.item.user.id"
                  class="badge badge-light border font-weight-normal">
              {{ $t('Creator') }}
            </span>
          </div>
        </template>
      </card-deck>
    </template>
  </dynamic-pagination>
</template>

<script>
export default {
  props: {
    title: String,
    placeholder: String,
    endpoint: String,
    creator: {
      type: Number,
      default: null,
    },
    perPage: {
      type: Number,
      default: 6,
    },
    enableFilter: {
      type: Boolean,
      default: true,
    },
  },
  methods: {
    getLink(item) {
      return item.user ? item.user._links.view : (item.group._links ? item.group._links.view : '');
    },
    getLinkClass(item) {
      return (item.group && !item.group._links) ? 'text-muted' : 'text-default stretched-link';
    },
    hasImage(item) {
      if (item.user) {
        return Boolean(item.user._links.image);
      }
      return Boolean(item.group._links && item.group._links.image);
    },
  },
};
</script>
