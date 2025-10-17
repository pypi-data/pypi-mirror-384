/* Copyright 2025 Karlsruhe Institute of Technology
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. */

import {computed, ref} from 'vue';

export function useUndoRedo(getCheckpointData, restoreCheckpointData, verifyCheckpointData = null, stackDepth = 10) {
  const undoStack = ref([]);
  const undoStackIndex = ref(0);

  const undoable = computed(() => undoStackIndex.value > 0);
  const redoable = computed(() => undoStackIndex.value < (undoStack.value.length - 1));

  function undo() {
    if (undoable.value) {
      undoStackIndex.value--;
      restoreCheckpointData(undoStack.value[undoStackIndex.value]);
    }
  }

  function redo() {
    if (redoable.value) {
      undoStackIndex.value++;
      restoreCheckpointData(undoStack.value[undoStackIndex.value]);
    }
  }

  function saveCheckpoint(...args) {
    const checkpointData = getCheckpointData(...args);

    if (undoStack.value.length > 0
        && verifyCheckpointData !== null
        && !verifyCheckpointData(undoStack.value[undoStackIndex.value], checkpointData)) {
      return;
    }

    undoStack.value.splice(undoStackIndex.value + 1);
    undoStack.value.push(checkpointData);
    undoStackIndex.value = undoStack.value.length - 1;

    if (undoStack.value.length > stackDepth) {
      undoStack.value.shift();
      undoStackIndex.value--;
    }
  }

  return {undoable, redoable, undo, redo, saveCheckpoint};
}
