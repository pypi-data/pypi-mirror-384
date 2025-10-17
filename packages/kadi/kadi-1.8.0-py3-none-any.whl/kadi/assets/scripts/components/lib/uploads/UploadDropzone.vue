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
    <div class="dropzone"
         :class="{'dragging': isDragging}"
         @click="clickDropzone"
         @dragenter.stop.prevent="isDragging = true"
         @dragover.stop.prevent="isDragging = true"
         @dragleave.stop.prevent="isDragging = false"
         @drop.stop.prevent="dropFiles">
      <div class="text-muted mx-3">{{ $t('Drop files here or click to upload.') }}</div>
    </div>
    <input ref="input" multiple type="file" class="input" @change="inputChange">
  </div>
</template>

<style lang="scss" scoped>
.dropzone {
  align-items: center;
  border: 2px dashed #b5bbc2;
  border-radius: 5px;
  cursor: pointer;
  display: flex;
  height: 100px;
  justify-content: center;
  min-height: 0;
  text-align: center;

  &.dragging {
    background-color: #f7f7f7;
    border: 2px solid #b5bbc2;
  }
}

.input {
  position: absolute;
  visibility: hidden;
}
</style>

<script>
export default {
  emits: ['add-file'],
  data() {
    return {
      isDragging: false,
    };
  },
  methods: {
    clickDropzone() {
      this.$refs.input.click();
    },
    inputChange(e) {
      for (const file of e.target.files) {
        this.$emit('add-file', file);
      }
      // Clear the input afterwards, as otherwise some browsers only seem to trigger the change event again if a
      // different file is selected the next time the input is used directly.
      this.$refs.input.value = '';
    },
    dropFiles(e) {
      this.isDragging = false;

      const data = e.dataTransfer;

      if (data.files.length === 0) {
        return;
      }

      // Check if the browser supports dropping of folders.
      if (data.items.length > 0 && data.items[0].webkitGetAsEntry) {
        for (const item of data.items) {
          const entry = item.webkitGetAsEntry();

          if (entry.isFile) {
            this.$emit('add-file', item.getAsFile());
          } else if (entry.isDirectory) {
            this.addFilesFromDirectory(entry);
          }
        }
      } else {
        for (const file of data.files) {
          this.$emit('add-file', file);
        }
      }
    },
    addFilesFromDirectory(item) {
      const reader = item.createReader();

      const readEntries = () => {
        reader.readEntries((entries) => {
          if (entries.length > 0) {
            for (const entry of entries) {
              if (entry.isFile) {
                entry.file((file) => this.$emit('add-file', file));
              } else if (entry.isDirectory) {
                this.addFilesFromDirectory(entry);
              }
            }
            // Some browsers will only handle the first 100 items otherwise.
            readEntries();
          }
        });
      };

      readEntries();
    },
  },
};
</script>
