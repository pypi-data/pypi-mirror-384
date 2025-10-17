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
  <div class="socket" :class="[data.port.socket.name, compatible ? '' : 'incompatible']">
    <i v-if="data.port.multipleConnections" class="fa-solid fa-plus fa-sm"></i>
  </div>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/vars.scss';

$bg-bool: #fa5a5a;
$bg-dep: #72de6d;
$bg-env: #636363;
$bg-float: #77dfed;
$bg-int: #c660fc;
$bg-pipe: #ebe836;
$bg-str: #6b9fff;

$multi-darken: 25%;

.socket {
  align-items: center;
  background: white;
  border: 2px solid black;
  border-radius: $socket-size * 0.5;
  cursor: pointer;
  display: inline-flex;
  height: $socket-size;
  justify-content: center;
  margin: $socket-margin;
  vertical-align: middle;
  width: $socket-size;

  &.incompatible {
    cursor: default;
    opacity: 0.2;
    transition: opacity 0.25s;
  }

  &.input {
    margin-left: -$socket-size * 0.5;
  }

  &.output {
    margin-right: -$socket-size * 0.5;
  }

  &:hover {
    border: 3px solid black;
  }

  &:not(.incompatible) {
    opacity: 1;
    transition: opacity 0.5s;
  }

  /* Socket types. */

  &.bool {
    background: $bg-bool;
    color: darken($bg-bool, $multi-darken);
  }

  &.dep {
    background: $bg-dep;
    color: darken($bg-dep, $multi-darken);
  }

  &.env {
    background: $bg-env;
    color: darken($bg-env, $multi-darken);
  }

  &.float {
    background: $bg-float;
    color: darken($bg-float, $multi-darken);
  }

  &.int {
    background: $bg-int;
    color: darken($bg-int, $multi-darken);
  }

  &.pipe {
    background: $bg-pipe;
    color: darken($bg-pipe, $multi-darken);
  }

  &.str {
    background: $bg-str;
    color: darken($bg-str, $multi-darken);
  }
}
</style>

<script>
export default {
  props: {
    data: Object,
    multi: Boolean,
  },
  data() {
    return {
      compatible: true,
    };
  },
  mounted() {
    this.data.editor.addPipe((context) => {
      if (context.type === 'socket-validate') {
        const currentPort = this.data.port;
        const otherPort = context.payload.port;

        if (currentPort.id === otherPort.id) {
          this.compatible = true;
        } else if ((this.data.nodeId === context.payload.nodeId) || (this.data.side === context.payload.side)) {
          this.compatible = false;
        } else if (this.data.side === 'output') {
          this.compatible = currentPort.socket.compatibleWith(otherPort.socket);
        } else {
          this.compatible = otherPort.socket.compatibleWith(currentPort.socket);
        }
      }

      if (context.type === 'socket-reset') {
        this.compatible = true;
      }

      return context;
    });
  },
};
</script>
