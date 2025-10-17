<!-- Copyright 2022 Karlsruhe Institute of Technology
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
    <div v-if="fileSize > maxFileSize && !isDataUrl && !forceLoad">
      <button type="button" class="btn btn-sm btn-light mb-2" @click="forceLoad = true">
        <i class="fa-solid fa-eye"></i> {{ $t('Load preview') }}
      </button>
    </div>
    <div v-else>
      <div v-if="previewType === 'image'" class="border bg-light text-center">
        <component :is="isDataUrl ? 'span' : 'a'"
                   target="_blank"
                   rel="noopener noreferrer"
                   :href="isDataUrl ? '' : url">
          <img class="img-fluid" :src="url">
        </component>
      </div>
      <iframe v-if="previewType === 'pdf'"
              class="w-100 vh-75 border rounded"
              frameborder="0"
              allowfullscreen
              :src="url">
      </iframe>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    previewType: String,
    url: String,
    fileSize: Number,
    maxFileSize: Number,
  },
  data() {
    return {
      forceLoad: false,
    };
  },
  computed: {
    isDataUrl() {
      return this.url.startsWith('data:');
    },
  },
};
</script>
