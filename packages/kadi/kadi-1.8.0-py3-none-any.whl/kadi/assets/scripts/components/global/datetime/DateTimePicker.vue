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

<script setup>
import {onMounted, onUnmounted, useTemplateRef} from 'vue';

import flatpickr from 'flatpickr';

import 'flatpickr/dist/l10n/de.js';

const props = defineProps({
  initialValue: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['input']);

const inputRef = useTemplateRef('input-ref');

let altInput = '';
let initialValueSet = false;
let picker = null;

function formatDate(date) {
  return dayjs(date).format('LL LTS');
}

onMounted(() => {
  inputRef.value.addEventListener('change', (e) => {
    // Only let our own event through, which is more reliable.
    if (!e.detail || !e.detail.propagate) {
      e.stopPropagation();
    }
  });

  picker = flatpickr(inputRef.value, {
    animate: false,
    closeOnSelect: true,
    defaultHour: 0,
    disableMobile: true,
    enableSeconds: true,
    enableTime: true,
    locale: kadi.globals.locale,
    minuteIncrement: 1,
    monthSelectorType: 'static',
    secondIncrement: 1,
    formatDate,
    onChange: (dates) => {
      if (dates.length > 0) {
        altInput = dates[0].toISOString();
      } else {
        altInput = '';
      }

      // Ignore the change event triggered by a potential initial value.
      if (initialValueSet) {
        emit('input', altInput);

        // Dispatch a regular 'change' event from the element as well, with additional metadata whether the event should
        // be propagated.
        inputRef.value.dispatchEvent(new CustomEvent('change', {bubbles: true, detail: {propagate: true}}));
      } else {
        initialValueSet = true;
      }
    },
  });

  const date = dayjs(props.initialValue);

  if (date.isValid()) {
    altInput = date.toISOString();
    picker.setDate(date.toDate(), true);
  } else {
    initialValueSet = true;
  }
});

onUnmounted(() => {
  picker.destroy();
});
</script>

<template>
  <input ref="input-ref" class="form-control time-picker-input">
</template>

<!-- Not scoped on purpose, as the new elements are attached to the body. -->
<style lang="scss">
@import '~flatpickr/dist/flatpickr.css';

.flatpickr-day {
  &.selected, &.selected:hover {
    background: #2c3e50 !important;
    border-color: #2c3e50 !important;
  }
}

.flatpickr-input {
  background-color: white !important;
}

.flatpickr-months {
  margin-top: 7px;
  font-size: 10pt;

  .flatpickr-prev-month:hover svg, .flatpickr-next-month:hover svg {
    fill: #2c3e50;
  }

  .flatpickr-current-month .numInputWrapper {
    padding-left: 5px;

    .arrowUp, .arrowDown {
      display: none;
    }
  }
}

.flatpickr-time .numInputWrapper {
  .arrowUp, .arrowDown {
    width: 20px;
    padding-left: 5px;
  }
}
</style>
