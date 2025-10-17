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

<!-- eslint-disable vue/no-mutating-props -->
<script setup>
import {nextTick} from 'vue';

import VueDraggable from 'vuedraggable';

const props = defineProps({
  extras: Array,
  editingMode: {
    type: Boolean,
    default: true,
  },
  // Can also be used to detect whether we are in a nested context at all.
  nestedType: {
    type: String,
    default: null,
  },
  depth: {
    type: Number,
    default: 0,
  },
});

const emit = defineEmits(['show-term-search', 'save-checkpoint']);

function newExtra(extraToCopy = null, copyErrors = true, copyValues = true) {
  const extra = {
    id: kadi.utils.randomAlnum(),
    isDragging: false,
    editDetails: false,
    editValidation: false,
    type: {value: 'str', errors: []},
    key: {value: null, errors: []},
    value: {value: null, errors: []},
    unit: {value: null, errors: []},
    description: {value: null, errors: []},
    term: {value: null, errors: []},
    validation: {value: null, errors: []},
  };

  // Always perform a deep copy if an extra is to be copied.
  if (extraToCopy) {
    extra.editDetails = extraToCopy.editDetails || false;
    extra.editValidation = extraToCopy.editValidation || false;

    // Assume the extra is formatted as formdata if the type (which should always exist) is an object.
    const isFormdata = kadi.utils.isObject(extraToCopy.type);

    // Copy all properties completely except for the value, since it might be nested.
    for (const prop of ['type', 'key', 'value', 'unit', 'description', 'term', 'validation']) {
      if (extraToCopy[prop]) {
        if (prop !== 'value') {
          const value = isFormdata ? extraToCopy[prop].value : extraToCopy[prop];
          extra[prop].value = kadi.utils.deepClone(value);
        }

        if (isFormdata && copyErrors) {
          extra[prop].errors = extraToCopy[prop].errors.slice();
        }
      }
    }

    // Copy the value (recursively, in case it is nested).
    const value = isFormdata ? extraToCopy.value.value : extraToCopy.value;

    if (kadi.utils.isNestedType(extra.type.value)) {
      extra.value.value = [];
      value.forEach((nestedExtra) => extra.value.value.push(newExtra(nestedExtra, copyErrors, copyValues)));
    } else if (copyValues) {
      extra.value.value = value;
    }
  }

  return extra;
}

async function focusExtra(extra) {
  await nextTick();

  // Focus the first input that is enabled.
  for (const inputType of ['type', 'key', 'value']) {
    const input = document.getElementsByClassName(`${inputType}-input-${extra.id}`)[0];

    if (input && !input.disabled && !input.readOnly) {
      input.focus();
      kadi.utils.scrollIntoView(input);
      return;
    }
  }
}

function addExtra(extra = null, index = null, focus = false, createCheckpoint = true) {
  let _newExtra = null;

  // If no extra to copy is given and we are inside a list with at least one extra, copy the structure of the last
  // extra, without values.
  if (extra === null && props.nestedType === 'list' && props.extras.length > 0) {
    let extraToCopy = null;

    if (index === null) {
      extraToCopy = props.extras[props.extras.length - 1];
    } else {
      extraToCopy = props.extras[index];
    }

    _newExtra = newExtra(extraToCopy, true, false);
  } else {
    _newExtra = newExtra(extra);
  }

  kadi.utils.addToArray(props.extras, _newExtra, index);

  if (focus) {
    nextTick(() => focusExtra(_newExtra));
  }

  if (createCheckpoint) {
    emit('save-checkpoint');
  }

  return _newExtra;
}

function addExtras(extras, createCheckpoint = true) {
  extras.forEach((extra) => addExtra(extra, null, false, false));

  if (createCheckpoint) {
    emit('save-checkpoint');
  }
}

function removeExtra(extra, createCheckpoint = true) {
  kadi.utils.removeFromArray(props.extras, extra);

  if (createCheckpoint) {
    emit('save-checkpoint');
  }
}

function removeExtras(createCheckpoint = true) {
  props.extras.length = 0;

  if (createCheckpoint) {
    emit('save-checkpoint');
  }
}

function duplicateExtra(extra) {
  const index = props.extras.indexOf(extra);
  const copy = newExtra(extra, false);
  props.extras.splice(index + 1, 0, copy);
  emit('save-checkpoint');
}

async function loadTemplate(endpoint) {
  let data = null;

  try {
    const response = await axios.get(endpoint);
    const template = response.data;

    // Allow both 'records' and 'extras' templates.
    if (template.type === 'record') {
      data = template.data.extras;
    } else if (template.type === 'extras') {
      data = template.data;
    }
  } catch (error) {
    kadi.base.flashDanger($t('Error loading template.'), error.request);
  }

  return data || [];
}

async function initNestedValue(extra, templateEndpoint = null) {
  if (templateEndpoint === null) {
    extra.value.value = [newExtra()];
  } else {
    const extras = await loadTemplate(templateEndpoint);
    const newExtras = [];

    for (const _extra of extras) {
      newExtras.push(newExtra(_extra));
    }
    extra.value.value = newExtras;

    emit('save-checkpoint');
  }
}

function startDrag(e) {
  const extra = e.item._underlying_vm_;
  extra.isDragging = true;
}

function endDrag(e) {
  const extra = e.item._underlying_vm_;
  extra.isDragging = false;

  if (e.from !== e.to || e.oldIndex !== e.newIndex) {
    emit('save-checkpoint');
  }
}

defineExpose({
  newExtra,
  addExtra,
  addExtras,
  removeExtra,
  removeExtras,
  focusExtra,
  loadTemplate,
});
</script>

<template>
  <div :class="{'mt-2': nestedType && extras.length > 0}">
    <vue-draggable item-key="id"
                   handle=".sort-handle"
                   scroll-sensitivity="100"
                   scroll-speed="15"
                   :list="extras"
                   :group="editingMode ? 'extras' : kadi.utils.randomAlnum()"
                   :force-fallback="true"
                   :empty-insert-threshold="35"
                   @start="startDrag"
                   @end="endDrag">
      <template #item="{element: extra, index}">
        <extras-editor-item :extra="extra"
                            :index="index"
                            :editing-mode="editingMode"
                            :nested-type="nestedType"
                            :depth="depth"
                            :class="index < extras.length - 1 ? 'mb-3' : 'mb-2'"
                            @add-extra="addExtra(null, index, true)"
                            @remove-extra="removeExtra(extra)"
                            @duplicate-extra="duplicateExtra(extra)"
                            @init-nested-value="initNestedValue(extra, $event)"
                            @show-term-search="$emit('show-term-search', $event)"
                            @save-checkpoint="$emit('save-checkpoint')">
        </extras-editor-item>
      </template>
    </vue-draggable>
  </div>
  <div class="form-row">
    <div class="col-md-3">
      <button v-if="editingMode || nestedType === 'list'"
              type="button"
              class="btn btn-sm btn-link text-primary p-0"
              tabindex="-1"
              :class="{'mt-2': extras.length > 0 && !kadi.utils.isNestedType(extras[extras.length - 1].type.value)}"
              @click="addExtra(null, null, true)">
        <i class="fa-solid fa-plus mr-1"></i> {{ $t('Add metadatum') }}
      </button>
    </div>
    <div class="col-md-9">
      <slot></slot>
    </div>
  </div>
</template>
