<!-- Copyright 2023 Karlsruhe Institute of Technology
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
    <em v-if="scopes.length === 0">{{ $t('None') }}</em>
    <div v-else>
      <pre class="ws-pre-wrap mb-0">{{ truncatedScopes }}</pre>
      <popover-toggle title="Scopes" toggle-class="" :width="200">
        <template #toggle>
          <strong>{{ scopesToggleText }}</strong>
        </template>
        <template #content>
          <pre class="ws-pre-wrap mb-0">{{ allScopes }}</pre>
        </template>
      </popover-toggle>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    scope: String,
    numScopesShown: {
      type: Number,
      default: 2,
    },
  },
  data() {
    return {
      scopes: [],
    };
  },
  computed: {
    allScopes() {
      return this.scopes.join('\n');
    },
    truncatedScopes() {
      if (this.scopes.length <= this.numScopesShown) {
        return this.allScopes;
      }

      return this.scopes.slice(0, this.numScopesShown).join('\n');
    },
    scopesToggleText() {
      if (this.scopes.length <= this.numScopesShown) {
        return '';
      }

      const numMoreScopes = this.scopes.length - this.numScopesShown;
      return $t('...and {{count}} more', {count: numMoreScopes});
    },
  },
  mounted() {
    if (this.scope !== '') {
      this.scopes = this.scope.split(' ');
    }
  },
};
</script>
