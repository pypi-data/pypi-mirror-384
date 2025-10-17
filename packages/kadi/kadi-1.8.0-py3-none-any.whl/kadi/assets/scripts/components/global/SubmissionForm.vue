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
  <form ref="form"
        :action="action"
        :method="method"
        :enctype="enctype"
        @change="onChange"
        @submit="onSubmit">
    <slot></slot>
  </form>
</template>

<script>
export default {
  props: {
    action: {
      type: String,
      default: '',
    },
    method: {
      type: String,
      default: 'post',
    },
    enctype: {
      type: String,
      default: 'application/x-www-form-urlencoded',
    },
    checkDirty: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['submit'],
  data() {
    return {
      isSubmitted: false,
      unsavedChanges: false,
    };
  },
  mounted() {
    if (this.checkDirty) {
      window.addEventListener('beforeunload', this.beforeUnload);
    }
  },
  unmounted() {
    if (this.checkDirty) {
      window.removeEventListener('beforeunload', this.beforeUnload);
    }
  },
  methods: {
    beforeUnload(e) {
      if (this.unsavedChanges && !this.isSubmitted) {
        e.preventDefault();
        return '';
      }
      return null;
    },
    onChange() {
      this.unsavedChanges = true;
      // Reset this flag in case the form submission was prevented from somewhere.
      this.isSubmitted = false;
    },
    onSubmit(e) {
      this.isSubmitted = true;
      this.$emit('submit', e);

      // Globally dispatch a custom event as well in order to react to form submissions.
      window.dispatchEvent(new Event('kadi-submit-form'));
    },
    // Convenience method for manually submitting the form from outside. Note that this will not trigger any events.
    submit() {
      this.isSubmitted = true;
      // To avoid problems when the form also contains a field called 'submit'.
      HTMLFormElement.prototype.submit.call(this.$refs.form);
    },
  },
};
</script>
