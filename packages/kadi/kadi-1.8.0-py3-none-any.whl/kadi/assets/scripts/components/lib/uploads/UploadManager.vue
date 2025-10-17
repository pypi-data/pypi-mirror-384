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
    <confirm-dialog ref="dialog"></confirm-dialog>
    <slot></slot>
    <upload-dropzone @add-file="addFile"></upload-dropzone>
    <input ref="resumeFileInput" type="file" class="input" @change="resumeFileInputChange">
    <div v-if="uploads.length > 0" class="card bg-light mt-4 mb-3">
      <div class="card-body py-2">
        <div class="form-row align-items-center">
          <div class="col-lg-8">
            {{ $t('Uploads completed') }}: <strong>{{ completedUploadsCount }}/{{ uploads.length }}</strong>
          </div>
          <div class="col-lg-2 d-lg-flex justify-content-end">
            <small class="text-muted">{{ kadi.utils.filesize(totalUploadSize) }}</small>
          </div>
          <div class="col-lg-2 d-lg-flex justify-content-end">
            <div class="btn-group btn-group-sm">
              <button type="button"
                      class="btn btn-primary"
                      :title="$t('Resume all uploads')"
                      :disabled="!uploadsResumable()"
                      @click="resumeUploads()">
                <i class="fa-solid fa-play"></i>
              </button>
              <button type="button"
                      class="btn btn-primary"
                      :title="$t('Pause all uploads')"
                      :disabled="!uploadsPausable()"
                      @click="pauseUploads()">
                <i class="fa-solid fa-pause"></i>
              </button>
              <button type="button"
                      class="btn btn-primary"
                      :title="$t('Cancel all uploads')"
                      :disabled="!uploadsCancelable()"
                      @click="cancelUploads()">
                <i class="fa-solid fa-ban"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-for="(upload, index) in paginatedUploads"
         :key="upload.id"
         class="card"
         :class="{'mb-3': index < uploads.length - 1}">
      <div class="card-body py-2">
        <div class="form-row align-items-center" :class="{'mb-2': upload.state !== UploadState.COMPLETED}">
          <div class="col-lg-8">
            <strong v-if="upload.state === UploadState.COMPLETED">
              <a v-if="upload.viewFileEndpoint" :href="upload.viewFileEndpoint">{{ upload.name }}</a>
              <span v-else>{{ upload.name }}</span>
            </strong>
            <span v-else class="text-muted">{{ upload.name }}</span>
          </div>
          <div class="col-lg-2 d-lg-flex justify-content-end">
            <small class="text-muted">{{ kadi.utils.filesize(upload.size) }}</small>
          </div>
          <div class="col-lg-2 d-lg-flex justify-content-end">
            <span class="badge badge-primary">{{ upload.prettyStateName }}</span>
          </div>
        </div>
        <div v-if="upload.state !== UploadState.COMPLETED" class="form-row align-items-center">
          <div class="col-lg-10 py-1">
            <div class="progress border">
              <div class="progress-bar" :style="{width: `${Math.floor(upload.progress)}%`}">
                {{ Math.floor(upload.progress) }}%
              </div>
            </div>
          </div>
          <div class="col-lg-2 mt-2 mt-lg-0 d-lg-flex justify-content-end">
            <i v-if="upload.state === UploadState.PROCESSING" class="fa-solid fa-circle-notch fa-spin mr-2"></i>
            <div class="btn-group btn-group-sm">
              <button v-if="upload.isPausable()"
                      type="button"
                      class="btn btn-light"
                      :title="$t('Pause upload')"
                      @click="pauseUploads(upload)">
                <i class="fa-solid fa-pause"></i>
              </button>
              <button v-if="upload.isResumable()"
                      type="button"
                      class="btn btn-light"
                      :title="$t('Resume upload')"
                      @click="resumeUploads(upload)">
                <i v-if="upload.isResumable(true)" class="fa-solid fa-play"></i>
                <i v-else class="fa-solid fa-folder-open"></i>
              </button>
              <button v-if="upload.isCancelable()"
                      type="button"
                      class="btn btn-light"
                      :title="$t('Cancel upload')"
                      @click="cancelUploads(upload)">
                <i class="fa-solid fa-ban"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
      <div v-if="upload.replacedFile !== null || upload.createdAt !== null" class="card-footer py-1">
        <div class="d-flex justify-content-between">
          <div>
            <div v-if="upload.replacedFile !== null">
              <span class="text-muted">{{ $t('Replaces') }}</span>
              <a class="text-muted" :href="upload.replacedFile._links.view">
                <strong>{{ upload.replacedFile.name }}</strong>
              </a>
            </div>
          </div>
          <div>
            <small v-if="upload.createdAt !== null" class="text-muted">
              {{ $t('Created at') }} <local-timestamp :timestamp="upload.createdAt"></local-timestamp>
            </small>
          </div>
        </div>
      </div>
    </div>
    <pagination-control :total="uploads.length" :per-page="perPage" @update-page="page = $event"></pagination-control>
  </div>
</template>

<style scoped>
.btn-modal {
  width: 100px;
}

.input {
  position: absolute;
  visibility: hidden;
}
</style>

<script>
import {Upload, UploadProvider, UploadState} from 'scripts/lib/uploads.js';

import UploadDropzone from 'scripts/components/lib/uploads/UploadDropzone.vue';

export default {
  components: {
    UploadDropzone,
  },
  props: {
    newUploadEndpoint: String,
    getUploadsEndpoint: String,
    perPage: {
      type: Number,
      default: 5,
    },
  },
  data() {
    return {
      uploads: [],
      provider: null,
      resumedUpload: null,
      uploadTimeoutHandle: null,
      page: 1,
      UploadState,
    };
  },
  computed: {
    uploadInProgress() {
      return this.uploads.some((upload) => upload.state === UploadState.UPLOADING);
    },
    paginatedUploads() {
      return kadi.utils.paginateArray(this.uploads, this.page, this.perPage);
    },
    completedUploadsCount() {
      // eslint-disable-next-line no-param-reassign
      return this.uploads.reduce((acc, upload) => (upload.state === UploadState.COMPLETED ? acc += 1 : acc), 0);
    },
    totalUploadSize() {
      // eslint-disable-next-line no-param-reassign
      return this.uploads.reduce((acc, upload) => acc += upload.size, 0);
    },
  },
  async mounted() {
    this.provider = new UploadProvider(this.newUploadEndpoint, this.onUploadReplace, null, this.onUploadError);

    // Load all incomplete uploads so the user can resume them.
    const loadedUploads = await this.provider.loadUploads(this.getUploadsEndpoint);

    for (const upload of loadedUploads) {
      this.uploads.push(upload);
    }

    window.addEventListener('beforeunload', this.beforeUnload);
  },
  unmounted() {
    window.removeEventListener('beforeunload', this.beforeUnload);
  },
  methods: {
    uploadsResumable() {
      return this.uploads.some((upload) => upload.isResumable(true));
    },

    uploadsPausable() {
      return this.uploads.some((upload) => upload.isPausable());
    },

    uploadsCancelable() {
      return this.uploads.some((upload) => upload.isCancelable());
    },

    addFile(file) {
      const upload = new Upload(file.name, file.size, file);
      this.uploads.push(upload);

      // When adding multiple files simultaneously, wait until they have all been added to the list.
      window.clearTimeout(this.uploadTimeoutHandle);
      this.uploadTimeoutHandle = window.setTimeout(() => this.uploadNextFile(), 100);
    },

    resumeFileInputChange(e) {
      const file = e.target.files[0];

      if (file.name !== this.resumedUpload.name || file.size !== this.resumedUpload.size) {
        kadi.base.flashWarning($t('The file you have selected has a different name or size than expected.'));
        return;
      }

      this.resumedUpload.blob = file;
      this.provider.resume(this.resumedUpload);
      this.uploadNextFile();
    },

    async onUploadReplace(upload) {
      const msg = $t(
        'A file with the name "{{filename}}" already exists in the current record. Do you want to replace it?',
        {filename: upload.name},
      );
      const input = await this.$refs.dialog.open(msg, false, true);

      if (input.checkbox) {
        for (const _upload of this.uploads) {
          if (input.status) {
            _upload.forceReplace = true;
          } else {
            _upload.skipReplace = true;
          }
        }
      }

      return input.status;
    },

    onUploadError(upload) {
      kadi.utils.removeFromArray(this.uploads, upload);
    },

    async uploadNextFile() {
      const upload = this.uploads.find((upload) => upload.state === UploadState.PENDING);

      if (this.uploadInProgress || !upload) {
        return;
      }

      await this.provider.upload(upload);
      this.uploadNextFile();
    },

    async cancelUploads(upload = null) {
      let msg = null;

      if (upload === null) {
        msg = $t('Are you sure you want to cancel all uploads?');
      } else {
        msg = $t('Are you sure you want to cancel this upload?');
      }

      const input = await this.$refs.dialog.open(msg);

      if (!input.status) {
        return;
      }

      const uploads = upload ? [upload] : this.uploads.slice();

      for (const _upload of uploads) {
        if (await this.provider.cancel(_upload)) {
          kadi.utils.removeFromArray(this.uploads, _upload);
        }
      }

      this.uploadNextFile();
    },

    pauseUploads(upload = null) {
      const uploads = upload ? [upload] : this.uploads;

      for (const _upload of uploads) {
        this.provider.pause(_upload);
      }

      this.uploadNextFile();
    },

    resumeUploads(upload = null) {
      if (upload) {
        if (!this.provider.resume(upload)) {
          // The upload is not directly resumable.
          this.resumedUpload = upload;
          this.$refs.resumeFileInput.click();
        }
      } else {
        for (const _upload of this.uploads) {
          this.provider.resume(_upload);
        }
      }

      this.uploadNextFile();
    },

    beforeUnload(e) {
      if (this.uploadInProgress) {
        e.preventDefault();
        return '';
      }
      return null;
    },
  },
};
</script>
