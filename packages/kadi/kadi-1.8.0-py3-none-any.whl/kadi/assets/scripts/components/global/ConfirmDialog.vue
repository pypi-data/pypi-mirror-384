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
  <div ref="dialog" class="modal" tabindex="-1" @keydown.enter="handleEnter">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-body">
          {{ message }}
          <input v-if="showPrompt" ref="prompt" v-model="promptValue" class="form-control form-control-sm mt-2">
        </div>
        <div class="modal-footer justify-content-between">
          <div>
            <button ref="btnAccept" type="button" class="btn btn-sm btn-primary btn-modal" data-dismiss="modal">
              {{ acceptText }}
            </button>
            <button ref="btnCancel" type="button" class="btn btn-sm btn-light btn-modal" data-dismiss="modal">
              {{ cancelText }}
            </button>
          </div>
          <div v-if="showCheckbox" class="form-check">
            <input :id="`apply-all-${suffix}`" v-model="checkboxValue" type="checkbox" class="form-check-input">
            <label class="form-check-label" :for="`apply-all-${suffix}`">{{ checkboxText }}</label>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.btn-modal {
  width: 100px;
}
</style>

<script>
export default {
  props: {
    acceptText: {
      type: String,
      default: $t('Yes'),
    },
    cancelText: {
      type: String,
      default: $t('No'),
    },
    checkboxText: {
      type: String,
      default: $t('Apply to all'),
    },
  },
  data() {
    return {
      dialog: null,
      suffix: kadi.utils.randomAlnum(),
      message: '',
      showPrompt: false,
      promptValue: '',
      showCheckbox: false,
      checkboxValue: false,
    };
  },
  unmounted() {
    this.dialog.modal('dispose');
  },
  methods: {
    handleEnter() {
      this.$refs.btnAccept.click();
    },
    async open(msg, showPrompt = false, showCheckbox = false) {
      this.message = msg;
      this.showPrompt = showPrompt;
      this.showCheckbox = showCheckbox;

      await this.$nextTick();

      $(this.$refs.dialog).on('shown.bs.modal', () => {
        // Ensure the backdrop is always visible.
        const backdrop = document.getElementsByClassName('modal-backdrop')[0];
        this.$el.parentNode.insertBefore(backdrop, this.$el.nextSibling);

        if (this.showPrompt) {
          // Without the timeout the focus does not seem to work consistently.
          setTimeout(() => this.$refs.prompt.focus(), 0);
        }
      });

      let acceptHandler = null;
      let cancelHandler = null;

      return new Promise((resolve) => {
        // Make sure that all event listeners are removed again and all inputs are reset after resolving the promise by
        // closing the modal via one of the buttons.
        const resolveDialog = (status) => {
          resolve({status, prompt: this.promptValue, checkbox: this.checkboxValue});

          this.promptValue = '';
          this.checkboxValue = false;

          this.$refs.btnAccept.removeEventListener('click', acceptHandler);
          this.$refs.btnCancel.removeEventListener('click', cancelHandler);

          $(this.$refs.dialog).off('shown.bs.modal');
        };

        acceptHandler = () => resolveDialog(true);
        cancelHandler = () => resolveDialog(false);

        this.$refs.btnAccept.addEventListener('click', acceptHandler);
        this.$refs.btnCancel.addEventListener('click', cancelHandler);

        this.dialog = $(this.$refs.dialog).modal({backdrop: 'static', keyboard: false});
      });
    },
  },
};
</script>
