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
  <svg>
    <path :d="path" :class="{'pseudo': isPseudo}"></path>
  </svg>
</template>

<style lang="scss" scoped>
svg {
  height: 9999px;
  overflow: visible !important;
  pointer-events: none;
  position: absolute;
  width: 9999px;

  path {
    fill: none;
    pointer-events: auto;
    stroke: black;
    stroke-linecap: square;
    stroke-width: 3px;

    &:hover {
      stroke-width: 5px;
    }

    &.pseudo {
      opacity: 0.5;
      stroke-dasharray: 10;
      stroke-linecap: round;
    }
  }
}
</style>

<script>
export default {
  props: {
    data: Object,
    start: Object,
    end: Object,
    path: String,
  },
  data() {
    return {
      isPseudo: this.data.isPseudo || false,
    };
  },
};
</script>
