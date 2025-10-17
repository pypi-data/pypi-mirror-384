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
  <div class="form-group">
    <extras-editor :id="field.id"
                   :name="field.name"
                   :label="field.label"
                   :initial-values="field.data"
                   :edit-extra-keys="editExtraKeys"
                   :template-endpoint="templateEndpoint"
                   :terms-endpoint="termsEndpoint"
                   :editing-mode="editingMode_"
                   :is-collapsed="isCollapsed_">
    </extras-editor>
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
    editExtraKeys: {
      type: Array,
      default: () => [],
    },
    templateEndpoint: {
      type: String,
      default: null,
    },
    termsEndpoint: {
      type: String,
      default: null,
    },
    editingMode: {
      type: Boolean,
      default: null,
    },
    isCollapsed: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      editingMode_: false,
      isCollapsed_: this.isCollapsed,
    };
  },
  created() {
    if (this.editingMode !== null) {
      this.editingMode_ = this.editingMode;
    } else {
      // If no mode is specified, we decide based on the content of the formdata.
      if (this.field.errors.length === 0) {
        this.editingMode_ = this.field.data.length === 0;
      } else {
        // Editing mode should have been active before if there are any errors besides values and units.
        this.editingMode_ = this.extrasInvalid(this.field.data, false);
      }
    }

    if (this.isCollapsed) {
      // Do not collapse the field if there are any errors.
      this.isCollapsed_ = !this.extrasInvalid(this.field.data);
    }
  },
  methods: {
    extrasInvalid(extras, allProps = true) {
      for (const extra of extras) {
        for (const [key, value] of Object.entries(extra)) {
          if (value.errors.length > 0 && (allProps || !['value', 'unit'].includes(key))) {
            return true;
          }
        }

        if (kadi.utils.isNestedType(extra.type)) {
          if (this.extrasInvalid(extra.value)) {
            return true;
          }
        }
      }

      return false;
    },
  },
};
</script>
