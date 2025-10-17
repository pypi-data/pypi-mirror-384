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
  <modal-dialog ref="dialog" title="Edit variables">
    <template #body>
      <ul class="list-group">
        <li class="list-group-item py-2 bg-light">
          <div class="form-row">
            <div class="col-md-5">Name</div>
            <div class="col-md-5">Value</div>
          </div>
        </li>
        <li v-for="(variable, index) in variables" :key="variable.id" class="list-group-item py-2">
          <div class="form-row">
            <div class="col-md-5 mb-2 mb-md-0">
              <input v-model.trim="variable.name"
                     class="form-control form-control-sm"
                     @change="changeVariable(variable)">
            </div>
            <div class="col-md-5 mb-2 mb-md-0">
              <input v-model="variable.value"
                     class="form-control form-control-sm"
                     @change="changeVariable(variable)">
            </div>
            <div class="col-md-2">
              <div class="btn-group btn-group-sm w-100">
                <button type="button" class="btn btn-light" title="Add variable" @click="addVariable(index)">
                  <i class="fa-solid fa-plus"></i>
                </button>
                <button v-if="variables.length > 1"
                        type="button"
                        class="btn btn-light"
                        title="Remove variable"
                        @click="removeVariable(index)">
                  <i class="fa-solid fa-xmark"></i>
                </button>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </template>
  </modal-dialog>
</template>

<script>
export default {
  emits: ['set-variables'],
  data() {
    return {
      variables: [],
      initialized: false,
    };
  },
  computed: {
    serializedVariables() {
      const variables = [];

      for (const variable of this.variables) {
        if (variable.name) {
          variables.push({name: variable.name, value: variable.value});
        }
      }

      return variables;
    },
  },
  mounted() {
    this.addVariable();
    this.initialized = true;
  },
  methods: {
    open() {
      this.$refs.dialog.open();
    },
    setVariables(variables) {
      this.variables = [];

      for (const variable of variables) {
        this.addVariable(null, variable.name, variable.value);
      }

      if (this.variables.length === 0) {
        this.addVariable();
      }
    },
    addVariable(index = null, name = '', value = '') {
      const variable = {id: kadi.utils.randomAlnum(), name, value};
      kadi.utils.addToArray(this.variables, variable, index);

      if (this.initialized) {
        this.$emit('set-variables', this.serializedVariables);
      }
    },
    removeVariable(index) {
      this.variables.splice(index, 1);

      if (this.initialized) {
        this.$emit('set-variables', this.serializedVariables);
      }
    },
    changeVariable(variable) {
      // Do not allow duplicate names.
      if (this.variables.filter((v) => v.name === variable.name).length > 1) {
        variable.name = '';
      }

      this.$emit('set-variables', this.serializedVariables);
    },
  },
};
</script>
