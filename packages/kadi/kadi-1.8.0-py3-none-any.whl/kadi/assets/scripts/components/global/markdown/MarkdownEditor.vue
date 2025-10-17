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
import {nextTick, onMounted, ref, useTemplateRef, watch} from 'vue';

import {useUndoRedo} from 'scripts/components/composables/undo-redo.js';

const props = defineProps({
  id: {
    type: String,
    default: 'markdown-editor',
  },
  name: {
    type: String,
    default: 'markdown-editor',
  },
  required: {
    type: Boolean,
    default: false,
  },
  initialValue: {
    type: String,
    default: '',
  },
  rows: {
    type: Number,
    default: 8,
  },
  autosize: {
    type: Boolean,
    default: true,
  },
  linkEndpoint: {
    type: String,
    default: null,
  },
  imageEndpoint: {
    type: String,
    default: null,
  },
  hasError: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['input']);

const containerRef = useTemplateRef('container-ref');
const toolbarRef = useTemplateRef('toolbar-ref');
const editorRef = useTemplateRef('editor-ref');
const previewRef = useTemplateRef('preview-ref');

const input = ref(props.initialValue);
const resizable = ref(true);
const previewActive = ref(false);
const linkSelectionActive = ref(false);
const imageSelectionActive = ref(false);
const imageWidth = ref(0);
const imageHeight = ref(0);

const containerId = kadi.utils.randomAlnum();
const tabSize = 4;
const toolbarBtnClasses = 'btn btn-link text-primary my-1';

let prevEditorHeight = 0;
let inputTimeoutHandle = null;

async function selectRange(selectionStart, selectionEnd = null) {
  await nextTick;

  // Set a single caret first, then focus the editor to scroll to it, then apply the actual selection range, if
  // applicable. This produces somewhat consistent results across browsers.
  editorRef.value.selectionStart = editorRef.value.selectionEnd = selectionEnd || selectionStart;
  editorRef.value.focus();
  editorRef.value.selectionStart = Math.max(selectionStart, 0);
}

const {undoable, redoable, undo, redo, saveCheckpoint} = useUndoRedo(
  () => {
    return {
      input: input.value,
      selectionStart: editorRef.value.selectionStart,
      selectionEnd: editorRef.value.selectionEnd,
    };
  },
  (data) => {
    input.value = data.input;
    selectRange(data.selectionStart, data.selectionEnd);
  },
  (currentData, newData) => {
    if (currentData.input !== newData.input) {
      // Dispatch a regular 'change' event from the element as well.
      containerRef.value.dispatchEvent(new Event('change', {bubbles: true}));
      return true;
    }
    return false;
  },
  25,
);

function saveAndUndo() {
  // Force a checkpoint of the current state before undoing.
  window.clearTimeout(inputTimeoutHandle);
  saveCheckpoint();
  undo();
}

function toggleFullscreen() {
  kadi.utils.toggleFullscreen(containerRef.value);
};

function resizeView() {
  if (kadi.utils.isFullscreen()) {
    const toolbarHeight = Math.round(toolbarRef.value.getBoundingClientRect().height);

    editorRef.value.style.height = previewRef.value.style.height = `calc(100vh - ${toolbarHeight - 1}px)`;
    previewRef.value.style.maxHeight = 'none';
    previewRef.value.style.borderBottomLeftRadius = previewRef.value.style.borderBottomLeftRadius = '0';
    toolbarRef.value.style.borderTopLeftRadius = toolbarRef.value.style.borderTopRightRadius = '0';

    resizable.value = false;
  } else {
    editorRef.value.style.height = `${prevEditorHeight}px`;
    previewRef.value.style.height = 'auto';
    previewRef.value.style.maxHeight = '55vh';
    previewRef.value.style.borderBottomLeftRadius = previewRef.value.style.borderBottomLeftRadius = '0.25rem';
    toolbarRef.value.style.borderTopLeftRadius = toolbarRef.value.style.borderTopRightRadius = '0.25rem';

    resizable.value = true;
  }
}

function getToolTitle(tool) {
  const title = tool.label;

  if (tool.shortcut) {
    return `${title} (${$t('Ctrl')}+${tool.shortcut.toUpperCase()})`;
  }

  return title;
}

function getSelectedRows() {
  let firstRowStart = editorRef.value.selectionStart;
  let prevChar = input.value[firstRowStart - 1];

  while (firstRowStart > 0 && prevChar !== '\n') {
    firstRowStart--;
    prevChar = input.value[firstRowStart - 1];
  }

  let lastRowEnd = editorRef.value.selectionEnd;
  let currentChar = input.value[lastRowEnd];

  while (lastRowEnd < input.value.length && currentChar !== '\n') {
    lastRowEnd++;
    currentChar = input.value[lastRowEnd];
  }

  const currentText = input.value.substring(firstRowStart, lastRowEnd);
  const rows = currentText.split('\n');

  const selectedRows = {
    start: firstRowStart,
    end: lastRowEnd,
    rows: [],
  };

  for (let i = 0; i < rows.length; i++) {
    let row = rows[i];

    if (i < (rows.length - 1)) {
      row += '\n';
    }

    selectedRows.rows.push(row);
  }

  return selectedRows;
}

function handleTab(e) {
  const selectionStart = editorRef.value.selectionStart;
  const selectionEnd = editorRef.value.selectionEnd;
  const selectedRows = getSelectedRows();
  const spaces = ' '.repeat(tabSize);

  const getAmountToRemove = (text) => {
    const match = text.match(/^( +)([\s\S]*)/);
    let toRemove = 0;

    if (match) {
      toRemove = Math.min(match[1].length, tabSize);
    }

    return toRemove;
  };

  if (selectedRows.rows.length === 1) {
    if (!e.shiftKey) {
      // Insert a normal tab at the current selection.
      input.value = input.value.substring(0, selectionStart) + spaces + input.value.substring(selectionEnd);
      selectRange(selectionStart + spaces.length);
    } else {
      // Unindent the current line.
      const toRemove = getAmountToRemove(selectedRows.rows[0]);

      input.value = input.value.substring(0, selectedRows.start) + input.value.substring(selectedRows.start + toRemove);
      selectRange(Math.max(selectionStart - toRemove, selectedRows.start));
    }
  } else {
    const endText = input.value.substring(selectedRows.end);
    input.value = input.value.substring(0, selectedRows.start);

    if (!e.shiftKey) {
      // Indent all selected lines.
      for (const row of selectedRows.rows) {
        input.value += spaces + row;
      }

      input.value += endText;
      selectRange(selectionStart + spaces.length, selectionEnd + (selectedRows.rows.length * spaces.length));
    } else {
      // Unindent all selected lines.
      let toRemoveFirst = 0;
      let toRemoveTotal = 0;

      for (let i = 0; i < selectedRows.rows.length; i++) {
        const toRemove = getAmountToRemove(selectedRows.rows[i]);

        if (i === 0) {
          toRemoveFirst = toRemove;
        }

        toRemoveTotal += toRemove;
        input.value += selectedRows.rows[i].substring(toRemove);
      }

      input.value += endText;
      selectRange(Math.max(selectionStart - toRemoveFirst, selectedRows.start), selectionEnd - toRemoveTotal);
    }
  }
}

function handleEnter() {
  const selectionStart = editorRef.value.selectionStart;
  const selectionEnd = editorRef.value.selectionEnd;
  const firstRow = getSelectedRows().rows[0];

  let insertText = '\n';

  // Handle unordered lists, ordered lists and block quotations.
  const match = firstRow.match(/^( *)(\* |[0-9]+\. |>+ )([\s\S]*)/);

  if (match) {
    if (match[2].includes('*')) {
      insertText += `${match[1]}* `;
    } else if (match[2].includes('>')) {
      const prefix = '>'.repeat(match[2].length - 1);
      insertText += `${match[1]}${prefix} `;
    } else {
      insertText += `${match[1]}${Number.parseInt(match[2], 10) + 1}. `;
    }
  } else {
    // Handle spaces at the beginning.
    const match = firstRow.match(/^( +)([\s\S]*)/);

    if (match) {
      insertText += match[1];
    }
  }

  input.value = input.value.substring(0, selectionStart) + insertText + input.value.substring(selectionEnd);
  selectRange(selectionStart + insertText.length);
}

function toggleBlock(startChars, endChars) {
  const selectionStart = editorRef.value.selectionStart;
  const selectionEnd = editorRef.value.selectionEnd;

  let removeBlock = false;
  let newSelectionStart = selectionStart + startChars.length;
  let newSelectionEnd = selectionEnd + endChars.length;

  if (selectionStart >= startChars.length && selectionEnd <= input.value.length - endChars.length) {
    const textBlock = input.value.substring(selectionStart - startChars.length, selectionEnd + endChars.length);

    let regexStart = '';
    let regexEnd = '';

    for (const char of startChars) {
      regexStart += `\\${char}`;
    }
    for (const char of endChars) {
      regexEnd += `\\${char}`;
    }

    const regex = new RegExp(`^${regexStart}[\\s\\S]*${regexEnd}$`);

    if (regex.test(textBlock)) {
      input.value = input.value.substring(0, selectionStart - startChars.length)
                    + input.value.substring(selectionStart, selectionEnd)
                    + input.value.substring(selectionEnd + endChars.length, input.value.length);
      removeBlock = true;
      newSelectionStart = selectionStart - startChars.length;
      newSelectionEnd = selectionEnd - endChars.length;
    }
  }

  if (!removeBlock) {
    input.value = input.value.substring(0, selectionStart)
                  + startChars
                  + input.value.substring(selectionStart, selectionEnd)
                  + endChars
                  + input.value.substring(selectionEnd, input.value.length);
  }

  selectRange(newSelectionStart, newSelectionEnd);
}

function togglePrefix(toggleRowsFunc) {
  const selectedRows = getSelectedRows();
  const endText = input.value.substring(selectedRows.end);

  input.value = input.value.substring(0, selectedRows.start);

  const newSelections = toggleRowsFunc(
    selectedRows,
    editorRef.value.selectionStart,
    editorRef.value.selectionEnd,
  );

  input.value += endText;

  selectRange(Math.max(newSelections.start, selectedRows.start), newSelections.end);
}

function insertText(text) {
  const selectionEnd = editorRef.value.selectionEnd;
  input.value = input.value.substring(0, selectionEnd) + text + input.value.substring(selectionEnd);
  selectRange(selectionEnd + text.length);
}

function toggleHeading() {
  togglePrefix((selectedRows, selectionStart, selectionEnd) => {
    let start = selectionStart;
    let end = selectionEnd;

    for (let i = 0; i < selectedRows.rows.length; i++) {
      if ((/^#{1,5} [\s\S]*/).test(selectedRows.rows[i])) {
        input.value += `#${selectedRows.rows[i]}`;

        end += 1;
        if (i === 0) {
          start += 1;
        }
      } else if ((/^#{6} [\s\S]*/).test(selectedRows.rows[i])) {
        input.value += selectedRows.rows[i].substring(7);

        end -= 7;
        if (i === 0) {
          start -= 7;
        }
      } else {
        input.value += `# ${selectedRows.rows[i]}`;

        end += 2;
        if (i === 0) {
          start += 2;
        }
      }
    }

    return {start, end};
  });
}

function toggleBold() {
  toggleBlock('**', '**');
}

function toggleItalic() {
  toggleBlock('*', '*');
}

function toggleStrikethrough() {
  toggleBlock('~~', '~~');
}

function toggleSuperscript() {
  toggleBlock('^', '^');
}

function toggleSubscript() {
  toggleBlock('~', '~');
}

function toggleCode() {
  if (getSelectedRows().rows.length === 1) {
    toggleBlock('`', '`');
  } else {
    toggleBlock('```\n', '\n```');
  }
}

function toggleMath() {
  if (getSelectedRows().rows.length === 1) {
    toggleBlock('$', '$');
  } else {
    toggleBlock('$$\n', '\n$$');
  }
}

function toggleUnorderedList() {
  togglePrefix((selectedRows, selectionStart, selectionEnd) => {
    let start = selectionStart;
    let end = selectionEnd;

    for (let i = 0; i < selectedRows.rows.length; i++) {
      const match = selectedRows.rows[i].match(/^( *)(\* )([\s\S]*)/);

      if (match) {
        input.value += match[1] + match[3];

        end -= 2;
        if (i === 0) {
          start -= 2;
        }
      } else {
        const match = selectedRows.rows[i].match(/^( *)([\s\S]*)/);
        input.value += `${match[1]}* ${match[2]}`;

        end += 2;
        if (i === 0) {
          start += 2;
        }
      }
    }

    return {start, end};
  });
}

function toggleOrderedList() {
  togglePrefix((selectedRows, selectionStart, selectionEnd) => {
    let start = selectionStart;
    let end = selectionEnd;

    for (let i = 0; i < selectedRows.rows.length; i++) {
      const match = selectedRows.rows[i].match(/^( *)([0-9]+\. )([\s\S]*)/);

      if (match) {
        input.value += match[1] + match[3];

        end -= match[2].length;
        if (i === 0) {
          start -= match[2].length;
        }
      } else {
        const match = selectedRows.rows[i].match(/^( *)([\s\S]*)/);
        const prefix = `${i + 1}. `;

        input.value += match[1] + prefix + match[2];

        end += prefix.length;
        if (i === 0) {
          start += prefix.length;
        }
      }
    }

    return {start, end};
  });
}

function toggleBlockQuotation() {
  togglePrefix((selectedRows, selectionStart, selectionEnd) => {
    let start = selectionStart;
    let end = selectionEnd;

    for (let i = 0; i < selectedRows.rows.length; i++) {
      const match = selectedRows.rows[i].match(/^( *)(> )([\s\S]*)/);

      if (match) {
        input.value += match[1] + match[3];

        end -= 2;
        if (i === 0) {
          start -= 2;
        }
      } else {
        const match = selectedRows.rows[i].match(/^( *)([\s\S]*)/);
        input.value += `${match[1]}> ${match[2]}`;

        end += 2;
        if (i === 0) {
          start += 2;
        }
      }
    }

    return {start, end};
  });
}

function insertHorizontalRule() {
  const rule = '\n\n---\n\n';
  insertText(rule);
}

function insertTable() {
  let column = $t('Column');
  let text = $t('Text');

  const colSize = Math.max(column.length + 2, text.length);
  const divider = '-'.repeat(colSize);

  column += ' '.repeat(Math.max(0, colSize - column.length));
  text += ' '.repeat(Math.max(0, colSize - text.length));

  const table = `\n\n| ${column} | ${column} | ${column} |\n`
                + `| ${divider} | ${divider} | ${divider} |\n`
                + `| ${text} | ${text} | ${text} |\n\n`;
  insertText(table);
}

function insertLink(toggleSelection) {
  if (toggleSelection && props.linkEndpoint) {
    imageSelectionActive.value = false;
    linkSelectionActive.value = !linkSelectionActive.value;

    // Resize the view again once the height of the toolbar is updated.
    nextTick(resizeView);
  } else {
    const textPlaceholder = $t('Text');
    const selectionEnd = editorRef.value.selectionEnd + textPlaceholder.length + 3;

    insertText(`[${textPlaceholder}](URL)`);
    selectRange(selectionEnd, selectionEnd + 3);
  }
}

function selectLink(file) {
  // Only use the path to stay domain-independent.
  const href = new URL(file.view_endpoint).pathname;
  insertText(`[${file.text}](${href})`);
}

function updateImageSize(ref, value) {
  ref.value = value;
  ref.value = Number.parseInt(value, 10);

  if (window.isNaN(ref.value) || ref.value < 1) {
    ref.value = 0;
  }
}

function updateImageWidth(value) {
  updateImageSize(imageWidth, value);
}

function updateImageHeight(value) {
  updateImageSize(imageHeight, value);
}

function insertImage() {
  if (props.imageEndpoint) {
    linkSelectionActive.value = false;
    imageSelectionActive.value = !imageSelectionActive.value;

    // Resize the view again once the height of the toolbar is updated.
    nextTick(resizeView);
  } else {
    let altPlaceholder = $t('Text');

    if (imageWidth.value || imageHeight.value) {
      altPlaceholder += `|${imageWidth.value || ''}x${imageHeight.value || ''}`;
    }

    const selectionEnd = editorRef.value.selectionEnd + altPlaceholder.length + 4;

    insertText(`![${altPlaceholder}](URL)`);
    selectRange(selectionEnd, selectionEnd + 3);
  }
}

function selectImage(file) {
  // Only use the path to stay domain-independent.
  const href = new URL(file.preview_endpoint).pathname;
  let alt = file.text;

  if (imageWidth.value || imageHeight.value) {
    alt += `|${imageWidth.value || ''}x${imageHeight.value || ''}`;
  }

  insertText(`![${alt}](${href})`);
}

const toolbar = [
  {
    icon: 'fa-heading',
    label: $t('Heading'),
    handler: toggleHeading,
    shortcut: 'h',
  },
  {
    icon: 'fa-bold',
    label: $t('Bold'),
    handler: toggleBold,
    shortcut: 'b',
  },
  {
    icon: 'fa-italic',
    label: $t('Italic'),
    handler: toggleItalic,
    shortcut: 'i',
  },
  {
    icon: 'fa-strikethrough',
    label: $t('Strikethrough'),
    handler: toggleStrikethrough,
    shortcut: 's',
  },
  {
    icon: 'fa-superscript',
    label: $t('Superscript'),
    handler: toggleSuperscript,
    shortcut: '1',
  },
  {
    icon: 'fa-subscript',
    label: $t('Subscript'),
    handler: toggleSubscript,
    shortcut: '2',
  },
  '|',
  {
    icon: 'fa-code',
    label: $t('Code'),
    handler: toggleCode,
    shortcut: 'd',
  },
  {
    icon: 'fa-square-root-variable',
    label: $t('Math'),
    handler: toggleMath,
    shortcut: 'm',
  },
  '|',
  {
    icon: 'fa-list-ul',
    label: $t('Unordered list'),
    handler: toggleUnorderedList,
    shortcut: 'u',
  },
  {
    icon: 'fa-list-ol',
    label: $t('Ordered list'),
    handler: toggleOrderedList,
    shortcut: 'o',
  },
  {
    icon: 'fa-quote-left',
    label: $t('Block quotation'),
    handler: toggleBlockQuotation,
    shortcut: 'l',
  },
  '|',
  {
    icon: 'fa-minus',
    label: $t('Horizontal rule'),
    handler: insertHorizontalRule,
    shortcut: null,
  },
  {
    icon: 'fa-table',
    label: $t('Table'),
    handler: insertTable,
    shortcut: null,
  },
];

async function keydownHandler(e) {
  if (e.ctrlKey) {
    for (const button of toolbar) {
      if (button.shortcut === e.key) {
        e.preventDefault();

        if (!previewActive.value) {
          button.handler();
        }
        return;
      }
    }

    switch (e.key) {
      case 'p':
        e.preventDefault();
        previewActive.value = !previewActive.value;

        await nextTick();

        if (!previewActive.value) {
          editorRef.value.focus();
        } else {
          previewRef.value.focus();
        }
        break;

      case 'z':
        e.preventDefault();
        saveAndUndo();
        break;

      case 'y':
        e.preventDefault();
        redo();
        break;

      default:
    }
  }
}

watch(input, () => {
  emit('input', input.value);

  window.clearTimeout(inputTimeoutHandle);
  inputTimeoutHandle = window.setTimeout(saveCheckpoint, 500);
});

onMounted(async() => {
  new ResizeObserver((entries) => {
    if (!previewActive.value && !kadi.utils.isFullscreen()) {
      prevEditorHeight = entries[0].borderBoxSize[0].blockSize;
    }
  }).observe(editorRef.value);

  saveCheckpoint();

  containerRef.value.addEventListener('keydown', keydownHandler);
  containerRef.value.addEventListener('fullscreenchange', resizeView);

  await nextTick();

  if (props.autosize && editorRef.value.scrollHeight > editorRef.value.clientHeight) {
    editorRef.value.style.height = `${Math.min(window.innerHeight - 200, editorRef.value.scrollHeight + 5)}px`;
  }
});
</script>

<template>
  <div :id="containerId" ref="container-ref">
    <div ref="toolbar-ref" class="card toolbar">
      <div class="card-body px-1 py-0">
        <button type="button"
                class="btn btn-link text-primary my-1"
                :class="{'border-active': previewActive}"
                :title="`${$t('Preview')} (${$t('Ctrl')}+P)`"
                @click="previewActive = !previewActive">
          <strong>{{ $t('Preview') }}</strong>
        </button>
        <span class="separator d-none d-lg-inline"></span>
        <span v-for="tool in toolbar" :key="tool.label">
          <span v-if="tool === '|'" class="separator d-none d-lg-inline"></span>
          <button v-else
                  type="button"
                  :class="toolbarBtnClasses"
                  :title="getToolTitle(tool)"
                  :disabled="previewActive"
                  @click="tool.handler">
            <i class="fa-solid" :class="tool.icon"></i>
          </button>
        </span>
        <span class="separator d-none d-lg-inline"></span>
        <button type="button"
                :title="$t('Link')"
                :class="toolbarBtnClasses + (linkSelectionActive ? ' border-active' : '')"
                :disabled="previewActive"
                @click="insertLink(true)">
          <i class="fa-solid fa-link"></i>
        </button>
        <button type="button"
                :title="$t('Image')"
                :class="toolbarBtnClasses + (imageSelectionActive ? ' border-active' : '')"
                :disabled="previewActive"
                @click="insertImage">
          <i class="fa-solid fa-image"></i>
        </button>
        <span class="separator d-none d-lg-inline"></span>
        <button type="button"
                :title="$t('Toggle fullscreen')"
                :class="toolbarBtnClasses"
                @click="toggleFullscreen">
          <i class="fa-solid fa-expand"></i>
        </button>
        <button type="button"
                :title="`${$t('Undo')} (${$t('Ctrl')}+Z)`"
                :class="toolbarBtnClasses"
                :disabled="!undoable"
                @click="saveAndUndo">
          <i class="fa-solid fa-rotate-left"></i>
        </button>
        <button type="button"
                :title="`${$t('Redo')} (${$t('Ctrl')}+Y)`"
                :class="toolbarBtnClasses"
                :disabled="!redoable"
                @click="redo">
          <i class="fa-solid fa-rotate-right"></i>
        </button>
        <div v-if="linkSelectionActive" key="link" class="mb-2">
          <hr class="mt-0 mb-2">
          <div class="form-row">
            <div class="col-md-4 mb-2 mb-md-0">
              <button type="button"
                      class="btn btn-sm btn-block btn-light"
                      :disabled="previewActive"
                      @click="insertLink(false)">
                {{ $t('Insert link placeholder') }}
              </button>
            </div>
            <div class="col-md-8">
              <dynamic-selection container-classes="select2-single-sm"
                                 :disabled="previewActive"
                                 :placeholder="$t('Select a record file to link')"
                                 :endpoint="linkEndpoint"
                                 :reset-on-select="true"
                                 :dropdown-parent="`#${containerId}`"
                                 @select="selectLink">
              </dynamic-selection>
            </div>
          </div>
        </div>
        <div v-if="imageSelectionActive" key="image" class="mb-2">
          <hr class="mt-0 mb-2">
          <div class="form-row">
            <div class="col-md-4 mb-2 mb-md-0">
              <div class="form-row">
                <div class="col">
                  <div class="input-group input-group-sm">
                    <input class="form-control"
                           :value="imageWidth || ''"
                           :placeholder="$t('Width')"
                           @change="updateImageWidth($event.target.value)">
                    <div class="input-group-append">
                      <span class="input-group-text">px</span>
                    </div>
                  </div>
                </div>
                <div class="col">
                  <div class="input-group input-group-sm">
                    <input class="form-control"
                           :value="imageHeight || ''"
                           :placeholder="$t('Height')"
                           @change="updateImageHeight($event.target.value)">
                    <div class="input-group-append">
                      <span class="input-group-text">px</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-md-8">
              <dynamic-selection container-classes="select2-single-sm"
                                 :disabled="previewActive"
                                 :placeholder="$t('Select an uploaded JPEG or PNG image')"
                                 :endpoint="imageEndpoint"
                                 :reset-on-select="true"
                                 :dropdown-parent="`#${containerId}`"
                                 @select="selectImage">
              </dynamic-selection>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-show="!previewActive">
      <textarea :id="id"
                ref="editor-ref"
                v-model="input"
                class="form-control editor"
                spellcheck="false"
                :name="name"
                :required="required"
                :rows="rows"
                :class="{'has-error': hasError, 'non-resizable': !resizable}"
                @keydown.tab="handleTab"
                @keydown.tab.prevent
                @keydown.enter="handleEnter"
                @keydown.enter.prevent>
      </textarea>
      <div class="card bg-light footer">
        <small class="text-muted">
          {{ $t('This editor supports Markdown, including math written in LaTeX syntax rendered with') }}
          <a class="text-muted ml-1"
             href="https://katex.org/docs/supported.html"
             target="_blank"
             rel="noopener noreferrer">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
            <strong>KaTeX</strong>.
          </a>
          {{ $t('Note that HTML tags and external images are not supported.') }}
        </small>
      </div>
    </div>
    <div v-show="previewActive">
      <div ref="preview-ref" class="card preview-container" tabindex="-1">
        <div class="card-body preview-content">
          <markdown-renderer :input="input"></markdown-renderer>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.border-active {
  border: 1px solid #ced4da;
}

.editor {
  border-radius: 0;
  box-shadow: none;
  font-family: monospace, monospace;
  font-size: 10pt;
  position: relative;
  z-index: 1;
}

.footer {
  border-color: #ced4da;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  margin-top: -1px;
  padding: 2px 10px 2px 10px;
}

.preview-container {
  border-color: #ced4da;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  max-height: 75vh;
}

.preview-content {
  overflow-y: auto;
}

.separator {
  border-right: 1px solid #dfdfdf;
  margin-left: 5px;
  margin-right: 5px;
  padding-bottom: 3px;
  padding-top: 3px;
}

.toolbar {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-color: #ced4da;
  margin-bottom: -1px;
}

.non-resizable {
  resize: none;
}
</style>
