<!-- Copyright 2023 Karlsruhe Institute of Technology
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
import Cookies from 'js-cookie';

const props = defineProps({
  cookieName: String,
  cookieSecure: Boolean,
  locales: Object,
});

function switchLocale(locale) {
  Cookies.set(props.cookieName, locale, {secure: props.cookieSecure, expires: 365, sameSite: 'Lax'});
  window.location.reload();
}
</script>

<template>
  <div class="dropup float-lg-right">
    <a class="footer-item" href="#" data-toggle="dropdown">
      <i class="fa-solid fa-language fa-lg mr-1"></i> {{ $t('Language') }}
    </a>
    <div class="dropdown-menu dropdown-menu-right mb-3">
      <strong class="dropdown-header">{{ $t('Select a language') }}</strong>
      <button v-for="(language, locale) in locales"
              :key="locale"
              type="button"
              class="dropdown-item"
              @click="switchLocale(locale)">
        {{ language }}
        <span v-if="locale === kadi.globals.locale" class="float-right">
          <i class="fa-solid fa-check fa-sm"></i>
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.dropdown-menu {
  @media (max-width: 992px) {
    top: -40px !important;
  }
}
</style>
