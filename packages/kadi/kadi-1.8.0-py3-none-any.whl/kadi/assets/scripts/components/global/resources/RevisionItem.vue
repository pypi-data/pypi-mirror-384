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
    <div class="row">
      <div class="col-md-6 mb-2 mb-md-0">
        <button type="button" class="btn btn-sm btn-light" :disabled="!showDiff" @click="toggleComparison">
          <i class="fa-solid fa-repeat"></i>
          <span v-if="compareLatest_">{{ $t('Compare to previous revision') }}</span>
          <span v-else>{{ $t('Compare to current state') }}</span>
        </button>
      </div>
      <div class="col-md-6 d-md-flex justify-content-end">
        <div>
          <button type="button" class="btn btn-sm btn-light" @click="toggleDiff">
            <span v-if="showDiff">
              <i class="fa-solid fa-eye"></i> {{ $t('Show current revision') }}
            </span>
            <span v-else>
              <i class="fa-solid fa-code-compare"></i> {{ $t('Show changes') }}
            </span>
          </button>
        </div>
      </div>
    </div>
    <hr>
    <div v-if="!loading">
      <div class="row mb-2">
        <div class="col-md-3">{{ $t('Persistent ID') }}</div>
        <div class="col-md-9">{{ revision.id }}</div>
      </div>
      <div v-if="revision._links.view_object" class="row mb-2">
        <div class="col-md-3">{{ $t('Object ID') }}</div>
        <div class="col-md-9">
          <a :href="revision._links.view_object">
            <strong>{{ revision.object_id }}</strong>
          </a>
        </div>
      </div>
      <div class="row mb-2">
        <div class="col-md-3">{{ $t('User') }}</div>
        <div class="col-md-9">
          <identity-popover v-if="revision.user" :user="revision.user"></identity-popover>
          <em v-else class="text-muted">{{ $t('No user.') }}</em>
        </div>
      </div>
      <div class="row">
        <div class="col-md-3">{{ $t('Timestamp') }}</div>
        <div class="col-md-9">
          <local-timestamp :timestamp="revision.timestamp"></local-timestamp>
          <br>
          <small class="text-muted">
            (<from-now :timestamp="revision.timestamp"></from-now>)
          </small>
        </div>
      </div>
      <hr>
      <div v-if="showDiff">
        <div class="card bg-light mb-3">
          <div class="card-body py-2">
            <i class="fa-solid fa-circle-info"></i>
            <small>
              <strong v-if="compareLatest_">{{ $t('Comparing to current state') }}</strong>
              <strong v-else>{{ $t('Comparing to previous revision') }}</strong>
            </small>
          </div>
        </div>
      </div>
      <em v-if="showDiff && !hasDiff()" class="text-muted">{{ $t('No changes.') }}</em>
      <div v-for="(value, prop) in revision.data" :key="prop">
        <div v-if="!showDiff || hasDiff(prop)">
          <div class="row mt-3">
            <div class="col-md-3">
              <strong>{{ revisionProp(prop) }}</strong>
            </div>
            <div class="col-md-9">
              <clipboard-button v-if="!showDiff" class="btn-sm clipboard-btn" :content="revisionClipboardValue(value)">
              </clipboard-button>
              <div class="bg-light rounded p-2">
                <pre v-if="showDiff" class="revision-content"><!--
               --><div v-for="(part, partIndex) in getDiff(prop)"
                       :key="partIndex"
                       :class="{'font-italic': part.value === null}"><!--
                 --><div v-if="part.added" class="revision-diff add">{{ revisionValue(part.value) }}</div><!--
                 --><div v-else-if="part.removed" class="revision-diff delete">{{ revisionValue(part.value) }}</div><!--
                 --><div v-else>{{ revisionValue(part.value) }}</div><!--
               --></div><!--
             --></pre>
                <div v-else>
                  <pre class="revision-content" :class="{'font-italic': value === null}"><!--
                 -->{{ revisionValue(value) }}<!--
               --></pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <i v-if="loading" class="fa-solid fa-circle-notch fa-spin"></i>
  </div>
</template>

<style scoped>
.clipboard-btn {
  position: absolute;
  right: 1.5rem;
  top: 0.5rem;
}

.revision-content {
  display: flex;
  flex-direction: column;
  justify-content: center;
  margin-bottom: 0;
  min-height: calc(15px + 1rem);
}

.revision-diff {
  border-radius: 0.25rem;
  margin-bottom: 0.1rem;
  margin-top: 0.1rem;
  min-width: 100%;
  padding-bottom: 0.25rem;
  padding-top: 0.25rem;
  width: fit-content;

  &.add {
    background-color: #ecfdf0;
    color: #009933;
  }

  &.delete {
    background-color: #fbe9eb;
    color: #d00928;
  }
}
</style>

<script>
import {diffJson} from 'diff';

export default {
  props: {
    endpoint: String,
    latestRevision: Number,
    compareLatest: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      revision: null,
      loading: true,
      showDiff: true,
      compareLatest_: this.compareLatest,
    };
  },
  mounted() {
    this.loadRevision();
  },
  methods: {
    revisionProp(prop) {
      return kadi.utils.capitalize(prop).split('_').join(' ');
    },
    revisionValue(value) {
      return value === null ? 'null' : value;
    },
    revisionClipboardValue(value) {
      if (typeof value === 'string') {
        return value;
      }

      return JSON.stringify(value, null, 2);
    },
    hasDiff(prop = null) {
      if (prop === null) {
        return Object.keys(this.revision.diff).length > 0;
      }

      return prop in this.revision.diff;
    },
    getDiff(prop) {
      let revisionData = this.revision.data[prop];

      if (this.hasDiff(prop)) {
        let diffData = this.revision.diff[prop];

        // When comparing to the latest state, we need to switch the diff around.
        if (this.compareLatest_) {
          [revisionData, diffData] = [diffData, revisionData];
        }

        // As null values are converted into strings when using 'diffJson', we handle this case separately instead in
        // order to visualize null values differently.
        if ([revisionData, diffData].includes(null)) {
          return [
            {removed: true, value: diffData},
            {added: true, value: revisionData},
          ];
        }

        return diffJson(diffData, revisionData);
      }

      return [{value: revisionData}];
    },
    async loadRevision() {
      this.loading = true;

      const config = {};

      if (this.compareLatest_ && this.latestRevision) {
        config.params = {revision: this.latestRevision};
      }

      try {
        const response = await axios.get(this.endpoint, config);

        this.revision = response.data;
        this.loading = false;
      } catch (error) {
        kadi.base.flashDanger($t('Error loading revision.'), error.request);
      }
    },
    toggleComparison() {
      this.compareLatest_ = !this.compareLatest_;
      this.loadRevision();
    },
    toggleDiff() {
      this.showDiff = !this.showDiff;
    },
  },
};
</script>
