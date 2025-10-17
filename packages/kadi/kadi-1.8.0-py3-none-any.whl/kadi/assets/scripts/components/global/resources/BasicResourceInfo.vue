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
    <div v-trim-ws class="d-flow-root">
      <small>
        <resource-visibility :visibility="resource.visibility"></resource-visibility>
      </small>
      <strong class="text-break ml-2">{{ resource.title }}</strong>
    </div>
    <small class="text-break">@{{ resource.identifier }}</small>
    <div v-if="showDescription">
      <small v-if="resource.plain_description" class="text-muted">
        {{ kadi.utils.truncate(resource.plain_description, 100) }}
      </small>
      <small v-else class="text-muted">
        <em>{{ $t('No description.') }}</em>
      </small>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    resource: Object,
    showDescription: {
      type: Boolean,
      default: true,
    },
  },
};
</script>
