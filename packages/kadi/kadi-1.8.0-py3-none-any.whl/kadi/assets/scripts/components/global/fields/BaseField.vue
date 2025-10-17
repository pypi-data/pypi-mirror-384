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
  <div class="form-group" :class="{'required': field.validation.required}">
    <label class="form-control-label" :for="field.id">{{ field.label }}</label>
    <slot :errors="errors" :has-error="hasError"></slot>
    <div v-for="error in errors" :key="error" class="invalid-feedback">{{ error }}</div>
    <small v-if="errors.length === 0" class="form-text text-muted">{{ field.description }}</small>
  </div>
</template>

<script>
export default {
  props: {
    field: Object,
  },
  data() {
    return {
      errors: [],
      minMaxLengthInvalid: false,
      minMaxLengthWarning: null,
      maxLengthInvalid: false,
      maxLengthWarning: null,
      minLengthInvalid: false,
      minLengthWarning: null,
    };
  },
  computed: {
    hasError() {
      return this.errors.length > 0;
    },
  },
  mounted() {
    this.field.errors.forEach((error) => this.errors.push(error));

    // This requires the messages set via server-side validation to be the same.
    if (this.field.validation.min && this.field.validation.max) {
      const message = $t('Field must be between {{minLength}} and {{maxLength}} characters long.', {
        minLength: this.field.validation.min,
        maxLength: this.field.validation.max,
      });
      this.initializeData('minMaxLengthInvalid', 'minMaxLengthWarning', message);
    } else if (this.field.validation.max) {
      const message = $t('Field cannot be longer than {{length}} characters.', {length: this.field.validation.max});
      this.initializeData('maxLengthInvalid', 'maxLengthWarning', message);
    } else if (this.field.validation.min) {
      const message = $t('Field must be at least {{length}} characters long.', {length: this.field.validation.min});
      this.initializeData('minLengthInvalid', 'minLengthWarning', message);
    }
  },
  methods: {
    initializeData(invalidFlagVar, warningMessageVar, message) {
      this[warningMessageVar] = message;
      if (this.errors.indexOf(this[warningMessageVar]) !== -1) {
        this[invalidFlagVar] = true;
      }
    },
    handleInvalidData(invalidFlagVar, warningMessageVar) {
      if (!this[invalidFlagVar]) {
        this[invalidFlagVar] = true;
        this.errors.push(this[warningMessageVar]);
      }
    },
    handleValidData(invalidFlagVar, warningMessageVar) {
      if (this[invalidFlagVar]) {
        this[invalidFlagVar] = false;
        kadi.utils.removeFromArray(this.errors, this[warningMessageVar]);
      }
    },
    validateMinMaxLength(data) {
      if ((data.length < this.field.validation.min && data.length > 0) || data.length > this.field.validation.max) {
        this.handleInvalidData('minMaxLengthInvalid', 'minMaxLengthWarning');
      } else {
        this.handleValidData('minMaxLengthInvalid', 'minMaxLengthWarning');
      }
    },
    validateMaxLength(data) {
      if (data.length > this.field.validation.max) {
        this.handleInvalidData('maxLengthInvalid', 'maxLengthWarning');
      } else {
        this.handleValidData('maxLengthInvalid', 'maxLengthWarning');
      }
    },
    validateMinLength(data) {
      if (data.length < this.field.validation.min && data.length > 0) {
        this.handleInvalidData('minLengthInvalid', 'minLengthWarning');
      } else {
        this.handleValidData('minLengthInvalid', 'minLengthWarning');
      }
    },
    // Apply all available client-side validation based on the field.
    validate(data) {
      if (this.field.validation.min && this.field.validation.max) {
        this.validateMinMaxLength(data);
      } else if (this.field.validation.max) {
        this.validateMaxLength(data);
      } else if (this.field.validation.min) {
        this.validateMinLength(data);
      }
    },
    // Add an additional error message, if not present already.
    addError(message) {
      if (this.errors.indexOf(message) === -1) {
        this.errors.push(message);
      }
    },
    // Remove an error message, if present.
    removeError(message) {
      kadi.utils.removeFromArray(this.errors, message);
    },
  },
};
</script>
