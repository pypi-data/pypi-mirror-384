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

<template>
  <div class="form-group">
    <div class="d-flex justify-content-between">
      <label class="form-control-label">{{ field.label }}</label>
      <div class="form-check">
        <input :id="`scope-full-${id}`"
               type="checkbox"
               class="form-check-input"
               :checked="scopesChecked()"
               @click="checkScopes($event.target.checked)">
        <label class="form-check-label" :for="`scope-full-${id}`">{{ $t('Full access') }}</label>
      </div>
    </div>
    <div class="card">
      <div class="card-body px-3 pt-3 pb-2">
        <div class="d-lg-flex justify-content-between">
          <div v-for="(actions, object, index) in scopes" :key="object" :class="{'mt-4 mt-lg-0': index > 0}">
            <div class="form-check mb-2">
              <input :id="`scope-${object}-${id}`"
                     type="checkbox"
                     class="form-check-input"
                     :checked="scopesChecked(object)"
                     @click="checkScopes($event.target.checked, object)">
              <label class="form-check-label" :for="`scope-${object}-${id}`">
                <strong>{{ kadi.utils.capitalize(getDisplayName(object)) }}</strong>
              </label>
            </div>
            <div v-for="action in actions" :key="getScopeValue(object, action)" class="form-check mb-1">
              <input :id="`scope-${getScopeValue(object, action)}-${id}`"
                     v-model="scopesModel[object][action].checked"
                     type="checkbox"
                     class="form-check-input">
              <label class="form-check-label" :for="`scope-${getScopeValue(object, action)}-${id}`">{{ action }}</label>
            </div>
          </div>
        </div>
      </div>
    </div>
    <small class="form-text text-muted">{{ field.description }}</small>
    <input type="hidden" :name="field.name" :value="serializedScopes">
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
    scopes: Object,
    getDisplayName: {
      type: Function,
      default: (objectName) => objectName,
    },
  },
  data() {
    return {
      id: kadi.utils.randomAlnum(),
      scopesModel: null,
    };
  },
  computed: {
    serializedScopes() {
      const checkedScopes = [];

      for (const object in this.scopesModel) {
        for (const action in this.scopesModel[object]) {
          if (this.scopesModel[object][action].checked) {
            checkedScopes.push(this.getScopeValue(object, action));
          }
        }
      }

      return checkedScopes.join(' ');
    },
  },
  created() {
    const initialScopes = this.field.data.split(' ');
    const scopesModel = {};

    for (const object in this.scopes) {
      scopesModel[object] = {};

      this.scopes[object].forEach((action) => {
        let checked = false;

        if (initialScopes.includes(this.getScopeValue(object, action))) {
          checked = true;
        }

        scopesModel[object][action] = {checked};
      });
    }

    this.scopesModel = scopesModel;
  },
  methods: {
    getScopeValue(object, action) {
      return `${object}.${action}`;
    },
    getActionModels(object = null) {
      const actionModels = [];

      if (object === null) {
        for (const objectModel of Object.values(this.scopesModel)) {
          actionModels.push(...Object.values(objectModel));
        }
      } else {
        actionModels.push(...Object.values(this.scopesModel[object]));
      }

      return actionModels;
    },
    scopesChecked(object = null) {
      const actionModels = this.getActionModels(object);

      for (const actionModel of actionModels) {
        if (!actionModel.checked) {
          return null;
        }
      }

      return 'true';
    },
    checkScopes(checked, object = null) {
      const actionModels = this.getActionModels(object);

      for (const actionModel of actionModels) {
        actionModel.checked = checked;
      }
    },
  },
};
</script>
