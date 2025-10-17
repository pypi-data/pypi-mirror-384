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
  <div v-if="input" class="input-group-append">
    <button type="button" class="btn clear-btn" @click="clearInput">
      <i class="fa-solid fa-xmark"></i>
    </button>
  </div>
</template>

<style lang="scss" scoped>
.clear-btn {
  background-color: white;
  border: 1px solid #ced4da;
  color: #7b8a8b;
  padding-left: 0.75rem;
  padding-right: 0.75rem;

  &:hover {
    color: black;
  }
}
</style>

<script>
export default {
  props: {
    input: String,
    inputId: {
      type: String,
      default: null,
    },
  },
  emits: ['clear-input'],
  methods: {
    clearInput() {
      this.$emit('clear-input');

      if (this.inputId !== null) {
        const elem = document.getElementById(this.inputId);

        if (elem) {
          elem.focus();
        }
      }
    },
  },
};
</script>
