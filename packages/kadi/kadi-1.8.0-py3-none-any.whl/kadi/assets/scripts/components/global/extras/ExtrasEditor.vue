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
import {computed, onMounted, provide, ref, useTemplateRef} from 'vue';

import {useUndoRedo} from 'scripts/components/composables/undo-redo.js';

const props = defineProps({
  id: {
    type: String,
    default: 'extras-editor',
  },
  name: {
    type: String,
    default: 'extras-editor',
  },
  label: {
    type: String,
    default: 'Extra metadata',
  },
  initialValues: {
    type: Array,
    default: () => [],
  },
  editExtraKeys: {
    type: Array,
    default: () => [],
  },
  templateEndpoint: {
    type: String,
    default: null,
  },
  termsEndpoint: {
    type: String,
    default: null,
  },
  editingMode: {
    type: Boolean,
    default: true,
  },
  isCollapsed: {
    type: Boolean,
    default: false,
  },
});

provide('templateEndpoint', props.templateEndpoint);
provide('enableTermSearch', Boolean(props.termsEndpoint));

const editorRef = useTemplateRef('editor-ref');
const extrasRef = useTemplateRef('extras-ref');
const pasteDialogRef = useTemplateRef('paste-dialog-ref');
const termSearchRef = useTemplateRef('term-search-ref');

const extras = ref([]);
const pastedExtras = ref('');
const pastedExtrasError = ref('');
const treeView = ref(false);
const editingMode_ = ref(props.editingMode);
const isCollapsed_ = ref(props.isCollapsed);

const numInitialFields = 3;

let currentExtra = null;

function extraIsEmpty(extra, nestedType = null) {
  if (nestedType === 'list') {
    return false;
  }

  for (const prop of ['key', 'value', 'unit', 'description', 'term', 'validation']) {
    if (extra[prop].value !== null) {
      return false;
    }
  }

  return true;
}

function serializeExtras(extras, nestedType = null) {
  const newExtras = [];

  for (const extra of extras) {
    if (extraIsEmpty(extra, nestedType)) {
      continue;
    }

    const newExtra = {
      type: extra.type.value,
      value: extra.value.value,
    };

    if (nestedType !== 'list') {
      newExtra.key = extra.key.value;
    }
    if (['int', 'float'].includes(newExtra.type)) {
      newExtra.unit = extra.unit.value;
    }

    for (const prop of ['description', 'term', 'validation']) {
      if (extra[prop].value) {
        newExtra[prop] = extra[prop].value;
      }
    }

    if (kadi.utils.isNestedType(newExtra.type)) {
      newExtra.value = serializeExtras(newExtra.value, newExtra.type);
    }

    newExtras.push(newExtra);
  }

  return newExtras;
}

const serializedExtras = computed(() => JSON.stringify(serializeExtras(extras.value)));

const {undoable, redoable, undo, redo, saveCheckpoint} = useUndoRedo(
  (triggerChange = true) => {
    if (triggerChange) {
      // Dispatch a regular 'change' event from the element as well.
      editorRef.value.dispatchEvent(new Event('change', {bubbles: true}));
    }

    const checkpointData = [];
    // Save a deep copy of the extra metadata.
    extras.value.forEach((extra) => checkpointData.push(extrasRef.value.newExtra(extra)));
    return checkpointData;
  },
  (data) => {
    extrasRef.value.removeExtras(false);
    extrasRef.value.addExtras(data, false);
  },
);

function removeEmptyExtras() {
  extras.value.slice().forEach((extra) => {
    if (extraIsEmpty(extra)) {
      extrasRef.value.removeExtra(extra, false);
    }
  });
}

function initializeFields() {
  for (let i = 0; i < numInitialFields; i++) {
    extrasRef.value.addExtra(null, null, false, false);
  }
}

function showPasteDialog() {
  pasteDialogRef.value.open();
}

function pasteExtras() {
  let parsedExtras = null;

  try {
    parsedExtras = JSON.parse(pastedExtras.value);
  } catch {
    pastedExtrasError.value = $t('Invalid JSON data.');
    return;
  }

  try {
    if (!kadi.utils.isArray(parsedExtras)) {
      throw new Error();
    }

    extrasRef.value.addExtras(parsedExtras, false);
    removeEmptyExtras();
  } catch {
    pastedExtrasError.value = $t('Invalid extras format.');
    return;
  }

  saveCheckpoint();

  pastedExtras.value = '';
  pastedExtrasError.value = '';
  pasteDialogRef.value.hide();
}

function formatExtras() {
  try {
    const parsedExtras = JSON.parse(pastedExtras.value);
    pastedExtras.value = JSON.stringify(parsedExtras, null, 2);
    pastedExtrasError.value = '';
  } catch {
    pastedExtrasError.value = $t('Invalid JSON data.');
  }
}

function resetEditor() {
  const reset = () => {
    extrasRef.value.removeExtras(false);
    initializeFields();
    saveCheckpoint();
  };

  // Only reset the editor if it is not in initial state already.
  if (extras.value.length === numInitialFields) {
    for (const extra of extras.value) {
      if (!extraIsEmpty(extra)) {
        reset();
        return;
      }
    }
  } else {
    reset();
  }
}

async function selectTemplate(template) {
  const data = await extrasRef.value.loadTemplate(template.endpoint);
  removeEmptyExtras();
  extrasRef.value.addExtras(data);
}

function focusExtra(extra) {
  treeView.value = false;
  extrasRef.value.focusExtra(extra);
}

function showTermSearch(extra) {
  currentExtra = extra;
  termSearchRef.value.open(extra.key.value || '');
}

function selectTerm(term) {
  currentExtra.term.value = term;
  saveCheckpoint();
}

onMounted(() => {
  if (props.initialValues.length > 0) {
    extrasRef.value.addExtras(props.initialValues, false);
  } else {
    initializeFields();
  }

  saveCheckpoint(false);

  if (props.editExtraKeys.length > 0) {
    let extra = null;
    let previousType = null;
    let currentExtras = extras.value;

    for (const key of props.editExtraKeys) {
      // Try to use the key as an index instead for list values.
      if (previousType === 'list') {
        const index = Number.parseInt(key, 10);

        if (window.isNaN(index) || index < 0 || index >= currentExtras.length) {
          break;
        }

        extra = currentExtras[index];
      } else {
        const result = currentExtras.find((extra) => extra.key.value === key);

        if (!result) {
          break;
        }

        extra = result;
      }

      previousType = extra.type.value;
      currentExtras = extra.value.value;

      // In case we can't continue with any nested values, just break out of the loop, even if not all keys were
      // processed yet.
      if (!kadi.utils.isArray(currentExtras)) {
        break;
      }
    }

    if (extra) {
      focusExtra(extra);
    }
  }

  editorRef.value.addEventListener('keydown', (e) => {
    if (e.ctrlKey) {
      switch (e.key) {
        case 'z':
          e.preventDefault();
          // Aside from keeping focus, this also forces a change event in case the shortcut is pressed while an input
          // field is still being edited. This in turn triggers the checkpoint creation before the undo function is
          // actually called.
          editorRef.value.focus();
          undo();
          break;

        case 'y':
          e.preventDefault();
          editorRef.value.focus();
          redo();
          break;

        case 'm':
          e.preventDefault();
          editingMode_.value = !editingMode_.value;
          editorRef.value.focus();
          break;

        case 'e':
          e.preventDefault();
          treeView.value = !treeView.value;
          editorRef.value.focus();
          break;

        default:
      }
    }
  });
});
</script>

<template>
  <div ref="editor-ref" tabindex="-1">
    <div class="form-row align-items-center">
      <div class="col-md-3 mb-2" :class="{'mb-md-0': isCollapsed_}">
        <collapse-item :id="id"
                       class="text-default"
                       :is-collapsed="isCollapsed_"
                       @collapse="isCollapsed_ = $event">
          {{ label }}
        </collapse-item>
      </div>
      <div v-if="!isCollapsed_" class="col-md-9 d-md-flex justify-content-end">
        <div class="btn-group btn-group-sm mr-1 mr-md-2">
          <button type="button"
                  class="btn btn-light"
                  tabindex="-1"
                  :title="`${$t('Undo')} (${$t('Ctrl')}+Z)`"
                  :disabled="treeView || !undoable"
                  @click="undo">
            <i class="fa-solid fa-rotate-left"></i>
          </button>
          <button type="button"
                  class="btn btn-light"
                  tabindex="-1"
                  :title="`${$t('Redo')} (${$t('Ctrl')}+Y)`"
                  :disabled="treeView || !redoable"
                  @click="redo">
            <i class="fa-solid fa-rotate-right"></i>
          </button>
          <button v-if="editingMode_"
                  type="button"
                  class="btn btn-light"
                  tabindex="-1"
                  :title="$t('Paste metadata')"
                  :disabled="treeView"
                  @click="showPasteDialog">
            <i class="fa-solid fa-paste"></i>
          </button>
          <button v-if="editingMode_"
                  type="button"
                  class="btn btn-light"
                  tabindex="-1"
                  :title="$t('Reset editor')"
                  :disabled="treeView"
                  @click="resetEditor">
            <i class="fa-solid fa-rotate"></i>
          </button>
          <button type="button"
                  class="btn btn-light"
                  tabindex="-1"
                  :title="`${$t('Toggle mode')} (${$t('Ctrl')}+M)`"
                  :disabled="treeView"
                  @click="editingMode_ = !editingMode_">
            <span v-if="!editingMode_">{{ $t('Editing mode') }}</span>
            <span v-else>{{ $t('Simple mode') }}</span>
          </button>
        </div>
        <button type="button"
                class="btn btn-sm btn-light"
                tabindex="-1"
                :title="`${$t('Toggle view')} (${$t('Ctrl')}+E)`"
                @click="treeView = !treeView">
          <span v-if="treeView">
            <i class="fa-solid fa-pencil"></i> {{ $t('Editor view') }}
          </span>
          <span v-else>
            <i class="fa-solid fa-bars-staggered"></i> {{ $t('Tree view') }}
          </span>
        </button>
      </div>
    </div>
    <div :id="id" class="mt-2">
      <div v-show="!treeView" class="pt-1">
        <extras-editor-items ref="extras-ref"
                             :extras="extras"
                             :editing-mode="editingMode_"
                             @show-term-search="showTermSearch($event)"
                             @save-checkpoint="saveCheckpoint">
          <div v-if="templateEndpoint" class="form-row align-items-center mt-2">
            <div class="offset-md-5 col-md-7 offset-xl-7 col-xl-5">
              <dynamic-selection container-classes="select2-single-sm"
                                 :placeholder="$t('Select a template')"
                                 :endpoint="templateEndpoint"
                                 :reset-on-select="true"
                                 @select="selectTemplate">
              </dynamic-selection>
            </div>
          </div>
        </extras-editor-items>
      </div>
      <div v-show="treeView" class="pt-1">
        <div class="card text-break overflow-auto">
          <div class="card-body py-1">
            <extras-editor-tree-view :extras="extras" @focus-extra="focusExtra"></extras-editor-tree-view>
          </div>
        </div>
      </div>
    </div>
    <input type="hidden" :name="name" :value="serializedExtras">
    <term-search v-if="termsEndpoint" ref="term-search-ref" :endpoint="termsEndpoint" @select-term="selectTerm">
    </term-search>
    <modal-dialog ref="paste-dialog-ref" :title="$t('Add metadata as JSON')">
      <template #body>
        <textarea v-model.trim="pastedExtras"
                  class="form-control form-control-sm paste-area-body"
                  spellcheck="false"
                  rows="20"
                  :class="{'has-error': pastedExtrasError}"
                  @change.stop>
        </textarea>
        <div class="card bg-light paste-area-footer">
          <small class="text-muted">
            {{ $t('Note that only the metadata format used by Kadi4Mat is currently supported.') }}
          </small>
        </div>
        <div v-if="pastedExtrasError" class="invalid-feedback">{{ pastedExtrasError }}</div>
      </template>
      <template #footer>
        <div class="d-flex justify-content-between">
          <button type="button" class="btn btn-sm btn-primary" :disabled="!pastedExtras" @click="pasteExtras">
            {{ $t('Add metadata') }}
          </button>
          <button type="button" class="btn btn-sm btn-light" :disabled="!pastedExtras" @click="formatExtras">
            {{ $t('Format JSON') }}
          </button>
        </div>
      </template>
    </modal-dialog>
  </div>
</template>

<style scoped>
.paste-area-body {
  border-radius: 0;
  box-shadow: none;
  font-family: monospace, monospace;
  font-size: 10pt;
  position: relative;
  z-index: 1;
}

.paste-area-footer {
  border-color: #ced4da;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  margin-top: -1px;
  padding: 2px 10px 2px 10px;
}
</style>
