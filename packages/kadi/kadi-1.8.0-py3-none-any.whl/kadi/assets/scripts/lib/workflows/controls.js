/* Copyright 2024 Karlsruhe Institute of Technology
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. */

import {ClassicPreset} from 'rete';

class BaseControl extends ClassicPreset.Control {
  constructor(updateCallback, label = '') {
    super();

    this.updateCallback = updateCallback;
    this.label = label;
  }
}

export class StringControl extends BaseControl {
  constructor(updateCallback, label = '', defaultValue = '') {
    super(updateCallback, label);
    this.value = defaultValue;
  }

  setValue(value) {
    const prevValue = this.value;
    this.value = String(value);

    if (this.value !== prevValue) {
      this.updateCallback();
    }
  }
}

export class BoolControl extends BaseControl {
  constructor(updateCallback, label = '', defaultValue = false) {
    super(updateCallback, label);

    this.value = defaultValue;
    this.truthy = ['true', 't', 'yes', 'y', 'on', '1'];
  }

  setValue(value) {
    const prevValue = this.value;

    if (typeof value === 'string') {
      this.value = this.truthy.includes(value.toLowerCase());
    } else {
      this.value = Boolean(value);
    }

    if (this.value !== prevValue) {
      this.updateCallback();
    }
  }
}

export class PortControl extends BaseControl {
  constructor(updateCallback, label = '', defaultValue = 3, maxValue = 99) {
    super(updateCallback, label);

    this.value = this.defaultValue = defaultValue;
    this.maxValue = maxValue;
    this.focus = false;
  }

  setValue(value) {
    const prevValue = this.value;
    this.value = Number.parseInt(value, 10);

    if (window.isNaN(this.value)) {
      this.value = this.defaultValue;
    }

    this.value = kadi.utils.clamp(this.value, 0, this.maxValue);

    if (this.value !== prevValue) {
      this.updateCallback();
    }
  }

  setFocus(value) {
    this.focus = value;
  }
}

export class FormatControl extends BaseControl {
  constructor(updateCallback, label = '', defaultCount = 3) {
    super(updateCallback, label);

    this.updateDefaultValue(defaultCount);
    this.value = this.defaultValue;
  }

  setValue(value) {
    const prevValue = this.value;
    this.value = String(value);

    if (this.value !== prevValue) {
      this.updateCallback();
    }
  }

  updateDefaultValue(count) {
    const placeholders = [];

    for (let i = 0; i < count; i++) {
      placeholders.push(`%${i}`);
    }

    this.defaultValue = `[${placeholders.join(', ')}]`;
  }
}
