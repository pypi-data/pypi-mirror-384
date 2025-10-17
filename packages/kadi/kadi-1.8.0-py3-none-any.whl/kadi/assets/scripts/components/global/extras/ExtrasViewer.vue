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

<script setup>
import {computed, onBeforeMount, ref, watch} from 'vue';

const props = defineProps({
  extras: Array,
  editEndpoint: {
    type: String,
    default: null,
  },
  editQueryParam: {
    type: String,
    default: 'key',
  },
  showToolbar: {
    type: Boolean,
    default: true,
  },
  showInfoToggles: {
    type: Boolean,
    default: false,
  },
  showNullValues: {
    type: Boolean,
    default: true,
  },
  nestedKeys: {
    type: Array,
    default: () => [],
  },
  depth: {
    type: Number,
    default: 0,
  },
});

const extras_ = ref(props.extras);
const serializedExtras = ref('');
const showInfoToggles_ = ref(props.showInfoToggles);
const showNullValues_ = ref(props.showNullValues);
const hasNullValues = ref(false);

const hasNestedType = computed(() => {
  for (const extra of extras_.value) {
    if (kadi.utils.isNestedType(extra.type)) {
      return true;
    }
  }
  return false;
});

const filteredExtras = computed(() => {
  const extras = [];

  for (const extra of extras_.value) {
    if (!extra.isNull || showNullValues_.value) {
      extras.push(extra);
    }
  }

  return extras;
});

const toggleClasses = 'btn btn-sm text-primary py-0 px-0 px-md-2 mx-1';
const validationKeys = {
  required: $t('Required'),
  range: $t('Range'),
  options: $t('Options'),
  iri: 'IRI',
};

function visitExtras(extras, callback) {
  extras.forEach((extra) => {
    callback(extra);

    if (kadi.utils.isNestedType(extra.type)) {
      visitExtras(extra.value, callback);
    }
  });
}

function collapseExtras(collapse) {
  visitExtras(extras_.value, (extra) => extra.isCollapsed = collapse);
}

function getExtraValue(extra) {
  if (['int', 'float'].includes(extra.type)) {
    return kadi.utils.toExponentional(extra.value);
  }

  return extra.value;
}

function getValidationValue(extra, key, value) {
  if (['required', 'iri'].includes(key)) {
    return $t('Yes');
  }

  if (key === 'range') {
    const ranges = [];

    if (value.min !== null) {
      ranges.push(`\u2265 ${kadi.utils.toExponentional(value.min)}`);
    }
    if (value.max !== null) {
      ranges.push(`\u2264 ${kadi.utils.toExponentional(value.max)}`);
    }

    return ranges.join(', ');
  }

  if (key === 'options') {
    const options = [];

    for (const option of value) {
      if (extra.type === 'str') {
        options.push(`"${option}"`);
      } else {
        options.push(kadi.utils.toExponentional(option));
      }
    }

    return options.join(', ');
  }

  return value;
}

function getEditLink(extra, index) {
  let url = props.editEndpoint;

  for (const key of [...props.nestedKeys, extra.key || index]) {
    url = kadi.utils.setSearchParam(props.editQueryParam, key, false, url);
  }

  return url.toString();
}

function isNull(extra) {
  if (kadi.utils.isNestedType(extra.type)) {
    for (const _extra of extra.value) {
      if (!isNull(_extra)) {
        return false;
      }
    }
    return true;
  }

  return extra.value === null;
}

watch(() => props.showNullValues, () => {
  showNullValues_.value = props.showNullValues;
});

onBeforeMount(() => {
  if (!props.nestedKeys.length > 0) {
    // Only perform a deep copy on the top component level.
    extras_.value = kadi.utils.deepClone(props.extras);

    visitExtras(extras_.value, (extra) => {
      extra.id = kadi.utils.randomAlnum();
      extra.isNull = isNull(extra);
      extra.showDetails = false;
      extra.isCollapsed = false;

      if (extra.isNull) {
        hasNullValues.value = true;
      }
      if (extra.validation) {
        showInfoToggles_.value = true;
      }
    });
  }

  serializedExtras.value = JSON.stringify(props.extras, null, 2);
});
</script>

<template>
  <div>
    <div v-if="nestedKeys.length === 0" class="row align-items-center" :class="{'mb-2': showToolbar}">
      <div class="col-sm-4 mb-2 mb-sm-0">
        <slot></slot>
      </div>
      <div v-if="showToolbar" class="col-sm-8 d-sm-flex justify-content-end">
        <div class="btn-group btn-group-sm">
          <button v-if="hasNestedType"
                  type="button"
                  class="btn btn-light"
                  :title="$t('Collapse all')"
                  @click="collapseExtras(true)">
            <i class="fa-regular fa-lg fa-square-minus"></i>
          </button>
          <button v-if="hasNestedType"
                  type="button"
                  class="btn btn-light"
                  :title="$t('Expand all')"
                  @click="collapseExtras(false)">
            <i class="fa-regular fa-lg fa-square-plus"></i>
          </button>
          <clipboard-button class="btn btn-light" :content="serializedExtras" :show-tooltip="false"></clipboard-button>
          <button v-if="hasNullValues"
                  type="button"
                  class="btn btn-light"
                  @click="showNullValues_ = !showNullValues_">
            <span v-if="showNullValues_">
              <i class="fa-solid fa-eye-slash"></i> {{ $t('Hide null values') }}
            </span>
            <span v-else>
              <i class="fa-solid fa-eye"></i> {{ $t('Show null values') }}
            </span>
          </button>
        </div>
      </div>
    </div>
    <ul class="list-group" :class="{'mb-2': depth > 0}">
      <li v-for="(extra, index) in filteredExtras"
          :key="extra.id"
          class="list-group-item extra py-1 pl-3 pr-0"
          :class="{'odd': depth % 2 == 1, 'nested': depth > 0}">
        <div class="row align-items-center"
             :class="{'mb-1': kadi.utils.isNestedType(extra.type) && extra.value.length > 0 && !extra.isCollapsed}">
          <!-- Key. -->
          <div class="col-md-4">
            <span v-if="!kadi.utils.isNestedType(extra.type)">{{ extra.key || `(${index + 1})` }}</span>
            <collapse-item v-if="kadi.utils.isNestedType(extra.type)"
                           :id="extra.id"
                           show-icon-class=""
                           hide-icon-class=""
                           :is-collapsed="extra.isCollapsed"
                           @collapse="extra.isCollapsed = $event">
              <strong>{{ extra.key || `(${index + 1})` }}</strong>
            </collapse-item>
          </div>
          <!-- Value and unit. -->
          <div :class="[editEndpoint || showInfoToggles_ ? 'col-md-5' : 'col-md-6']">
            <div v-if="!kadi.utils.isNestedType(extra.type)">
              <span v-if="extra.value === null">
                <em>null</em>
              </span>
              <span v-else>
                <local-timestamp v-if="extra.type === 'date'" :timestamp="extra.value"></local-timestamp>
                <a v-else-if="extra.validation && extra.validation.iri && kadi.utils.isHttpUrl(extra.value)"
                   v-trim-ws
                   class="text-primary"
                   target="_blank"
                   rel="noopener noreferrer"
                   :href="extra.value">
                  <i class="fa-solid fa-arrow-up-right-from-square fa-sm mr-1"></i>
                  <span>{{ extra.value }}</span>
                </a>
                <span v-else>{{ getExtraValue(extra) }}</span>
              </span>
              <span class="text-muted">{{ extra.unit }}</span>
            </div>
            <collapse-item v-if="kadi.utils.isNestedType(extra.type) && extra.isCollapsed && extra.value.length > 0"
                           :id="extra.id"
                           show-icon-class=""
                           hide-icon-class=""
                           :is-collapsed="extra.isCollapsed"
                           @collapse="extra.isCollapsed = $event">
              <strong>[...]</strong>
            </collapse-item>
          </div>
          <!-- Type. -->
          <div class="col-md-2 d-md-flex justify-content-end">
            <small class="text-muted mr-3">{{ kadi.utils.capitalize(kadi.utils.prettyTypeName(extra.type)) }}</small>
          </div>
          <!-- Edit link and additional information toggle. -->
          <div class="col-md-1 d-md-flex justify-content-end">
            <button v-if="extra.description || extra.term || extra.validation"
                    type="button"
                    class="float-md-right mr-3 mr-md-0"
                    :title="$t('Toggle additional information')"
                    :class="toggleClasses"
                    @click="extra.showDetails = !extra.showDetails">
              <i v-if="extra.showDetails" class="fa-solid fa-angle-up"></i>
              <i v-else class="fa-solid fa-angle-down"></i>
              <span class="d-md-none">{{ $t('Toggle additional information') }}</span>
            </button>
            <br v-if="extra.description || extra.term || extra.validation">
            <a v-if="editEndpoint"
               :title="$t('Edit metadatum')"
               :class="toggleClasses"
               :href="getEditLink(extra, index)">
              <i class="fa-solid fa-pencil"></i>
              <span class="d-md-none">{{ $t('Edit metadatum') }}</span>
            </a>
          </div>
        </div>
        <div v-if="extra.showDetails">
          <div class="card card-body bg-light py-1 px-2 my-1 mr-3">
            <div v-if="extra.description">
              <div class="row my-2 my-sm-0">
                <small class="col-sm-4">
                  <em>{{ $t('Description') }}</em>
                </small>
                <small class="col-sm-8">
                  <span class="ws-pre-wrap">{{ extra.description }}</span>
                </small>
              </div>
            </div>
            <div v-if="extra.term">
              <hr v-if="extra.description" class="my-1">
              <div class="row my-2 my-sm-0">
                <small class="col-sm-4">
                  <em>{{ $t('Term IRI') }}</em>
                </small>
                <small class="col-sm-8">
                  <a v-if="kadi.utils.isHttpUrl(extra.term)"
                     v-trim-ws
                     class="text-primary"
                     target="_blank"
                     rel="noopener noreferrer"
                     :href="extra.term">
                    <i class="fa-solid fa-arrow-up-right-from-square mr-1"></i>
                    <span>{{ extra.term }}</span>
                  </a>
                  <span v-else>{{ extra.term }}</span>
                </small>
              </div>
            </div>
            <div v-if="extra.validation">
              <hr v-if="extra.description || extra.term" class="my-1">
              <div v-for="(value, key) in extra.validation" :key="key" class="row my-2 my-sm-0">
                <small class="col-sm-4">
                  <em>{{ $t('Validation') }} ({{ validationKeys[key] || key }})</em>
                </small>
                <small class="col-sm-8">{{ getValidationValue(extra, key, value) }}</small>
              </div>
            </div>
          </div>
        </div>
        <div v-if="kadi.utils.isNestedType(extra.type) && extra.value.length > 0">
          <div :id="extra.id">
            <extras-viewer :extras="extra.value"
                           :edit-endpoint="editEndpoint"
                           :show-info-toggles="showInfoToggles_"
                           :show-null-values="showNullValues_"
                           :nested-keys="[...nestedKeys, extra.key || index]"
                           :depth="depth + 1">
            </extras-viewer>
          </div>
        </div>
      </li>
    </ul>
  </div>
</template>

<style lang="scss" scoped>
.extra {
  margin-right: -1px;
  min-width: 150px;

  &.nested {
    border-bottom-right-radius: 0;
    border-top-right-radius: 0;
  }

  &.odd {
    background-color: #f2f2f2;
  }
}
</style>
