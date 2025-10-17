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

<script setup>
import {computed, nextTick, onMounted, ref, watch} from 'vue';

import VueDraggable from 'vuedraggable';

const props = defineProps({
  type: String,
  convertValue: Function,
  initialValidation: {
    type: Object,
    default: () => ({}),
  },
});

const emit = defineEmits(['validate']);

const required = ref(false);
const range = ref({min: null, max: null});
const options = ref([]);
const iri = ref(false);

const isNumericType = computed(() => ['int', 'float'].includes(props.type));

let initialized = false;

function updateValidation() {
  if (!initialized) {
    return;
  }

  if (kadi.utils.isNestedType(props.type)) {
    emit('validate', null);
    return;
  }

  const validation = {
    required: required.value,
  };

  if (isNumericType.value) {
    validation.range = {min: range.value.min, max: range.value.max};
  }

  if (['str', 'int', 'float'].includes(props.type)) {
    validation.options = [];

    for (const option of options.value) {
      if (option.value !== null) {
        validation.options.push(option.value);
      }
    }
  }

  if (props.type === 'str') {
    validation.iri = iri.value;
  }

  emit('validate', validation);
}

async function changeRange(prop, value, updateValidation_ = true) {
  const prevValue = range.value[prop];
  // Set the value to the given value as is first, as otherwise the view is not updated correctly if the converted value
  // is the same as before.
  range.value[prop] = value;

  await nextTick();

  const newValue = props.convertValue(value);
  range.value[prop] = newValue;

  if (updateValidation_ && prevValue !== newValue) {
    updateValidation();
  }
}

function getOptionValue(option) {
  if (isNumericType.value) {
    return kadi.utils.toExponentional(option.value);
  }

  return option.value;
}

function addOption(option = null, index = null) {
  const newOption = {
    id: kadi.utils.randomAlnum(),
    value: props.convertValue(option),
  };

  kadi.utils.addToArray(options.value, newOption, index);
}

function removeOption(index) {
  const option = options.value.splice(index, 1)[0];

  if (option.value !== null) {
    updateValidation();
  }
}

async function changeOption(option, value, updateValidation_ = true) {
  const prevValue = option.value;
  // See comment in 'changeRange'.
  option.value = value;

  await nextTick();

  let newValue = props.convertValue(value);
  // Check if this option already exists and reset the new value if so.
  const index = options.value.findIndex((o) => o.value === newValue && o.id !== option.id);

  if (index !== -1) {
    newValue = null;
  }

  option.value = newValue;

  if (updateValidation_ && prevValue !== newValue) {
    updateValidation();
  }
}

function endDrag(e) {
  if (e.oldIndex !== e.newIndex) {
    updateValidation();
  }
}

watch(() => props.type, () => {
  for (const option of options.value) {
    changeOption(option, option.value, false);
  }
  for (const prop of ['min', 'max']) {
    changeRange(prop, range.value[prop], false);
  }

  updateValidation();
});

watch([required, iri], () => {
  updateValidation();
});

onMounted(async() => {
  addOption();

  // This initialization is enough, since the whole component is re-rendered anyways when e.g. using the undo/redo
  // functionality.
  if (props.initialValidation) {
    required.value = props.initialValidation.required || false;
    iri.value = props.initialValidation.iri || false;

    const range_ = props.initialValidation.range;

    if (range_) {
      for (const prop of ['min', 'max']) {
        range.value[prop] = range_[prop];
      }
    }

    const options_ = props.initialValidation.options;

    if (options_ && options_.length > 0) {
      removeOption(0);

      for (const option of props.initialValidation.options) {
        addOption(option);
      }
    }
  }

  // Skip first potential change.
  await nextTick();
  initialized = true;
});
</script>

<template>
  <div class="card">
    <div class="mx-2">
      <div class="form-row align-items-center my-2">
        <div class="col-md-2 text-muted">
          <small>{{ $t('Required') }}</small>
        </div>
        <div class="col-md-10">
          <input v-model="required" type="checkbox" class="align-middle">
        </div>
      </div>
      <div v-if="isNumericType" class="form-row align-items-center my-2">
        <div class="col-md-2 text-muted">
          <small>{{ $t('Range') }}</small>
        </div>
        <div class="col-md-10">
          <div class="d-flex justify-content-between">
            <div class="input-group input-group-sm mr-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&ge;</span>
              </div>
              <input class="form-control"
                     :value="kadi.utils.toExponentional(range.min)"
                     @change="changeRange('min', $event.target.value)">
            </div>
            <div class="input-group input-group-sm ml-1">
              <div class="input-group-prepend">
                <span class="input-group-text">&le;</span>
              </div>
              <input class="form-control"
                     :value="kadi.utils.toExponentional(range.max)"
                     @change="changeRange('max', $event.target.value)">
            </div>
          </div>
        </div>
      </div>
      <div v-if="['str', 'int', 'float'].includes(type)" class="form-row align-items-center my-2">
        <div class="col-md-2 text-muted">
          <small>{{ $t('Options') }}</small>
        </div>
        <div class="col-md-10">
          <vue-draggable item-key="id" handle=".sort-handle" :list="options" :force-fallback="true" @end="endDrag">
            <template #item="{element: option, index}">
              <div class="form-row" :class="{'mb-md-1 mb-3': index < options.length - 1}">
                <div class="col-md-10 mb-1 mb-md-0">
                  <input class="form-control form-control-sm"
                         :value="getOptionValue(option)"
                         @change="changeOption(option, $event.target.value)">
                </div>
                <div class="col-md-2">
                  <div class="btn-group btn-group-sm w-100">
                    <button type="button" class="btn btn-light" tabindex="-1" @click="addOption(null, index)">
                      <i class="fa-solid fa-plus"></i>
                    </button>
                    <button v-if="options.length > 1"
                            type="button"
                            class="btn btn-light"
                            tabindex="-1"
                            @click="removeOption(index)">
                      <i class="fa-solid fa-xmark"></i>
                    </button>
                    <span class="btn btn-light disabled sort-handle" tabindex="-1">
                      <i class="fa-solid fa-bars"></i>
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </vue-draggable>
          <small class="form-text text-muted">{{ $t('Possible values of this metadatum.') }}</small>
        </div>
      </div>
      <div v-if="type === 'str'" class="form-row align-items-center my-2">
        <div class="col-md-2 text-muted">
          <small>IRI</small>
        </div>
        <div class="col-md-10">
          <input v-model="iri" type="checkbox" class="align-middle">
          <small class="form-text text-muted">{{ $t('Whether the value of this metadatum represents an IRI.') }}</small>
        </div>
      </div>
    </div>
  </div>
</template>
