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

<template>
  <div class="input-group input-group-sm" @pointerdown.stop>
    <input ref="input" v-model="value" class="form-control input" :title="value">
    <div class="input-group-append">
      <button type="button" class="btn btn-light" @click="value--">
        <i class="fa-solid fa-minus"></i>
      </button>
      <button type="button" class="btn btn-light" @click="value++">
        <i class="fa-solid fa-plus"></i>
      </button>
    </div>
  </div>
</template>

<style scoped>
.input {
  width: 40px;
}
</style>

<script>
export default {
  props: {
    data: Object,
  },
  data() {
    return {
      value: this.data.value,
    };
  },
  watch: {
    value() {
      this.data.setValue(this.value);
      this.data.setFocus(true);

      this.value = this.data.value;
    },
  },
  mounted() {
    if (this.data.focus) {
      this.data.setFocus(false);
      this.$refs.input.focus();
    }
  },
};
</script>
