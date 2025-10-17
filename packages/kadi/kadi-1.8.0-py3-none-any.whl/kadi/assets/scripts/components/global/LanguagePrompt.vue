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
import {onMounted, ref} from 'vue';

import Cookies from 'js-cookie';

const props = defineProps({
  cookieName: String,
  cookieSecure: Boolean,
  preferredLocale: String,
});

const showLangPrompt = ref(false);

const storageKey = 'hide_lang_prompt';

function switchLocale(locale) {
  Cookies.set(props.cookieName, locale, {secure: props.cookieSecure, expires: 365, sameSite: 'Lax'});
  window.location.reload();
}

function dismissPrompt() {
  showLangPrompt.value = false;
  window.localStorage.setItem(storageKey, 'true');
}

function acceptPrompt() {
  dismissPrompt();
  switchLocale(props.preferredLocale);
}

onMounted(() => {
  const hasLocaleCookie = Boolean(Cookies.get(props.cookieName));
  const promptDismissed = Boolean(window.localStorage.getItem(storageKey));

  if (!hasLocaleCookie && !promptDismissed && props.preferredLocale !== kadi.globals.locale) {
    showLangPrompt.value = true;
  }
});
</script>

<template>
  <div v-if="showLangPrompt" class="card bg-light">
    <div class="card-body py-3">
      <div class="row align-items-center">
        <div class="col-lg-9">
          Based on your browser settings, you seem to prefer a different language. Do you want to change the current
          language?
        </div>
        <div class="col-lg-3 mt-2 mt-lg-0 d-lg-flex justify-content-end">
          <div>
            <button type="button" class="btn btn-sm btn-primary" @click="acceptPrompt">Yes</button>
            <button type="button" class="btn btn-sm btn-light" @click="dismissPrompt">No</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
