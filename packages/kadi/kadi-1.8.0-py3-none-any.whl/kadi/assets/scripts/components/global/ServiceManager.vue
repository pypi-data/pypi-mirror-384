<!-- Copyright 2024 Karlsruhe Institute of Technology
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
    {{ $t('This functionality requires a service that is not yet connected to your account.') }}
    <!-- eslint-disable-next-line @stylistic/js/max-len -->
    {{ $t('Click one of the buttons below to either connect your account directly to the service or to manage all of your connected services.') }}
    <hr>
    <a class="btn btn-sm btn-primary" :href="connectEndpoint">{{ $t('Connect service') }}</a>
    <a class="btn btn-sm btn-light" :href="manageEndpoint">{{ $t('Manage services') }}</a>
  </div>
</template>

<script>
export default {
  props: {
    connectEndpoint: String,
    manageEndpoint: String,
  },
};
</script>
