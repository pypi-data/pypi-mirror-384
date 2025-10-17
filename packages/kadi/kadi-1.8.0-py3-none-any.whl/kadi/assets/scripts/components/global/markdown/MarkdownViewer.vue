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
import {ref} from 'vue';

defineProps({
  lines: Array,
  encoding: {
    type: String,
    default: null,
  },
});

const showMarkdown = ref(true);
</script>

<template>
  <div>
    <div class="row mb-2">
      <div class="col-lg-6">
        <button type="button" class="btn btn-sm btn-light text-muted" @click="showMarkdown = !showMarkdown">
          <span v-if="showMarkdown">
            <i class="fa-solid fa-code"></i> {{ $t('Plain text') }}
          </span>
          <span v-else>
            <i class="fa-solid fa-eye"></i> {{ $t('Markdown') }}
          </span>
        </button>
      </div>
      <div v-if="encoding" class="col-lg-6 d-lg-flex justify-content-end align-items-end">
        <small class="text-muted">{{ $t('Detected encoding') }}: {{ encoding.toUpperCase() }}</small>
      </div>
    </div>
    <div class="card bg-light" :class="{'max-vh-75 overflow-auto': showMarkdown}">
      <div v-show="showMarkdown" class="card-body">
        <markdown-renderer :input="lines.join('\n')"></markdown-renderer>
      </div>
      <div v-show="!showMarkdown">
        <text-viewer :lines="lines" :show-border="false"></text-viewer>
      </div>
    </div>
  </div>
</template>
