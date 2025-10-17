<!-- Copyright 2022 Karlsruhe Institute of Technology
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
  <div class="form-group">
    <label class="form-control-label">{{ field.label }}</label>
    <div class="card">
      <div class="card-body p-2">
        <vue-draggable item-key="resource" handle=".sort-handle" :list="currentLayout" :force-fallback="true">
          <template #item="{element: resourceConfig, index}">
            <div class="border rounded bg-light p-2" :class="{'mb-2': index < currentLayout.length - 1}">
              <div class="form-row">
                <div class="col-sm-6 mb-2 mb-sm-0">
                  <button type="button" class="btn btn-sm btn-light disabled sort-handle">
                    <i class="fa-solid fa-bars"></i>
                  </button>
                  <strong class="ml-1">{{ resourceTypes[resourceConfig.resource] }}</strong>
                </div>
                <div class="col-sm-6 d-sm-flex justify-content-end">
                  <small>
                    {{ $t('Maximum amount of resources') }}: {{ resourceConfig.max_items }}
                    <range-slider :max="10"
                                  :step="2"
                                  :initial-value="resourceConfig.max_items"
                                  @input="resourceConfig.max_items = $event">
                    </range-slider>
                  </small>
                </div>
              </div>
              <hr class="mt-1 mb-2">
              <div class="form-row">
                <div class="col-md-4 mb-2 mb-md-0">
                  <div class="input-group input-group-sm">
                    <div class="input-group-prepend">
                      <span class="input-group-text">{{ $t('Creator') }}</span>
                    </div>
                    <select v-model="resourceConfig.creator" class="custom-select">
                      <option v-for="creator in creatorTypes" :key="creator.key" :value="creator.key">
                        {{ creator.title }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="col-md-4 mb-2 mb-md-0">
                  <div class="input-group input-group-sm">
                    <div class="input-group-prepend">
                      <span class="input-group-text">{{ $t('Visibility') }}</span>
                    </div>
                    <select v-model="resourceConfig.visibility" class="custom-select">
                      <option v-for="visibility in visibilityTypes" :key="visibility.key" :value="visibility.key">
                        {{ visibility.title }}
                      </option>
                    </select>
                  </div>
                </div>
                <div class="col-md-4 d-flex align-items-center">
                  <div class="form-check">
                    <input :id="`permissions-${index}-${suffix}`"
                           v-model="resourceConfig.explicit_permissions"
                           type="checkbox"
                           class="form-check-input">
                    <label class="form-check-label" :for="`permissions-${index}-${suffix}`">
                      <span v-if="resourceConfig.resource === 'group'">
                        {{ $t('Only consider groups with membership') }}
                      </span>
                      <span v-else>{{ $t('Only consider explicit permissions') }}</span>
                    </label>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </vue-draggable>
      </div>
    </div>
    <small class="form-text text-muted">{{ field.description }}</small>
    <input type="hidden" :name="field.name" :value="serializedLayout">
  </div>
</template>

<style scoped>
.sort-handle {
  width: 50px;
}
</style>

<script>
import VueDraggable from 'vuedraggable';

export default {
  components: {
    VueDraggable,
  },
  props: {
    field: Object,
  },
  data() {
    return {
      suffix: kadi.utils.randomAlnum(),
      currentLayout: [],
      resourceTypes: {
        record: $t('Records'),
        collection: $t('Collections'),
        template: $t('Templates'),
        group: $t('Groups'),
      },
      visibilityTypes: [
        {key: 'all', title: $t('All')},
        {key: 'private', title: $t('Private')},
        {key: 'public', title: $t('Public')},
      ],
      creatorTypes: [
        {key: 'any', title: $t('Any')},
        {key: 'self', title: $t('Self')},
      ],
      defaultResourceOrder: ['record', 'collection', 'template', 'group'],
      defaultResourceConfig: {max_items: 0, creator: 'any', visibility: 'all', explicit_permissions: false},
    };
  },
  computed: {
    serializedLayout() {
      return JSON.stringify(this.currentLayout);
    },
  },
  mounted() {
    // Determine the initial layout settings based on the field data and the default resource config.
    const currentResourceTypes = [];

    for (const resourceConfig of this.field.data) {
      if (!currentResourceTypes.includes(resourceConfig.resource)) {
        // Accommodate for properties that were added later on.
        for (const [prop, defaultValue] of Object.entries(this.defaultResourceConfig)) {
          if (!(prop in resourceConfig)) {
            resourceConfig[prop] = defaultValue;
          }
        }

        this.currentLayout.push(resourceConfig);
        currentResourceTypes.push(resourceConfig.resource);
      }
    }
    for (const resourceType of this.defaultResourceOrder) {
      if (!currentResourceTypes.includes(resourceType)) {
        this.currentLayout.push({resource: resourceType, ...this.defaultResourceConfig});
      }
    }
  },
};
</script>
