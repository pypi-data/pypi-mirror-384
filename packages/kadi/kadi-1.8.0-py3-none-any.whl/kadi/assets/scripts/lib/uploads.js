/* Copyright 2024 Karlsruhe Institute of Technology
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

const UploadState = {
  PENDING: 'pending',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  PAUSED: 'paused',
  CANCELED: 'canceled',
};

class Upload {
  skipReplace = false;
  controller = null;
  progress = 0;

  // Only used once the upload has been initialized.
  uploadType = null;
  createdAt = null;
  replacedFile = null;
  getUploadEndpoint = null;
  deleteUploadEndpoint = null;

  // Only used once the upload has been completed.
  viewFileEndpoint = null;

  // Only used for direct uploads.
  uploadDataEndpoint = null;

  // Only used for chunked uploads.
  chunks = [];
  chunkCount = null;
  chunkSize = null;
  uploadChunkEndpoint = null;
  finishUploadEndpoint = null;

  constructor(name, size, blob = null, forceReplace = false, origin = null) {
    this.name = name;
    this.size = size;
    this.blob = blob;
    this.forceReplace = forceReplace;
    // An identifier to distinguish where an upload originated from.
    this.origin = origin;

    this.id = kadi.utils.randomAlnum();
    this.state = UploadState.PENDING;
  }

  get initialized() {
    return Boolean(this.uploadType);
  }

  get chunked() {
    return this.uploadType === 'chunked';
  }

  get prettyStateName() {
    switch (this.state) {
      case UploadState.PENDING: return $t('Pending');
      case UploadState.UPLOADING: return $t('Uploading');
      case UploadState.PROCESSING: return $t('Processing');
      case UploadState.COMPLETED: return $t('Completed');
      case UploadState.PAUSED: return $t('Paused');
      case UploadState.CANCELED: return $t('Canceled');
      default: return this.state;
    }
  }

  initialize(data) {
    this.uploadType = data.upload_type;
    this.createdAt = data.created_at;
    this.replacedFile = data.file;
    this.getUploadEndpoint = data._links.self;
    this.deleteUploadEndpoint = data._actions.delete;

    if (!this.chunked) {
      this.uploadDataEndpoint = data._actions.upload_data;
    } else {
      this.chunks = data.chunks;
      this.chunkCount = data.chunk_count;
      this.chunkSize = data._meta.chunk_size;
      this.uploadChunkEndpoint = data._actions.upload_data;
      this.finishUploadEndpoint = data._actions.finish;
      this.updateChunkProgress();
    }
  }

  updateChunkProgress(additionalSize = 0) {
    // eslint-disable-next-line no-param-reassign
    const totalChunkSize = this.chunks.reduce((acc, chunk) => acc += chunk.size, 0);
    this.progress = Math.min((totalChunkSize + additionalSize), this.size) / this.size * 100;
  }

  isPausable() {
    // Uploads that are still pending can always be paused.
    if (this.state === UploadState.PENDING) {
      return true;
    }

    // Otherwise, only chunked uploads that have already been started can be paused.
    return this.chunked && this.state === UploadState.UPLOADING;
  }

  isResumable(direct = false) {
    // Uploads that are not paused can never be resumed.
    if (this.state !== UploadState.PAUSED) {
      return false;
    }

    // Paused uploads can always be resumed, although not necessarily directly.
    if (!direct) {
      return true;
    }

    // Chunked uploads that only need to be finished can be resumed directly.
    if (this.chunked && this.chunks.length === this.chunkCount) {
      return true;
    }

    // Otherwise, it depends on whether the upload has any data attached.
    return Boolean(this.blob);
  }

  isCancelable() {
    // Only pending, started and paused uploads can be canceled.
    return [UploadState.PENDING, UploadState.UPLOADING, UploadState.PAUSED].includes(this.state);
  }
}

class UploadProvider {
  constructor(newUploadEndpoint, replaceFileCallback = null, successCallback = null, errorCallback = null) {
    this.newUploadEndpoint = newUploadEndpoint;
    this.replaceFileCallback = replaceFileCallback;
    this.successCallback = successCallback;
    this.errorCallback = errorCallback;
  }

  async upload(upload) {
    upload.state = UploadState.UPLOADING;

    if (!await this._initiateUpload(upload)) {
      return;
    }

    if (!upload.chunked) {
      await this._uploadDirect(upload);
    } else {
      await this._uploadChunked(upload);
    }
  }

  pause(upload) {
    if (!upload.isPausable()) {
      return false;
    }

    if (upload.controller) {
      upload.controller.abort();
      upload.controller = null;
    }

    if (upload.chunked) {
      upload.updateChunkProgress();
    }

    upload.state = UploadState.PAUSED;
    return true;
  }

  resume(upload) {
    if (!upload.isResumable(true)) {
      return false;
    }

    upload.state = UploadState.PENDING;
    return true;
  }

  async cancel(upload) {
    if (!upload.isCancelable()) {
      return false;
    }

    if (upload.controller) {
      upload.controller.abort();
      upload.controller = null;
    }

    if (await this._deleteUpload(upload)) {
      upload.state = UploadState.CANCELED;
      return true;
    }

    return false;
  }

  async loadUploads(endpoint) {
    const uploads = [];

    try {
      const response = await axios.get(endpoint);

      for (const uploadData of response.data.items) {
        const upload = new Upload(uploadData.name, uploadData.size);
        upload.initialize(uploadData);

        if (uploadData.state === 'active') {
          upload.state = UploadState.PAUSED;
        } else {
          // Ignore direct processing uploads.
          if (!upload.chunked) {
            continue;
          }

          upload.state = UploadState.PROCESSING;
          this._updateUploadStatus(upload);
        }

        uploads.push(upload);
      }
    } catch (error) {
      kadi.base.flashDanger($t('Error loading uploads.'), error.request);
    }

    return uploads;
  }

  async _deleteUpload(upload) {
    if (upload.deleteUploadEndpoint) {
      try {
        await axios.delete(upload.deleteUploadEndpoint);
      } catch (error) {
        // If the upload could not be found anymore, it might have already been deleted or completed.
        if (error.request.status === 404) {
          return true;
        }

        kadi.base.flashDanger($t('Error deleting upload.'), error.request);
        return false;
      }
    }

    return true;
  }

  async _initiateUpload(upload, replaceFileEndpoint = null) {
    // The upload has already been initiated.
    if (upload.initialized) {
      return true;
    }

    const data = {size: upload.size};
    let requestFunc = axios.post;
    let endpoint = this.newUploadEndpoint;

    if (replaceFileEndpoint) {
      requestFunc = axios.put;
      endpoint = replaceFileEndpoint;
    } else {
      data.name = upload.name;
    }

    try {
      const response = await requestFunc(endpoint, data);
      upload.initialize(response.data);
    } catch (error) {
      // A file with the name of the upload already exists.
      if (error.request.status === 409) {
        const endpoint = error.response.data.file._actions.edit_data;

        if (upload.forceReplace) {
          return this._initiateUpload(upload, endpoint);
        }

        if (!upload.skipReplace) {
          if (this.replaceFileCallback) {
            if (await this.replaceFileCallback(upload)) {
              return this._initiateUpload(upload, endpoint);
            }
          } else {
            kadi.base.flashWarning(error.response.data.description);
          }
        }
      // An upload quota was exceeded.
      } else if (error.request.status === 413) {
        kadi.base.flashWarning(error.response.data.description);
      } else {
        kadi.base.flashDanger($t('Error initiating upload.'), error.request);
      }

      upload.state = UploadState.CANCELED;

      if (this.errorCallback) {
        this.errorCallback(upload);
      }

      return false;
    }

    return true;
  }

  async _uploadDirect(upload) {
    const controller = new AbortController();
    upload.controller = controller;

    const config = {
      headers: {
        'Content-Type': 'application/octet-stream',
      },
      onUploadProgress: (e) => {
        upload.progress = (e.loaded / e.total) * 100;
      },
      signal: controller.signal,
    };

    try {
      const response = await axios.put(upload.uploadDataEndpoint, upload.blob, config);
      const file = response.data;

      upload.state = UploadState.COMPLETED;
      upload.viewFileEndpoint = file._links.view;

      if (this.successCallback) {
        this.successCallback(upload, file);
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        return;
      }

      kadi.base.flashDanger($t('Error uploading file.'), error.request);
      upload.state = UploadState.CANCELED;

      if (await this._deleteUpload(upload) && this.errorCallback) {
        this.errorCallback(upload);
      }
    } finally {
      upload.controller = null;
    }
  }

  async _uploadChunked(upload) {
    if (!await this._uploadChunks(upload)) {
      return;
    }

    upload.state = UploadState.PROCESSING;

    try {
      await axios.post(upload.finishUploadEndpoint);
    } catch (error) {
      // The upload processing task could not be started.
      if (error.request.status === 503) {
        kadi.base.flashWarning(error.response.data.description);
        upload.state = UploadState.PAUSED;
      } else {
        kadi.base.flashDanger($t('Error finishing upload.'), error.request);
        upload.state = UploadState.CANCELED;

        if (await this._deleteUpload(upload) && this.errorCallback) {
          this.errorCallback(upload);
        }
      }

      return;
    }

    this._updateUploadStatus(upload);
  }

  _getNextChunkIndex(upload) {
    for (let index = 0; index < upload.chunkCount; index++) {
      const found = upload.chunks.find((chunk) => chunk.index === index);

      if (!found) {
        return index;
      }
    }

    return null;
  }

  async _uploadChunks(upload) {
    while (true) {
      // Stop uploading if the upload state has been changed.
      if (upload.state !== UploadState.UPLOADING) {
        return false;
      }

      const chunkIndex = this._getNextChunkIndex(upload);

      // If no index for the next chunk could be found, we are done uploading.
      if (chunkIndex === null) {
        break;
      }

      const start = chunkIndex * upload.chunkSize;
      const end = Math.min(start + upload.chunkSize, upload.size);
      const blob = upload.blob.slice(start, end);

      let timeout = 0;

      // Try uploading the chunk until it succeeds.
      while (true) {
        // Stop uploading if the upload state has been changed.
        if (upload.state !== UploadState.UPLOADING) {
          return false;
        }

        try {
          const controller = new AbortController();
          upload.controller = controller;

          const config = {
            headers: {
              'Content-Type': 'application/octet-stream',
              'Kadi-Chunk-Index': chunkIndex,
              'Kadi-Chunk-Size': blob.size,
            },
            onUploadProgress: (e) => {
              upload.updateChunkProgress(e.loaded);
            },
            signal: controller.signal,
          };

          const response = await axios.put(upload.uploadChunkEndpoint, blob, config);

          upload.chunks = response.data.chunks;
          upload.updateChunkProgress();

          break;
        } catch (error) {
          if (axios.isCancel(error)) {
            return false;
          }

          const errorMsg = $t('Error uploading chunk.');

          // Don't retry if the upload does not exist anymore.
          if (error.request.status === 404) {
            kadi.base.flashDanger(errorMsg, error.request);
            upload.state = UploadState.CANCELED;

            if (this.errorCallback) {
              this.errorCallback(upload);
            }

            return false;
          }

          if (timeout < 60_000) {
            timeout += 5_000;
          }

          const retryMsg = $t('Retrying in {{timeout}} seconds.', {timeout: timeout / 1_000});
          kadi.base.flashWarning(`${errorMsg} ${retryMsg}`);

          // Make sure to reset the progress again.
          upload.updateChunkProgress();

          await kadi.utils.sleep(timeout);
        } finally {
          upload.controller = null;
        }
      }
    }

    return true;
  }

  _updateUploadStatus(upload) {
    let timeout = 0;

    const _updateStatus = async() => {
      if (timeout < 30_000) {
        timeout += 1_000;
      }

      try {
        const response = await axios.get(upload.getUploadEndpoint);
        const task = response.data._meta.task;

        if (task.file) {
          // The upload finished successfully.
          upload.state = UploadState.COMPLETED;
          upload.viewFileEndpoint = task.file._links.view;

          if (this.successCallback) {
            this.successCallback(upload, task.file);
          }
        } else if (task.error) {
          // The upload finished with an error.
          kadi.base.flashDanger(task.error);
          upload.state = UploadState.CANCELED;

          if (this.errorCallback) {
            this.errorCallback(upload);
          }
        } else {
          // The upload is still processing.
          window.setTimeout(_updateStatus, timeout);
        }
      } catch (error) {
        kadi.base.flashDanger($t('Error updating upload status.'), error.request);
      }
    };

    window.setTimeout(_updateStatus, 100);
  }
}

export {UploadState, Upload, UploadProvider};
