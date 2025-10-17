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
  <div ref="node" class="node" :class="[data.selected ? 'selected': '', data.tool ? data.tool.type : '']">
    <!-- Node header including label and execution profile -->
    <div v-if="data.label || executionProfile" class="d-flex justify-content-between align-items-center header">
      <strong v-if="data.label" :title="data.label">{{ nodeLabel }}</strong>
      <div v-if="executionProfile" class="dropdown ml-4" @pointerdown.stop>
        <button type="button"
                class="btn btn-sm dropdown-btn"
                data-toggle="dropdown"
                data-display="static"
                :title="executionProfile">
          <i class="fa-solid fa-sm" :class="getExecutionProfileIcon(executionProfile)"></i>
        </button>
        <div class="dropdown-menu m-0 p-0">
          <div class="dropdown-header text-default px-2 py-1">Execution profile</div>
          <div class="dropdown-divider my-0"></div>
          <button v-for="profile in data.executionProfiles"
                  :key="profile"
                  type="button"
                  class="dropdown-item px-2"
                  :class="{'active': profile === executionProfile}"
                  @click="updateExecutionProfile(profile)">
            <small>
              <i class="fa-solid fa-sm" :class="getExecutionProfileIcon(profile)"></i> {{ profile }}
            </small>
          </button>
        </div>
      </div>
    </div>
    <!-- Node body including inputs, controls and outputs -->
    <div class="content">
      <div v-if="data.hasInputs" class="column">
        <div v-for="[key, input] in data.sortedInputs" :key="`input-${key}-${seed}`" class="input">
          <node-component class="socket" :data="socketData(key, input, 'input')" :emit="emit"></node-component>
          <span :title="input.label">
            {{ portLabel(input) }}<strong v-if="input.required" class="required">*</strong>
          </span>
        </div>
      </div>
      <div v-if="data.hasControls" class="column">
        <div v-for="[key, control] in data.sortedControls" :key="`control-${key}-${seed}`" class="control">
          <span v-if="control.label" class="label" :title="control.label">{{ control.label }}</span>
          <node-component :data="{type: 'control', payload: control}" :emit="emit"></node-component>
        </div>
      </div>
      <div v-if="data.hasOutputs" class="column">
        <div v-for="[key, output] in data.sortedOutputs" :key="`output-${key}-${seed}`" class="output">
          <span :title="output.label">{{ portLabel(output) }}</span>
          <node-component class="socket" :data="socketData(key, output, 'output')" :emit="emit"></node-component>
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@import 'styles/workflows/vars.scss';

$io-margin: 5px;

$opacity: 0.95;
$opacity-hover: 0.8;

.node {
  background: rgba($bg-builtin, $opacity);
  border: 2px solid black;
  border-radius: 0.75rem;
  box-sizing: border-box;
  cursor: pointer;
  min-width: 150px;
  padding-bottom: 10px;
  padding-top: 10px;
  position: relative;
  user-select: none;

  .content {
    display: table;
    width: 100%;

    .column {
      display: table-cell;
      white-space: nowrap;

      .required {
        color: red;
        font-size: 125%;
      }

      &:not(:last-child) {
        padding-right: 20px;
      }
    }
  }

  .control {
    align-items: center;
    display: flex;
    max-width: 325px;
    padding: $socket-margin $socket-size * 0.5 + $socket-margin;

    .label {
      min-width: 75px;
    }
  }

  .dropdown-btn {
    align-items: center;
    border: 1px solid rgba(black, 0.3);
    display: flex;
    height: 25px;
    justify-content: center;
    width: 25px;
  }

  .dropdown-menu {
    min-width: 0;
  }

  .header {
    padding: 0 18px 18px 18px;
  }

  .input {
    margin-bottom: $io-margin;
    margin-top: $io-margin;
    text-align: left;

    .socket {
      display: inline-block;
      margin-left: -($socket-size * 0.5 + $socket-margin + 1);
    }
  }

  .output {
    margin-bottom: $io-margin;
    margin-top: $io-margin;
    text-align: right;

    .socket {
      display: inline-block;
      margin-right: -($socket-size * 0.5 + $socket-margin + 1);
    }
  }

  &.env {
    background: rgba($bg-env, $opacity);
    color: white;

    .dropdown-btn {
      border: 1px solid rgba(white, 0.3);
      color: white;
    }
  }

  &.program {
    background: rgba($bg-program, $opacity);
    color: white;

    .dropdown-btn {
      border: 1px solid rgba(white, 0.3);
      color: white;
    }
  }

  &:hover, &.selected {
    background: rgba(darken($bg-builtin, 20%), $opacity-hover);

    &.env {
      background: rgba(darken($bg-env, 20%), $opacity-hover);
    }

    &.program {
      background: rgba(darken($bg-program, 20%), $opacity-hover);
    }
  }
}
</style>

<script>
import {Ref as NodeComponent} from 'rete-vue-plugin';

export default {
  components: {
    NodeComponent,
  },
  props: {
    data: Object,
    emit: Function,
    seed: Number,
  },
  data() {
    return {
      executionProfile: this.data.executionProfile,
      executionProfileIcons: {
        Default: 'fa-play',
        Skip: 'fa-ban',
        Detached: 'fa-link-slash',
      },
    };
  },
  computed: {
    nodeLabel() {
      return kadi.utils.truncate(this.data.label, 50);
    },
  },
  mounted() {
    const observer = new ResizeObserver((entries) => {
      const borderBox = entries[0].borderBoxSize[0];
      this.data.setWidth(borderBox.inlineSize);
      this.data.setHeight(borderBox.blockSize);
    });
    observer.observe(this.$refs.node);
  },
  methods: {
    getExecutionProfileIcon(profile) {
      return this.executionProfileIcons[profile] || 'fa-question';
    },
    updateExecutionProfile(profile) {
      this.executionProfile = profile;
      this.data.setExecutionProfile(profile);
    },
    portLabel(port) {
      return kadi.utils.truncate(port.label, 25);
    },
    socketData(key, port, side) {
      return {
        type: 'socket',
        side,
        key,
        nodeId: this.data.id,
        payload: {port, side, editor: this.data.editor, nodeId: this.data.id},
      };
    },
  },
};
</script>
