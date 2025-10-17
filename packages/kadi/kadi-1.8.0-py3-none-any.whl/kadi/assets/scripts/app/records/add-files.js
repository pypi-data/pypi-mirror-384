/* Copyright 2020 Karlsruhe Institute of Technology
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

import {Upload, UploadProvider} from 'scripts/lib/uploads.js';
import {newVue} from 'scripts/lib/core.js';

import ImageEditor from 'scripts/components/lib/ImageEditor.vue';
import TextEditor from 'scripts/components/lib/TextEditor.vue';
import UploadManager from 'scripts/components/lib/uploads/UploadManager.vue';
import WorkflowEditor from 'scripts/components/lib/workflows/WorkflowEditor.vue';

newVue({
  components: {
    ImageEditor,
    TextEditor,
    UploadManager,
    WorkflowEditor,
  },
  data() {
    return {
      uploadProvider: null,
      currentTab: null,
      fileTypes: {
        image: {
          filename: '',
          currentFile: null,
          fileUrl: null,
          unsavedChanges: false,
          uploading: false,
        },
        text: {
          filename: '',
          currentFile: null,
          fileUrl: null,
          unsavedChanges: false,
          uploading: false,
        },
        workflow: {
          filename: '',
          currentFile: null,
          fileUrl: null,
          unsavedChanges: false,
          uploading: false,
        },
      },
    };
  },
  mounted() {
    this.uploadProvider = new UploadProvider(
      kadi.context.upload_endpoint,
      this.onUploadReplace,
      this.onUploadSuccess,
      this.onUploadError,
    );

    const fileType = kadi.context.file_type;
    const currentFile = kadi.context.current_file;

    if (fileType !== null && fileType in this.fileTypes) {
      const fileMeta = this.fileTypes[fileType];

      fileMeta.filename = currentFile.name;
      fileMeta.currentFile = currentFile;
      fileMeta.fileUrl = currentFile._links.download;

      // Wait until the content of the previous tab has loaded, as some components rely on the DOM to initialize their
      // size correctly.
      this.$nextTick(() => this.$refs.navTabs.changeTab(fileType));
    }

    kadi.base.tour.initialize('basic', 'files');
  },
  methods: {
    changeTab(tab) {
      this.currentTab = tab;
    },
    uploadDisabled(fileType) {
      const fileMeta = this.fileTypes[fileType];
      return !fileMeta.unsavedChanges || fileMeta.uploading || !fileMeta.filename || fileMeta.filename.length > 256;
    },
    async onUploadReplace(upload) {
      const msg = $t(
        'A file with the name "{{filename}}" already exists in the current record. Do you want to replace it?',
        {filename: upload.name},
      );

      const input = await this.$refs.dialog.open(msg);
      return input.status;
    },
    onUploadSuccess(upload, file) {
      const fileMeta = this.fileTypes[upload.origin];

      fileMeta.currentFile = file;
      fileMeta.unsavedChanges = false;
      fileMeta.uploading = false;

      kadi.base.flashSuccess($t('File uploaded successfully.'));
    },
    onUploadError(upload) {
      this.fileTypes[upload.origin].uploading = false;
    },
    async uploadFile(file, fileType) {
      const currentFile = this.fileTypes[fileType].currentFile;
      const replaceFile = currentFile && currentFile.name === file.name;

      if (replaceFile) {
        const response = await axios.get(currentFile._links.self);

        // Check if the content of the current file has changed since last (up)loading it by comparing the checksums.
        if (currentFile.checksum !== response.data.checksum) {
          // eslint-disable-next-line @stylistic/js/max-len
          const msg = $t('The content of the file you are currently editing changed since loading it. Do you still want to replace it?');
          const input = await this.$refs.dialog.open(msg);

          if (!input.status) {
            return;
          }
        }
      }

      this.fileTypes[fileType].uploading = true;

      const upload = new Upload(file.name, file.size, file, replaceFile, fileType);
      this.uploadProvider.upload(upload);
    },
    saveImage(canvas) {
      let filename = this.fileTypes.image.filename;

      if (!filename.endsWith('.png')) {
        filename += '.png';
      }

      const bstr = window.atob(canvas.toDataURL().split(',')[1]);
      let n = bstr.length;
      const u8arr = new Uint8Array(n);

      while (n) {
        u8arr[n - 1] = bstr.charCodeAt(n - 1);
        n -= 1;
      }

      const file = new File([u8arr], filename);
      this.uploadFile(file, 'image');
    },
    saveText(editor, newline) {
      let filename = this.fileTypes.text.filename;

      // Only do a very basic check whether any file extension exists at all.
      if (!filename.includes('.')) {
        filename += '.txt';
      }

      let text = editor.state.doc.toString();

      if (newline === 'windows') {
        text = text.replaceAll('\n', '\r\n');
      }

      const file = new File([text], filename);
      this.uploadFile(file, 'text');
    },
    saveWorkflow(editor) {
      let filename = this.fileTypes.workflow.filename;

      if (!filename.endsWith('.flow')) {
        filename += '.flow';
      }

      const file = new File([JSON.stringify(editor.dump(), null, 2)], filename);
      this.uploadFile(file, 'workflow');
    },
  },
});
